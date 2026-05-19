"""NLTK resource bootstrapping for PDF parsing dependencies."""

from __future__ import annotations

from functools import lru_cache
from typing import Final

import nltk
import structlog

from core.config import config
from core.errors import AppError


logger = structlog.get_logger("docintel.nltk_resources")

REQUIRED_RESOURCES: Final[tuple[tuple[str, str], ...]] = (
    ("tokenizers/punkt/english.pickle", "punkt"),
    ("tokenizers/punkt_tab/english/", "punkt_tab"),
)


def _configure_nltk_data_path() -> None:
    config.NLTK_DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_dir = str(config.NLTK_DATA_DIR)
    if data_dir not in nltk.data.path:
        nltk.data.path.insert(0, data_dir)


@lru_cache(maxsize=1)
def ensure_nltk_resources() -> None:
    """Ensure sentence tokenization resources exist before OCR fallbacks run."""
    _configure_nltk_data_path()

    missing_downloads: list[str] = []
    for resource_path, download_name in REQUIRED_RESOURCES:
        try:
            nltk.data.find(resource_path)
        except LookupError:
            missing_downloads.append(download_name)

    if not missing_downloads:
        logger.info(
            "nltk_resources_ready",
            resources=[download_name for _, download_name in REQUIRED_RESOURCES],
            data_dir=str(config.NLTK_DATA_DIR),
        )
        return

    if not config.AUTO_DOWNLOAD_NLTK:
        raise AppError(
            message="Required NLTK resources are missing on the server.",
            code="NLTK_RESOURCE_MISSING",
            status_code=503,
            details={"resources": missing_downloads},
        )

    logger.info(
        "nltk_resource_download_started",
        resources=missing_downloads,
        data_dir=str(config.NLTK_DATA_DIR),
    )
    for download_name in missing_downloads:
        downloaded = nltk.download(
            download_name,
            download_dir=str(config.NLTK_DATA_DIR),
            quiet=True,
        )
        if not downloaded:
            raise AppError(
                message="Failed to download required NLTK resources.",
                code="NLTK_DOWNLOAD_FAILED",
                status_code=500,
                details={"resource": download_name},
            )

    for resource_path, download_name in REQUIRED_RESOURCES:
        try:
            nltk.data.find(resource_path)
        except LookupError as error:
            raise AppError(
                message="NLTK resources are still unavailable after download.",
                code="NLTK_RESOURCE_MISSING",
                status_code=500,
                details={"resource": download_name},
            ) from error

    logger.info(
        "nltk_resource_download_completed",
        resources=missing_downloads,
        data_dir=str(config.NLTK_DATA_DIR),
    )
