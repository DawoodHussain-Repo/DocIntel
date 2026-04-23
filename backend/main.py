"""FastAPI application with secure upload and streaming chat endpoints."""
from contextlib import asynccontextmanager

import chromadb
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from core.agent import create_agent
from core.checkpointer import set_checkpointer
from core.config import config
from core.errors import AppError
from core.models import ErrorResponse, HealthData, SuccessResponse
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from utils.logger import setup_logging
from api.middleware import LoggingMiddleware
from services.chat_service import stream_chat_events
from services.upload_service import process_contract_upload


setup_logging()
logger = structlog.get_logger("docintel.main")

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize runtime dependencies and validate startup configuration."""
    logger.info("application_startup_started", version=config.APP_VERSION)
    
    try:
        config.validate()
        logger.info("configuration_validated")
        
        from chromadb.config import Settings
        app.state.chroma_client = chromadb.PersistentClient(
            path=str(config.CHROMA_PERSIST_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info("chromadb_initialized", persist_dir=str(config.CHROMA_PERSIST_DIR))
        
        async with AsyncSqliteSaver.from_conn_string(
            str(config.SQLITE_DB_PATH)
        ) as checkpointer:
            set_checkpointer(checkpointer)
            logger.info("checkpointer_initialized", db_path=str(config.SQLITE_DB_PATH))
            
            app.state.agent = await create_agent(app.state.chroma_client)
            logger.info("application_startup_completed")
            
            yield
            
    except Exception as error:
        logger.exception(
            "application_startup_failed",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        raise
    
    logger.info("application_shutdown_started")
    logger.info("application_shutdown_completed")


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.ALLOWED_HOSTS)


@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Attach baseline security headers to every HTTP response."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(_: Request, _error: RateLimitExceeded) -> JSONResponse:
    """Return structured error for rate limit violations."""
    logger.warning("rate_limit_exceeded")
    
    payload = ErrorResponse(
        error="Rate limit exceeded. Please try again later.",
        code="RATE_LIMIT_EXCEEDED",
        details={},
    )
    return JSONResponse(status_code=429, content=payload.model_dump())


@app.exception_handler(AppError)
async def app_error_handler(_: Request, error: AppError) -> JSONResponse:
    """Return structured API errors for known application exceptions."""
    logger.warning(
        "application_error",
        error_code=error.code,
        error_message=error.message,
        status_code=error.status_code,
    )
    
    payload = ErrorResponse(
        error=error.message,
        code=error.code,
        details=error.details,
    )
    return JSONResponse(status_code=error.status_code, content=payload.model_dump())


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, error: HTTPException) -> JSONResponse:
    """Map HTTPExceptions into the standard error response envelope."""
    logger.warning(
        "http_error",
        status_code=error.status_code,
        detail=str(error.detail),
    )
    
    detail = error.detail if isinstance(error.detail, str) else "Request failed."
    payload = ErrorResponse(error=detail, code="HTTP_ERROR")
    return JSONResponse(status_code=error.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_: Request, error: RequestValidationError) -> JSONResponse:
    """Return typed validation failures for malformed request payloads."""
    logger.warning(
        "validation_error",
        error_count=len(error.errors()),
        errors=error.errors(),
    )
    
    payload = ErrorResponse(
        error="Request validation failed.",
        code="VALIDATION_ERROR",
        details={"errors": error.errors()},
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, error: Exception) -> JSONResponse:
    """Return a safe generic payload for unhandled server errors."""
    logger.exception(
        "unhandled_error",
        error_type=type(error).__name__,
        error_message=str(error),
    )
    
    payload = ErrorResponse(
        error="Internal server error.",
        code="INTERNAL_SERVER_ERROR",
        details=None,
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


@app.post("/api/upload_contract", response_model=SuccessResponse, status_code=201)
@limiter.limit("10/minute")
async def upload_contract(request: Request, file: UploadFile = File(...)) -> SuccessResponse:
    """Validate and index an uploaded contract PDF."""
    logger.info(
        "upload_started",
        filename=file.filename,
        content_type=file.content_type,
    )
    
    content = await file.read()
    result = process_contract_upload(
        file.filename, file.content_type, content, app.state.chroma_client
    )
    
    logger.info(
        "upload_completed",
        filename=file.filename,
        chunks_indexed=result.chunks_indexed,
    )
    
    return SuccessResponse(data=result.model_dump())


@app.get("/api/chat/stream")
@limiter.limit("30/minute")
async def chat_stream(
    request: Request,
    query: str = Query(..., min_length=1, max_length=config.MAX_QUERY_LENGTH),
    thread_id: str = Query(..., min_length=1),
) -> StreamingResponse:
    """Stream agent responses as structured SSE events."""
    logger.info(
        "chat_stream_started",
        query_length=len(query),
        thread_id=thread_id,
    )
    
    agent = getattr(app.state, "agent", None)
    if agent is None:
        logger.error("agent_not_ready")
        raise AppError(
            message="Agent is not initialized yet.",
            code="AGENT_NOT_READY",
            status_code=503,
        )

    event_stream = stream_chat_events(agent=agent, query=query, thread_id=thread_id)
    return StreamingResponse(
        event_stream,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/health", response_model=SuccessResponse)
async def health_check() -> SuccessResponse:
    """Report backend health status with deep checks for uptime monitoring."""
    checks = {}
    
    # Check ChromaDB
    try:
        chroma_client = getattr(app.state, "chroma_client", None)
        if chroma_client:
            chroma_client.list_collections()
            checks["chromadb"] = "ok"
        else:
            checks["chromadb"] = "not_initialized"
    except Exception as error:
        logger.warning("health_check_chromadb_failed", error=str(error))
        checks["chromadb"] = "error"
    
    # Check Agent
    agent = getattr(app.state, "agent", None)
    checks["agent"] = "ok" if agent is not None else "not_initialized"
    
    # Check SQLite checkpointer
    try:
        from core.checkpointer import get_checkpointer
        checkpointer = get_checkpointer()
        checks["checkpointer"] = "ok" if checkpointer is not None else "not_initialized"
    except Exception as error:
        logger.warning("health_check_checkpointer_failed", error=str(error))
        checks["checkpointer"] = "error"
    
    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503
    
    data = HealthData(
        service="docintel-backend",
        version=config.APP_VERSION,
    ).model_dump()
    data["checks"] = checks
    
    return JSONResponse(
        status_code=status_code,
        content=SuccessResponse(
            data=data,
            message="healthy" if all_ok else "degraded",
        ).model_dump(),
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=config.BACKEND_PORT, reload=True)
