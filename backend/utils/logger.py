"""Structured logging configuration with JSON output for production."""
import logging
import sys
from typing import Any

import structlog

from core.config import config


def setup_logging() -> None:
    """Configure structlog with JSON rendering for production observability."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.LOG_LEVEL.upper()),
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if config.LOG_FORMAT == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, config.LOG_LEVEL.upper())
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "docintel") -> Any:
    """Get a bound logger instance with the specified name."""
    return structlog.get_logger(name)


def sanitize_for_logging(data: Any, max_length: int = 100) -> Any:
    """Sanitize data for logging to prevent PII leakage and log bloat."""
    if isinstance(data, str):
        if len(data) > max_length:
            return f"{data[:max_length]}... (truncated, length={len(data)})"
        return data
    
    if isinstance(data, (list, tuple)):
        return f"<{type(data).__name__} length={len(data)}>"
    
    if isinstance(data, dict):
        return {k: sanitize_for_logging(v, max_length) for k, v in data.items()}
    
    return data
