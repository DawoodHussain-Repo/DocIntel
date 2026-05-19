"""Service for streaming agent events as compliant SSE output."""
import asyncio
import json
import uuid
from typing import Any, AsyncGenerator, AsyncIterator, Dict

import structlog
from langchain_core.messages import HumanMessage

from core.config import config
from core.errors import AppError
from core.models import StreamDoneData
from services.agent_service import AgentService
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


async def _iterate_with_timeout(
    iterator: AsyncIterator[str],
    timeout_seconds: int,
) -> AsyncGenerator[str, None]:
    """Iterate an async stream with an overall timeout compatible with Python 3.10."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_seconds

    while True:
        remaining = deadline - loop.time()
        if remaining <= 0:
            raise asyncio.TimeoutError

        try:
            next_event = await asyncio.wait_for(iterator.__anext__(), timeout=remaining)
        except StopAsyncIteration:
            return

        yield next_event


async def stream_chat_events(
    agent_service: AgentService,
    query: str,
    thread_id: str,
    active_document: str | None = None,
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
    
    token_count = 0
    tool_call_count = 0
    emitted_message_ids: set[str] = set()
    emitted_tool_call_ids: set[str] = set()

    async def _stream_agent_events() -> AsyncGenerator[str, None]:
        nonlocal token_count, tool_call_count

        async for event in agent_service.stream(
            sanitized_query,
            validated_thread_id,
            run_id,
            active_document=active_document,
        ):
            event_name = event.get("event")
            chunk = event.get("data", {}).get("chunk")
            output = event.get("data", {}).get("output")

            if event_name == "on_chat_model_stream":
                if chunk and hasattr(chunk, "tool_calls") and chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        tool_call_id = str(tool_call.get("id", f"tool-call-{tool_call_count + 1}"))
                        if tool_call_id in emitted_tool_call_ids:
                            continue
                        emitted_tool_call_ids.add(tool_call_id)
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
                continue

            if event_name == "on_chain_end" and event.get("name") == "llm":
                messages = output.get("messages") if isinstance(output, dict) else None
                if not isinstance(messages, list) or not messages:
                    continue

                message = messages[-1]
                message_id = str(getattr(message, "id", ""))

                tool_calls = getattr(message, "tool_calls", None) or []
                for tool_call in tool_calls:
                    tool_call_id = str(tool_call.get("id", f"tool-call-{tool_call_count + 1}"))
                    if tool_call_id in emitted_tool_call_ids:
                        continue
                    emitted_tool_call_ids.add(tool_call_id)
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

                token_text = _extract_text(message)
                if token_text and message_id not in emitted_message_ids:
                    emitted_message_ids.add(message_id)
                    token_count += 1
                    yield _format_sse_event("token", {"text": token_text})

    try:
        async for event in _iterate_with_timeout(
            _stream_agent_events(),
            config.AGENT_TIMEOUT_SECONDS,
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
            error_message=sanitize_for_logging(str(error), max_length=400),
        )
        
        done_payload = StreamDoneData(
            finish_reason="error",
            error="Streaming failed due to an internal server error.",
        ).model_dump()
        done_payload["run_id"] = run_id
        yield _format_sse_event("done", done_payload)
