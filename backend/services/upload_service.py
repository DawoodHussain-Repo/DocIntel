"""Service for secure contract upload validation and ingestion orchestration."""
import re
from typing import Any, Optional

import structlog

from core.ingestion import process_pdf
from core.models import UploadContractData
from core.errors import AppError
from core.config import config


logger = structlog.get_logger("docintel.upload_service")


def _sanitize_filename(filename: Optional[str]) -> str:
    """Sanitize filename to prevent path traversal and injection attacks."""
    if not filename:
        return "uploaded_contract.pdf"
    
    # Remove null bytes
    sanitized = filename.replace('\x00', '')
    
    # Extract just the filename (no path components)
    sanitized = sanitized.split('/')[-1].split('\\')[-1]
    
    # Reject path traversal attempts
    if '..' in sanitized or '/' in sanitized or '\\' in sanitized:
        return "uploaded_contract.pdf"
    
    # Keep only alphanumeric, hyphen, underscore, dot
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '_', sanitized)
    
    # Ensure it ends with .pdf
    if not sanitized.lower().endswith('.pdf'):
        sanitized = f"{sanitized}.pdf"
    
    # Limit length
    if len(sanitized) > 255:
        sanitized = sanitized[:251] + ".pdf"
    
    return sanitized


def _is_pdf_magic_header(content: bytes) -> bool:
    """Return True when file bytes begin with the PDF magic signature."""
    return content.startswith(b"%PDF-")


def _validate_upload(content_type: Optional[str], content: bytes) -> None:
    """Validate content type, signature, and size for contract uploads."""
    if content_type not in config.ALLOWED_MIME_TYPES:
        raise AppError(
            message="File must be a PDF.",
            code="INVALID_MIME_TYPE",
            status_code=400,
            details={"allowed": config.ALLOWED_MIME_TYPES},
        )

    if len(content) > config.MAX_FILE_SIZE_BYTES:
        raise AppError(
            message=(
                f"File size exceeds {config.MAX_FILE_SIZE_MB}MB limit."
            ),
            code="FILE_TOO_LARGE",
            status_code=413,
        )

    if not _is_pdf_magic_header(content):
        raise AppError(
            message="Uploaded file is not a valid PDF binary.",
            code="INVALID_PDF_SIGNATURE",
            status_code=400,
        )


def process_contract_upload(
    file_name: Optional[str],
    content_type: Optional[str],
    content: bytes,
    chroma_client: Any,
) -> UploadContractData:
    """Validate an upload and index the PDF into the legal document collection."""
    safe_file_name = _sanitize_filename(file_name)
    
    logger.info(
        "upload_received",
        filename=safe_file_name,
        size_bytes=len(content),
        content_type=content_type,
    )
    
    _validate_upload(content_type, content)
    logger.info("validation_passed")

    temp_file_path = config.WORKSPACE_DIR / f"{config.create_uuid()}.pdf"

    try:
        config.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        temp_file_path.write_bytes(content)
        
        logger.info(
            "pdf_parsing_started",
            filename=safe_file_name,
        )
        
        ingestion_result = process_pdf(str(temp_file_path), safe_file_name, chroma_client)
        
        logger.info(
            "upload_completed",
            filename=safe_file_name,
            chunks_indexed=ingestion_result.get("chunks_indexed", 0),
            collection=ingestion_result.get("collection", "unknown"),
        )
        
    except AppError:
        raise
    except Exception as error:
        logger.exception(
            "upload_processing_failed",
            error_type=type(error).__name__,
            error_message=str(error),
        )
        raise AppError(
            message=f"Failed to process uploaded contract: {error}",
            code="UPLOAD_PROCESSING_FAILED",
            status_code=500,
        ) from error
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()
            logger.debug("temp_file_cleaned")

    return UploadContractData(**ingestion_result)
