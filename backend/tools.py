"""ChromaDB tools for legal document search."""
from typing import Any, Dict, List

from langchain.tools import tool

from config import config


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
    def search_legal_clauses(query: str) -> str:
        """Search indexed legal documents and return top matching clauses.

        The tool returns up to SEARCH_RESULT_LIMIT matching chunks with page
        numbers and headings. If no matches are found, it returns the exact
        out-of-scope response phrase expected by the product.
        Never raises exceptions; failures are returned as descriptive text.

        Args:
            query: User query for contract clause retrieval.

        Returns:
            String payload with formatted clause excerpts or failure text.
        """
        try:
            collection = chroma_client.get_collection("legal_docs")
            results = collection.query(
                query_texts=[query],
                n_results=config.SEARCH_RESULT_LIMIT,
            )

            documents = results.get("documents", [[]])
            metadatas = results.get("metadatas", [[]])
            if not documents or not documents[0]:
                return "This clause is not present in the document."

            return _format_query_results(documents[0], metadatas[0])
        except Exception as error:
            return f"Search failed: {error}. Please try a different query."

    return search_legal_clauses
