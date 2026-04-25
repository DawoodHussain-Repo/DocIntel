"""Retrieval helpers for scoped ChromaDB access (per-document)."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple

import structlog

from core.errors import AppError
from core.models import DocumentChunk


logger = structlog.get_logger("docintel.retrieval")


def _dedupe_by_chunk_index(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[Tuple[str, int]] = set()
    deduped: List[Dict[str, Any]] = []
    for item in items:
        source_file = str(item.get("source_file") or "")
        chunk_index = int(item.get("chunk_index") or 0)
        key = (source_file, chunk_index)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def get_legal_collection(chroma_client: Any):
    """Get the default legal document collection or raise a typed error."""
    try:
        return chroma_client.get_collection("legal_docs")
    except Exception as error:
        raise AppError(
            message="No documents have been indexed yet.",
            code="COLLECTION_NOT_READY",
            status_code=422,
            details={"error": str(error)},
        ) from error


def retrieve_chunks(
    chroma_client: Any,
    query: str,
    source_file: str,
    n_results: int = 4,
) -> List[Dict[str, Any]]:
    """Retrieve the top chunks for a query scoped to a specific uploaded file."""
    if not source_file or not source_file.strip():
        raise AppError(
            message="file is required.",
            code="MISSING_FILE",
            status_code=400,
        )

    collection = get_legal_collection(chroma_client)
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"source_file": source_file},
            include=["documents", "metadatas", "distances"],
        )
    except TypeError:
        # Older Chroma versions may not support include/distances; fall back safely.
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={"source_file": source_file},
        )

    documents = (results or {}).get("documents", [[]])[0] or []
    metadatas = (results or {}).get("metadatas", [[]])[0] or []
    distances = (results or {}).get("distances", [[]])[0] if isinstance((results or {}).get("distances"), list) else None

    items: List[Dict[str, Any]] = []
    for idx, (doc, meta) in enumerate(zip(documents, metadatas)):
        distance = None
        if distances and idx < len(distances):
            distance = distances[idx]
        items.append(
            {
                "text": doc,
                "distance": distance,
                "source_file": meta.get("source_file", source_file),
                "page_number": meta.get("page_number", 1),
                "heading": meta.get("heading", "Document Section"),
                "chunk_index": meta.get("chunk_index", idx),
            }
        )

    return items


def retrieve_document_chunks(
    chroma_client: Any,
    source_file: str,
) -> List[DocumentChunk]:
    """Retrieve all indexed chunks for a document in stable chunk order."""
    ensure_document_exists(chroma_client, source_file)
    collection = get_legal_collection(chroma_client)
    results = collection.get(
        where={"source_file": source_file},
        include=["documents", "metadatas"],
    )

    documents = (results or {}).get("documents") or []
    metadatas = (results or {}).get("metadatas") or []

    chunks = [
        DocumentChunk(
            source_file=str(metadata.get("source_file", source_file)),
            text=str(document),
            page_number=int(metadata.get("page_number", 1) or 1),
            heading=str(metadata.get("heading", "Document Section")),
            chunk_index=int(metadata.get("chunk_index", index) or index),
        )
        for index, (document, metadata) in enumerate(zip(documents, metadatas))
    ]
    return sorted(chunks, key=lambda chunk: chunk.chunk_index)


def retrieve_for_queries(
    chroma_client: Any,
    queries: List[str],
    source_file: str,
    n_results_each: int = 3,
    max_total: int = 18,
) -> List[Dict[str, Any]]:
    """Retrieve and dedupe chunks across multiple queries, scoped to one file."""
    all_items: List[Dict[str, Any]] = []
    for query in queries:
        if not query.strip():
            continue
        all_items.extend(retrieve_chunks(chroma_client, query, source_file, n_results_each))

    deduped = _dedupe_by_chunk_index(all_items)
    return deduped[:max_total]


def ensure_document_exists(chroma_client: Any, source_file: str) -> None:
    """Raise when the requested document has no chunks in the collection."""
    collection = get_legal_collection(chroma_client)
    try:
        results = collection.get(
            where={"source_file": source_file},
            include=["metadatas"],
            limit=1,
        )
        ids = (results or {}).get("ids") or []
        if ids:
            return
    except TypeError:
        # Some versions do not support `limit`; fall back to query.
        results = collection.query(
            query_texts=["contract"],
            n_results=1,
            where={"source_file": source_file},
        )
        docs = (results or {}).get("documents", [[]])[0] or []
        if docs:
            return

    raise AppError(
        message="Requested document was not found in the index. Upload it first.",
        code="DOCUMENT_NOT_FOUND",
        status_code=404,
        details={"file": source_file},
    )


def retrieve_comprehensive_evidence(
    chroma_client: Any,
    source_file: str,
    max_chunks: int = 20,
) -> List[Dict[str, Any]]:
    """
    Retrieve diverse, high-quality chunks covering all contract aspects.
    Uses strategic queries to ensure comprehensive coverage.
    
    Args:
        chroma_client: ChromaDB client
        source_file: Document filename to retrieve from
        max_chunks: Maximum number of chunks to return (default 20)
    
    Returns:
        List of deduplicated chunks with diverse contract coverage
    """
    # Strategic queries covering all major contract aspects
    comprehensive_queries = [
        "parties names effective date commencement",
        "term duration period renewal automatic",
        "payment fees amount compensation invoice schedule",
        "termination notice cause convenience breach",
        "liability indemnification limitation cap exclusion",
        "confidentiality proprietary information disclosure",
        "intellectual property ownership rights license",
        "governing law jurisdiction venue arbitration",
        "warranties representations disclaimers as-is",
        "assignment transfer subcontracting delegation",
    ]
    
    # Retrieve with higher n_results to ensure diversity
    all_items = retrieve_for_queries(
        chroma_client,
        comprehensive_queries,
        source_file,
        n_results_each=3,
        max_total=max_chunks,
    )
    
    logger.info(
        "comprehensive_evidence_retrieved",
        source_file=source_file,
        chunks_retrieved=len(all_items),
        max_chunks=max_chunks,
    )
    
    return all_items
