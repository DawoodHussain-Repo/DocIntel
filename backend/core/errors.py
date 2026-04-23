"""Application error types for structured API failure handling."""
from typing import Any, Dict, Optional


class AppError(Exception):
    """Structured application error with machine-readable code."""

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
