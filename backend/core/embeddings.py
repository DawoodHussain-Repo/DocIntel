"""Embedding model lifecycle helpers."""

from __future__ import annotations

from functools import lru_cache

import structlog
from sentence_transformers import SentenceTransformer

from core.config import config
from core.errors import AppError


logger = structlog.get_logger("docintel.embeddings")


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Return the shared embedding model instance."""
    try:
        logger.info(
            "embedding_model_initialization_started",
            model=config.EMBEDDING_MODEL_NAME,
        )
        model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        logger.info(
            "embedding_model_initialization_completed",
            model=config.EMBEDDING_MODEL_NAME,
        )
        return model
    except Exception as error:
        logger.exception(
            "embedding_model_initialization_failed",
            model=config.EMBEDDING_MODEL_NAME,
            error_type=type(error).__name__,
            error_message=str(error),
        )
        raise AppError(
            message=(
                "The embedding model is unavailable. Ensure the configured "
                "sentence-transformer is installed or cached locally."
            ),
            code="EMBEDDING_MODEL_UNAVAILABLE",
            status_code=503,
            details={"model": config.EMBEDDING_MODEL_NAME},
        ) from error
