"""PDF ingestion pipeline with heading-aware chunking."""
import hashlib
from typing import Any, Dict, List

from sentence_transformers import SentenceTransformer
from unstructured.partition.pdf import partition_pdf

from config import config
from errors import AppError

COLLECTION_NAME = "legal_docs"

embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)


def _extract_page_number(metadata: Any) -> int:
    """Extract a stable positive page number from unstructured metadata."""
    page_number = getattr(metadata, "page_number", 1)
    if isinstance(page_number, int) and page_number > 0:
        return page_number
    return 1


def chunk_by_headings(elements: List[Any], source_file: str) -> List[Dict[str, Any]]:
    """Chunk document content by title/header boundaries when available."""
    chunks: List[Dict[str, Any]] = []
    current_chunk_lines: List[str] = []
    current_heading = "Document Section"
    current_page = 1
    chunk_index = 0

    for element in elements:
        element_text = (getattr(element, "text", "") or "").strip()
        if not element_text:
            continue

        element_type = getattr(element, "category", "")
        page_number = _extract_page_number(getattr(element, "metadata", None))

        if element_type in ["Title", "Header"]:
            if current_chunk_lines:
                chunks.append(
                    {
                        "text": "\n".join(current_chunk_lines),
                        "metadata": {
                            "source_file": source_file,
                            "page_number": current_page,
                            "heading": current_heading,
                            "chunk_index": chunk_index,
                        },
                    }
                )
                chunk_index += 1

            current_chunk_lines = [element_text]
            current_heading = element_text
            current_page = page_number
            continue

        if not current_chunk_lines:
            current_page = page_number
        current_chunk_lines.append(element_text)

    if current_chunk_lines:
        chunks.append(
            {
                "text": "\n".join(current_chunk_lines),
                "metadata": {
                    "source_file": source_file,
                    "page_number": current_page,
                    "heading": current_heading,
                    "chunk_index": chunk_index,
                },
            }
        )

    return chunks


def semantic_chunk_fallback(
    text: str,
    source_file: str,
    max_tokens: int = 800,
    overlap: int = 100,
) -> List[Dict[str, Any]]:
    """Chunk text by approximate token windows when heading signals are absent."""
    max_chars = max_tokens * 4
    overlap_chars = overlap * 4
    chunks: List[Dict[str, Any]] = []

    start = 0
    chunk_index = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(
                {
                    "text": chunk_text,
                    "metadata": {
                        "source_file": source_file,
                        "page_number": 1,
                        "heading": "Document Section",
                        "chunk_index": chunk_index,
                    },
                }
            )
            chunk_index += 1

        if end >= len(text):
            break
        start = max(0, end - overlap_chars)

    return chunks


def process_pdf(file_path: str, filename: str, chroma_client: Any) -> Dict[str, Any]:
    """Parse, chunk, embed, and index a PDF document in ChromaDB."""
    try:
        elements = partition_pdf(file_path)
    except Exception as error:
        raise AppError(
            message=f"Failed to parse PDF: {error}",
            code="PDF_PARSE_FAILED",
            status_code=500,
        ) from error

    valid_elements = [element for element in elements if getattr(element, "text", "")]
    if not valid_elements:
        raise AppError(
            message="The uploaded PDF does not contain extractable text.",
            code="EMPTY_DOCUMENT",
            status_code=422,
        )

    has_headings = any(
        getattr(element, "category", "") in ["Title", "Header"]
        for element in valid_elements
    )
    if has_headings:
        chunks = chunk_by_headings(valid_elements, filename)
    else:
        full_text = "\n".join((element.text or "") for element in valid_elements)
        chunks = semantic_chunk_fallback(full_text, filename)

    if not chunks:
        raise AppError(
            message="Unable to create chunks from the uploaded PDF.",
            code="CHUNKING_FAILED",
            status_code=500,
        )

    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_model.encode(texts).tolist()
    doc_ids = [
        hashlib.md5(
            f"{filename}_{chunk['metadata']['chunk_index']}".encode("utf-8")
        ).hexdigest()
        for chunk in chunks
    ]

    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)
    collection.upsert(
        ids=doc_ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=[chunk["metadata"] for chunk in chunks],
    )

    return {
        "file": filename,
        "chunks_indexed": len(chunks),
        "collection": COLLECTION_NAME,
    }
