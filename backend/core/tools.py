"""ChromaDB tools for legal document search."""
import re
from typing import Any, Dict, List, Optional

import structlog
from langchain.tools import tool

from core.config import config


logger = structlog.get_logger("docintel.tools")


def _sanitize_query(query: str) -> str:
    """Sanitize user query to prevent injection and limit length."""
    sanitized = query.strip()
    
    # Remove control characters
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)
    
    # Trim to max length
    if len(sanitized) > config.MAX_QUERY_LENGTH:
        sanitized = sanitized[:config.MAX_QUERY_LENGTH]
    
    return sanitized


def _sanitize_source_file(source_file: Optional[str]) -> Optional[str]:
    """Sanitize a filename used for per-document filtering."""
    if not source_file:
        return None

    sanitized = source_file.replace("\x00", "").strip()
    sanitized = sanitized.split("/")[-1].split("\\")[-1]
    sanitized = re.sub(r"[^a-zA-Z0-9._-]", "_", sanitized)
    if not sanitized:
        return None
    return sanitized[:255]


def _format_query_results(
    documents: List[str],
    metadatas: List[Dict[str, Any]],
) -> str:
    """Format retrieval output with page and heading metadata for grounding."""
    formatted_chunks: List[str] = []
    for index, (document, metadata) in enumerate(zip(documents, metadatas), 1):
        page_num = metadata.get("page_number", "Unknown")
        heading = metadata.get("heading", "Document Section")
        formatted_chunks.append(
            (
                f"--- Clause [{index}] (Page {page_num}, Heading: {heading}) ---\n"
                f"{document}"
            )
        )
    return "\n\n".join(formatted_chunks)


def create_search_legal_clauses_tool(chroma_client: Any):
    """Build a search tool with injected dependencies for deterministic behavior."""

    @tool
    def search_legal_clauses(query: str, source_file: Optional[str] = None) -> str:
        """Search indexed legal documents and return top matching clauses.

        The tool returns up to SEARCH_RESULT_LIMIT matching chunks with page
        numbers and headings. If no matches are found, it returns the exact
        out-of-scope response phrase expected by the product.
        Never raises exceptions; failures are returned as descriptive text.

        Args:
            query: User query for contract clause retrieval.
            source_file: Optional uploaded filename to scope search results.

        Returns:
            String payload with formatted clause excerpts or failure text.
        """
        sanitized_query = _sanitize_query(query)
        sanitized_source_file = _sanitize_source_file(source_file)
        
        if not sanitized_query:
            logger.warning("tool_search_empty_query")
            return "This clause is not present in the document."
        
        logger.info(
            "tool_search_invoked",
            query_length=len(sanitized_query),
        )
        
        try:
            collection = chroma_client.get_collection("legal_docs")
            if sanitized_source_file:
                results = collection.query(
                    query_texts=[sanitized_query],
                    n_results=config.SEARCH_RESULT_LIMIT,
                    where={"source_file": sanitized_source_file},
                )
            else:
                results = collection.query(
                    query_texts=[sanitized_query],
                    n_results=config.SEARCH_RESULT_LIMIT,
                )

            documents = results.get("documents", [[]])
            metadatas = results.get("metadatas", [[]])
            
            if not documents or not documents[0]:
                logger.info("tool_search_no_results")
                return "This clause is not present in the document."

            result_count = len(documents[0])
            logger.info("tool_search_completed", result_count=result_count)
            
            return _format_query_results(documents[0], metadatas[0])
            
        except Exception as error:
            logger.exception(
                "tool_search_failed",
                error_type=type(error).__name__,
                error_message=str(error),
            )
            return f"Search failed: {error}. Please try a different query."

    return search_legal_clauses
