"""FastAPI application with secure upload and streaming chat endpoints."""
from contextlib import asynccontextmanager

import chromadb

from fastapi import FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from agent import create_agent
from checkpointer import set_checkpointer
from config import config
from errors import AppError
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from models import ErrorResponse, HealthData, SuccessResponse
from services.chat_service import stream_chat_events
from services.upload_service import process_contract_upload


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize runtime dependencies and validate startup configuration."""
    config.validate()
    app.state.chroma_client = chromadb.PersistentClient(
        path=str(config.CHROMA_PERSIST_DIR)
    )
    async with AsyncSqliteSaver.from_conn_string(
        str(config.SQLITE_DB_PATH)
    ) as checkpointer:
        set_checkpointer(checkpointer)
        app.state.agent = await create_agent(app.state.chroma_client)
        yield


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    lifespan=lifespan,
)

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


@app.exception_handler(AppError)
async def app_error_handler(_: Request, error: AppError) -> JSONResponse:
    """Return structured API errors for known application exceptions."""
    payload = ErrorResponse(
        error=error.message,
        code=error.code,
        details=error.details,
    )
    return JSONResponse(status_code=error.status_code, content=payload.model_dump())


@app.exception_handler(HTTPException)
async def http_error_handler(_: Request, error: HTTPException) -> JSONResponse:
    """Map HTTPExceptions into the standard error response envelope."""
    detail = error.detail if isinstance(error.detail, str) else "Request failed."
    payload = ErrorResponse(error=detail, code="HTTP_ERROR")
    return JSONResponse(status_code=error.status_code, content=payload.model_dump())


@app.exception_handler(RequestValidationError)
async def request_validation_handler(_: Request, error: RequestValidationError) -> JSONResponse:
    """Return typed validation failures for malformed request payloads."""
    payload = ErrorResponse(
        error="Request validation failed.",
        code="VALIDATION_ERROR",
        details={"errors": error.errors()},
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, _error: Exception) -> JSONResponse:
    """Return a safe generic payload for unhandled server errors."""
    payload = ErrorResponse(
        error="Internal server error.",
        code="INTERNAL_SERVER_ERROR",
        details=None,
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


@app.post("/api/upload_contract", response_model=SuccessResponse, status_code=201)
async def upload_contract(file: UploadFile = File(...)) -> SuccessResponse:
    """Validate and index an uploaded contract PDF."""
    content = await file.read()
    result = process_contract_upload(
        file.filename, file.content_type, content, app.state.chroma_client
    )
    return SuccessResponse(data=result.model_dump())


@app.get("/api/chat/stream")
async def chat_stream(
    query: str = Query(..., min_length=1, max_length=config.MAX_QUERY_LENGTH),
    thread_id: str = Query(..., min_length=1),
) -> StreamingResponse:
    """Stream agent responses as structured SSE events."""
    agent = getattr(app.state, "agent", None)
    if agent is None:
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
    """Report backend health status for uptime checks."""
    data = HealthData(service="docintel-backend", version=config.APP_VERSION)
    return SuccessResponse(data=data.model_dump())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=config.BACKEND_PORT, reload=True)
