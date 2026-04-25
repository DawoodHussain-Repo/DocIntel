"""Typed LangChain invocation helpers."""

from __future__ import annotations

import asyncio
from typing import Any, TypeVar

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from core.errors import AppError


logger = structlog.get_logger("docintel.llm_utils")
TModel = TypeVar("TModel", bound=BaseModel)


def estimate_token_count(*parts: str) -> int:
    """Estimate token usage conservatively from plain text inputs."""
    return sum(max(1, len(part) // 4) for part in parts if part)


async def invoke_structured_model(
    llm: Any,
    schema: type[TModel],
    system_prompt: str,
    user_prompt: str,
    chain_name: str,
    max_attempts: int = 3,
) -> TModel:
    """Invoke an LLM and validate the response with a Pydantic schema."""
    structured_llm = llm.with_structured_output(schema)
    estimated_tokens = estimate_token_count(system_prompt, user_prompt)
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(
                "llm_chain_started",
                chain_name=chain_name,
                attempt=attempt,
                estimated_tokens=estimated_tokens,
            )
            result = await structured_llm.ainvoke(
                [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt),
                ]
            )
            validated = result if isinstance(result, schema) else schema.model_validate(result)
            logger.info(
                "llm_chain_completed",
                chain_name=chain_name,
                attempt=attempt,
            )
            return validated
        except Exception as error:
            last_error = error
            logger.warning(
                "llm_chain_failed",
                chain_name=chain_name,
                attempt=attempt,
                error_type=type(error).__name__,
                error_message=str(error),
            )
            if attempt == max_attempts:
                break
            await asyncio.sleep(2 ** (attempt - 1))

    raise AppError(
        message="Model invocation failed.",
        code="MODEL_INVOCATION_FAILED",
        status_code=500,
        details={"chain": chain_name, "error": str(last_error) if last_error else "unknown"},
    ) from last_error
