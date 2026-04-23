"""Service for streaming agent events as compliant SSE output."""
import asyncio
import json
import uuid
from typing import Any, AsyncGenerator, Dict

import structlog
from langchain_core.messages import HumanMessage

from core.config import config
from core.errors import AppError
from core.models import StreamDoneData
from utils.logger import sanitize_for_logging


logger = structlog.get_logger("docintel.chat_service")


def _sanitize_query_input(query: str) -> str:
    """Sanitize and validate user query input."""
    # Strip whitespace
    sanitized = query.strip()
    
    # Reject purely whitespace queries
    if not sanitized:
        raise AppError(
            message="Query cannot be empty.",
            code="EMPTY_QUERY",
            status_code=400,
        )
    
    # Check length
    if len(sanitized) > config.MAX_QUERY_LENGTH:
        raise AppError(
            message=(
                f"Query exceeds maximum length of {config.MAX_QUERY_LENGTH} characters."
            ),
            code="QUERY_TOO_LONG",
            status_code=400,
        )
    
    return sanitized


def _format_sse_event(event_name: str, payload: Dict[str, Any]) -> str:
    """Serialize an SSE event using JSON data payloads only."""
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=True)}\n\n"


def validate_thread_id(thread_id: str) -> str:
    """Validate and normalize a UUID thread identifier string."""
    try:
        return str(uuid.UUID(thread_id))
    except ValueError as error:
        raise AppError(
            message="Invalid thread_id format. Expected UUID.",
            code="INVALID_THREAD_ID",
            status_code=400,
        ) from error


def _extract_text(chunk: Any) -> str:
    """Extract text content from streaming model chunks."""
    if chunk is None or not hasattr(chunk, "content"):
        return ""

    content = chunk.content
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        text_parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict)
        ]
        return "".join(text_parts)

    return ""


async def stream_chat_events(
    agent: Any,
    query: str,
    thread_id: str,
) -> AsyncGenerator[str, None]:
    """Yield tool_call, token, and done events for a chat query."""
    sanitized_query = _sanitize_query_input(query)
    validated_thread_id = validate_thread_id(thread_id)
    run_id = str(uuid.uuid4())
    
    structlog.contextvars.bind_contextvars(
        run_id=run_id,
        thread_id=validated_thread_id,
    )
    
    logger.info(
        "agent_stream_started",
        query_preview=sanitize_for_logging(sanitized_query, max_length=80),
    )
    
    agent_input = {
        "messages": [HumanMessage(content=sanitized_query)],
        "run_id": run_id,
        "thread_id": validated_thread_id,
    }
    agent_config = {"configurable": {"thread_id": validated_thread_id}}

    token_count = 0
    tool_call_count = 0

    try:
        # Wrap agent invocation with timeout
        async def _stream_with_timeout():
            nonlocal token_count, tool_call_count
            
            async for event in agent.astream_events(agent_input, agent_config, version="v1"):
                if event.get("event") != "on_chat_model_stream":
                    continue

                chunk = event.get("data", {}).get("chunk")

                if chunk and hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        tool_call_count += 1
                        tool_name = tool_call.get("name", "unknown_tool")
                        
                        logger.info(
                            "tool_call_invoked",
                            tool_name=tool_name,
                            tool_call_index=tool_call_count,
                        )
                        
                        yield _format_sse_event(
                            "tool_call",
                            {
                                "tool": tool_name,
                                "query": str(tool_call.get("args", {})),
                            },
                        )

                token_text = _extract_text(chunk)
                if token_text:
                    token_count += 1
                    yield _format_sse_event("token", {"text": token_text})
        
        async for event in asyncio.wait_for(
            _stream_with_timeout(),
            timeout=config.AGENT_TIMEOUT_SECONDS
        ):
            yield event

        logger.info(
            "agent_stream_completed",
            token_count=token_count,
            tool_call_count=tool_call_count,
            run_id=run_id,
        )
        
        done_payload = StreamDoneData(
            finish_reason="stop",
            error=None,
        ).model_dump()
        done_payload["run_id"] = run_id
        yield _format_sse_event("done", done_payload)

    except asyncio.TimeoutError:
        logger.warning(
            "agent_stream_timeout",
            timeout_seconds=config.AGENT_TIMEOUT_SECONDS,
        )
        
        done_payload = StreamDoneData(
            finish_reason="timeout",
            error=f"Agent timed out after {config.AGENT_TIMEOUT_SECONDS} seconds.",
        ).model_dump()
        done_payload["run_id"] = run_id
        yield _format_sse_event("done", done_payload)
        
    except asyncio.CancelledError:
        logger.info("agent_stream_cancelled")
        return
        
    except Exception as error:
        logger.exception(
            "agent_stream_failed",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        
        done_payload = StreamDoneData(
            finish_reason="error",
            error=f"Streaming failed: {error}",
        ).model_dump()
        done_payload["run_id"] = run_id
        yield _format_sse_event("done", done_payload)
