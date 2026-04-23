"""Service for streaming agent events as compliant SSE output."""
import asyncio
import json
import uuid
from typing import Any, AsyncGenerator, Dict

from langchain_core.messages import HumanMessage

from config import config
from errors import AppError
from models import StreamDoneData


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
    if not query.strip():
        raise AppError(
            message="Query cannot be empty.",
            code="EMPTY_QUERY",
            status_code=400,
        )

    if len(query) > config.MAX_QUERY_LENGTH:
        raise AppError(
            message=(
                f"Query exceeds maximum length of {config.MAX_QUERY_LENGTH} characters."
            ),
            code="QUERY_TOO_LONG",
            status_code=400,
        )

    validated_thread_id = validate_thread_id(thread_id)
    agent_input = {"messages": [HumanMessage(content=query.strip())]}
    agent_config = {"configurable": {"thread_id": validated_thread_id}}

    try:
        async for event in agent.astream_events(agent_input, agent_config, version="v1"):
            if event.get("event") != "on_chat_model_stream":
                continue

            chunk = event.get("data", {}).get("chunk")

            if chunk and hasattr(chunk, "tool_calls") and chunk.tool_calls:
                for tool_call in chunk.tool_calls:
                    yield _format_sse_event(
                        "tool_call",
                        {
                            "tool": tool_call.get("name", "unknown_tool"),
                            "query": str(tool_call.get("args", {})),
                        },
                    )

            token_text = _extract_text(chunk)
            if token_text:
                yield _format_sse_event("token", {"text": token_text})

        done_payload = StreamDoneData(finish_reason="stop", error=None).model_dump()
        yield _format_sse_event("done", done_payload)

    except asyncio.CancelledError:
        return
    except Exception as error:
        done_payload = StreamDoneData(
            finish_reason="error",
            error=f"Streaming failed: {error}",
        ).model_dump()
        yield _format_sse_event("done", done_payload)
