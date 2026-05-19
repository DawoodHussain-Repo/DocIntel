"""Fast text-first PDF extraction with safe fallbacks."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from time import perf_counter
from typing import Any

import structlog
from pypdf import PdfReader
from unstructured.partition.pdf import partition_pdf

from core.config import config
from core.errors import AppError
from core.nltk_resources import ensure_nltk_resources


logger = structlog.get_logger("docintel.pdf_extraction")

HEADING_PATTERN = re.compile(
    r"^(?:section|clause|article)?\s*\d+(?:\.\d+)*[\)\].:\- ]+\S+",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class SimpleMetadata:
    """Minimal metadata shape expected by downstream chunking."""

    page_number: int = 1


@dataclass(frozen=True)
class SimpleElement:
    """Lightweight text element compatible with heading-aware chunking."""

    text: str
    category: str
    metadata: SimpleMetadata


def _is_heading_candidate(line: str) -> bool:
    text = line.strip()
    if len(text) < 3 or len(text) > 120:
        return False
    if HEADING_PATTERN.match(text):
        return True
    if text.endswith((".", ";", ",")):
        return False

    words = [word for word in re.split(r"\s+", text) if any(char.isalpha() for char in word)]
    if not words or len(words) > 10:
        return False

    if text.isupper():
        return True

    title_case_words = sum(1 for word in words if word[:1].isupper())
    return title_case_words / len(words) >= 0.85


def _normalize_page_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in (text or "").replace("\x00", " ").splitlines():
        normalized = re.sub(r"[ \t]+", " ", raw_line).strip()
        if normalized:
            lines.append(normalized)
    return "\n".join(lines)


def _filter_text_elements(elements: list[Any]) -> list[Any]:
    return [element for element in elements if getattr(element, "text", "").strip()]


def _extract_with_pypdf(file_path: str, filename: str) -> list[SimpleElement]:
    start_time = perf_counter()
    extracted_elements: list[SimpleElement] = []
    total_text_chars = 0

    try:
        reader = PdfReader(file_path, strict=False)
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as error:
                logger.warning(
                    "pypdf_decrypt_failed",
                    filename=filename,
                    error_type=type(error).__name__,
                )
                return []

        for page_number, page in enumerate(reader.pages, start=1):
            try:
                page_text = _normalize_page_text(page.extract_text() or "")
            except Exception as error:
                logger.warning(
                    "pypdf_page_extraction_failed",
                    filename=filename,
                    page_number=page_number,
                    error_type=type(error).__name__,
                    error_message=str(error),
                )
                continue

            if not page_text:
                continue

            total_text_chars += len(page_text)
            for line in page_text.splitlines():
                extracted_elements.append(
                    SimpleElement(
                        text=line,
                        category="Title" if _is_heading_candidate(line) else "NarrativeText",
                        metadata=SimpleMetadata(page_number=page_number),
                    )
                )

        duration_ms = round((perf_counter() - start_time) * 1000, 2)
        if total_text_chars < config.PDF_TEXT_MIN_CHARS:
            logger.info(
                "pypdf_extraction_insufficient",
                filename=filename,
                total_text_chars=total_text_chars,
                duration_ms=duration_ms,
            )
            return []

        logger.info(
            "pypdf_extraction_completed",
            filename=filename,
            pages=len(reader.pages),
            elements=len(extracted_elements),
            total_text_chars=total_text_chars,
            duration_ms=duration_ms,
        )
        return extracted_elements
    except Exception as error:
        logger.warning(
            "pypdf_extraction_failed",
            filename=filename,
            error_type=type(error).__name__,
            error_message=str(error),
        )
        return []


@lru_cache(maxsize=1)
def configure_tesseract_environment() -> str | None:
    """Make the system Tesseract binary discoverable for OCR fallbacks."""
    if os.name != "nt":
        return os.environ.get("TESSERACT_PATH")

    tesseract_dir = r"C:\Program Files\Tesseract-OCR"
    if not os.path.exists(tesseract_dir):
        logger.info("tesseract_directory_missing", path=tesseract_dir)
        return None

    current_path = os.environ.get("PATH", "")
    if tesseract_dir not in current_path:
        os.environ["PATH"] = f"{tesseract_dir};{current_path}"
        logger.info("tesseract_added_to_path", path=tesseract_dir)

    tesseract_exe = os.path.join(tesseract_dir, "tesseract.exe")
    if os.path.exists(tesseract_exe):
        os.environ["TESSERACT_PATH"] = tesseract_exe
        logger.info("tesseract_path_set", path=tesseract_exe)
        return tesseract_exe

    logger.info("tesseract_executable_missing", path=tesseract_exe)
    return None


def _extract_with_unstructured(
    file_path: str,
    filename: str,
    strategy: str,
    enable_ocr: bool,
) -> list[Any]:
    start_time = perf_counter()
    elements = partition_pdf(
        file_path,
        strategy=strategy,
        extract_images_in_pdf=enable_ocr,
        infer_table_structure=False,
    )
    valid_elements = _filter_text_elements(elements)
    logger.info(
        "unstructured_extraction_completed",
        filename=filename,
        strategy=strategy,
        enable_ocr=enable_ocr,
        element_count=len(valid_elements),
        duration_ms=round((perf_counter() - start_time) * 1000, 2),
    )
    return valid_elements


def extract_pdf_elements(file_path: str, filename: str) -> list[Any]:
    """Extract text elements with a fast digital-first path and safe fallbacks."""
    os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "0")

    pypdf_elements = _extract_with_pypdf(file_path, filename)
    if pypdf_elements:
        logger.info("pdf_text_extraction_selected", filename=filename, strategy="pypdf")
        return pypdf_elements

    last_error: Exception | None = None

    try:
        logger.info("pdf_parsing_attempt", strategy="fast", filename=filename)
        fast_elements = _extract_with_unstructured(
            file_path=file_path,
            filename=filename,
            strategy="fast",
            enable_ocr=False,
        )
        if fast_elements:
            logger.info("pdf_text_extraction_selected", filename=filename, strategy="fast")
            return fast_elements
    except Exception as error:
        last_error = error
        logger.warning(
            "pdf_fast_strategy_failed",
            filename=filename,
            error_type=type(error).__name__,
            error_message=str(error)[:200],
        )

    try:
        ensure_nltk_resources()
        logger.info("pdf_parsing_attempt", strategy="hi_res_no_ocr", filename=filename)
        hi_res_elements = _extract_with_unstructured(
            file_path=file_path,
            filename=filename,
            strategy="hi_res",
            enable_ocr=False,
        )
        if hi_res_elements:
            logger.info(
                "pdf_text_extraction_selected",
                filename=filename,
                strategy="hi_res_no_ocr",
            )
            return hi_res_elements
    except AppError:
        raise
    except Exception as error:
        last_error = error
        logger.warning(
            "pdf_hi_res_no_ocr_failed",
            filename=filename,
            error_type=type(error).__name__,
            error_message=str(error)[:200],
        )

    if not config.ENABLE_OCR_FALLBACK:
        raise AppError(
            message="The uploaded PDF could not be extracted without OCR.",
            code="PDF_TEXT_EXTRACTION_FAILED",
            status_code=422,
            details={"file": filename},
        )

    logger.info("pdf_attempting_ocr", filename=filename)
    configure_tesseract_environment()

    try:
        ensure_nltk_resources()
        logger.info("pdf_parsing_attempt", strategy="hi_res_with_ocr", filename=filename)
        ocr_elements = _extract_with_unstructured(
            file_path=file_path,
            filename=filename,
            strategy="hi_res",
            enable_ocr=True,
        )
        if ocr_elements:
            logger.info(
                "pdf_text_extraction_selected",
                filename=filename,
                strategy="hi_res_with_ocr",
            )
            return ocr_elements
        raise AppError(
            message=(
                "The uploaded PDF does not contain extractable text even after OCR. "
                "It may be empty, corrupted, or image-only with unreadable scans."
            ),
            code="EMPTY_DOCUMENT",
            status_code=422,
        )
    except AppError:
        raise
    except Exception as error:
        error_message = str(error).lower()
        if "tesseract" in error_message:
            raise AppError(
                message=(
                    "OCR is required for this PDF, but Tesseract is not installed "
                    "or is not available on the server PATH."
                ),
                code="OCR_NOT_AVAILABLE",
                status_code=422,
                details={"error": str(error)[:500]},
            ) from error

        raise AppError(
            message="Failed to extract text from the uploaded PDF.",
            code="PDF_PARSE_FAILED",
            status_code=500,
            details={
                "last_error": str(error)[:500],
                "previous_error": str(last_error)[:500] if last_error else None,
            },
        ) from error
