"""Service for secure contract upload validation and ingestion orchestration."""
from typing import Any, Optional

from ingestion import process_pdf
from models import UploadContractData
from errors import AppError
from config import config


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
    _validate_upload(content_type, content)

    safe_file_name = file_name or "uploaded_contract.pdf"
    temp_file_path = config.WORKSPACE_DIR / f"{config.create_uuid()}.pdf"

    try:
        config.WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        temp_file_path.write_bytes(content)
        ingestion_result = process_pdf(str(temp_file_path), safe_file_name, chroma_client)
    except AppError:
        raise
    except Exception as error:
        raise AppError(
            message=f"Failed to process uploaded contract: {error}",
            code="UPLOAD_PROCESSING_FAILED",
            status_code=500,
        ) from error
    finally:
        if temp_file_path.exists():
            temp_file_path.unlink()

    return UploadContractData(**ingestion_result)
