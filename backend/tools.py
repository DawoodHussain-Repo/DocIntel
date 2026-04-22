import os
import chromadb
from langchain.tools import tool
from dotenv import load_dotenv

load_dotenv()

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
)

@tool
def search_legal_clauses(query: str) -> str:
    """Search for relevant legal clauses in indexed documents.
    
    Args:
        query: The search query to find relevant contract clauses
        
    Returns:
        Formatted string with top 3 most relevant clauses
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
        return f"Error searching documents: {str(e)}"
