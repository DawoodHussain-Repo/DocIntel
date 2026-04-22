"""ChromaDB tools for legal document search."""
import chromadb
from langchain.tools import tool
from config import config

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)


@tool
def search_legal_clauses(query: str) -> str:
    """Search for relevant legal clauses in indexed documents.
    
    Returns the top 3 most similar chunks with page numbers and headings.
    If no results are found, returns a message stating so.
    Never raises exceptions — returns error description as string on failure.
    
    Args:
        query: The search query to find relevant contract clauses
        
    Returns:
        Formatted string with top 3 most relevant clauses or error message
    """
    try:
        collection = chroma_client.get_collection("legal_docs")
        
        results = collection.query(
            query_texts=[query],
            n_results=3
        )
        
        if not results["documents"] or len(results["documents"][0]) == 0:
            return "No relevant clauses found in the indexed documents."
        
        formatted_output = []
        for i, (doc, metadata) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
            page_num = metadata.get("page_number", "Unknown")
            heading = metadata.get("heading", "No heading")
            
            formatted_output.append(
                f"--- Clause [{i}] (Page {page_num}, Heading: {heading}) ---\n{doc}"
            )
        
        return "\n\n".join(formatted_output)
    
    except Exception as e:
        return f"Search failed: {e}. Please try a different query."
