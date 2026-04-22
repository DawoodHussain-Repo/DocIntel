import os
import hashlib
import chromadb
from typing import List, Dict
from unstructured.partition.pdf import partition_pdf
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

# Initialize ChromaDB client
chroma_client = chromadb.PersistentClient(
    path=os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
)

def chunk_by_headings(elements, source_file: str) -> List[Dict]:
    """Chunk document using heading-aware strategy."""
    chunks = []
    current_chunk = []
    current_heading = None
    chunk_index = 0
    
    for element in elements:
        element_type = element.category
        
        # Check if this is a heading
        if element_type in ["Title", "Header"]:
            # Save previous chunk if it exists
            if current_chunk:
                chunks.append({
                    "text": "\n".join(current_chunk),
                    "metadata": {
                        "source_file": source_file,
                        "page_number": getattr(element, "metadata", {}).get("page_number", 1),
                        "heading": current_heading,
                        "chunk_index": chunk_index
                    }
                })
                chunk_index += 1
                current_chunk = []
            
            # Start new chunk with this heading
            current_heading = element.text
            current_chunk.append(element.text)
        else:
            current_chunk.append(element.text)
    
    # Add final chunk
    if current_chunk:
        chunks.append({
            "text": "\n".join(current_chunk),
            "metadata": {
                "source_file": source_file,
                "page_number": getattr(elements[-1], "metadata", {}).get("page_number", 1),
                "heading": current_heading,
                "chunk_index": chunk_index
            }
        })
    
    return chunks

def semantic_chunk_fallback(text: str, source_file: str, max_tokens: int = 800, overlap: int = 100) -> List[Dict]:
    """Fallback to semantic chunking if no headings found."""
    # Approximate tokens (rough estimate: 1 token ≈ 4 chars)
    max_chars = max_tokens * 4
    overlap_chars = overlap * 4
    
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        end = start + max_chars
        chunk_text = text[start:end]
        
        chunks.append({
            "text": chunk_text,
            "metadata": {
                "source_file": source_file,
                "page_number": 1,  # Unknown in fallback mode
                "heading": None,
                "chunk_index": chunk_index
            }
        })
        
        chunk_index += 1
        start = end - overlap_chars
    
    return chunks

def process_pdf(file_path: str, filename: str) -> Dict:
    """Process PDF: parse, chunk, embed, and store in ChromaDB."""
    
    # Parse PDF using Unstructured
    elements = partition_pdf(file_path)
    
    # Check if we have headings
    has_headings = any(e.category in ["Title", "Header"] for e in elements)
    
    if has_headings:
        chunks = chunk_by_headings(elements, filename)
    else:
        # Fallback to semantic chunking
        full_text = "\n".join([e.text for e in elements])
        chunks = semantic_chunk_fallback(full_text, filename)
    
    # Generate embeddings
    texts = [chunk["text"] for chunk in chunks]
    embeddings = embedding_model.encode(texts).tolist()
    
    # Generate document IDs
    doc_ids = [
        hashlib.md5(f"{filename}_{chunk['metadata']['chunk_index']}".encode()).hexdigest()
        for chunk in chunks
    ]
    
    # Get or create collection
    try:
        collection = chroma_client.get_collection("legal_docs")
    except:
        collection = chroma_client.create_collection("legal_docs")
    
    # Upsert to ChromaDB
    collection.upsert(
        ids=doc_ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=[chunk["metadata"] for chunk in chunks]
    )
    
    return {
        "status": "success",
        "file": filename,
        "chunks_indexed": len(chunks),
        "collection": "legal_docs"
    }
