"""Pydantic models for API request and response contracts."""
from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field


class UploadContractData(BaseModel):
    """Upload result payload for a successfully indexed contract."""

    file: str = Field(..., min_length=1)
    chunks_indexed: int = Field(..., ge=0)
    collection: str = Field(..., min_length=1)


class HealthData(BaseModel):
    """Health status payload for backend monitoring."""

    service: str
    version: str


class StreamDoneData(BaseModel):
    """Final SSE completion payload."""

    finish_reason: Literal["stop", "error", "timeout"]
    error: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success envelope for all non-streaming endpoints."""

    status: Literal["success"] = "success"
    data: Any
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standard error envelope for all API failures."""

    status: Literal["error"] = "error"
    error: str
    code: str
    details: Optional[Dict[str, Any]] = None
