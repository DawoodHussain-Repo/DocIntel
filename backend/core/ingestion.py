"""PDF ingestion pipeline with heading-aware chunking and recursive text splitting."""
import hashlib
from typing import Any, Dict, List

from sentence_transformers import SentenceTransformer
from unstructured.partition.pdf import partition_pdf

from core.config import config
from core.errors import AppError

COLLECTION_NAME = "legal_docs"

embedding_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)


class RecursiveTextSplitter:
    """Recursive text splitter with semantic separators for legal documents."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = [
            "\n\n\n",  # Multiple blank lines (section breaks)
            "\n\n",    # Paragraph breaks
            "\n",      # Line breaks
            ". ",      # Sentence endings
            "; ",      # Clause separators
            ", ",      # List items
            " ",       # Word boundaries
            "",        # Character-level fallback
        ]

    def split_text(self, text: str) -> List[str]:
        """Split text recursively using semantic separators."""
        return self._split_text_recursive(text, self.separators)

    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using the first applicable separator."""
        if not text or len(text) <= self.chunk_size:
            return [text] if text else []

        if not separators:
            return self._split_by_length(text)

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            return self._split_by_length(text)

        splits = text.split(separator)
        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            split_length = len(split)

            if current_length + split_length + len(separator) <= self.chunk_size:
                current_chunk.append(split)
                current_length += split_length + len(separator)
            else:
                if current_chunk:
                    chunk_text = separator.join(current_chunk)
                    if len(chunk_text) > self.chunk_size:
                        chunks.extend(
                            self._split_text_recursive(chunk_text, remaining_separators)
                        )
                    else:
                        chunks.append(chunk_text)

                current_chunk = [split]
                current_length = split_length

        if current_chunk:
            chunk_text = separator.join(current_chunk)
            if len(chunk_text) > self.chunk_size:
                chunks.extend(
                    self._split_text_recursive(chunk_text, remaining_separators)
                )
            else:
                chunks.append(chunk_text)

        return self._merge_chunks_with_overlap(chunks)

    def _split_by_length(self, text: str) -> List[str]:
        """Split text by character length as final fallback."""
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            chunks.append(text[start:end])
            start = end - self.chunk_overlap if end < len(text) else end
        return chunks

    def _merge_chunks_with_overlap(self, chunks: List[str]) -> List[str]:
        """Merge chunks with overlap to preserve context across boundaries."""
        if not chunks or self.chunk_overlap == 0:
            return chunks

        merged = []
        for i, chunk in enumerate(chunks):
            if i == 0:
                merged.append(chunk)
            else:
                overlap_text = merged[-1][-self.chunk_overlap:]
                merged.append(overlap_text + chunk)

        return merged


def _extract_page_number(metadata: Any) -> int:
    """Extract a stable positive page number from unstructured metadata."""
    page_number = getattr(metadata, "page_number", 1)
    if isinstance(page_number, int) and page_number > 0:
        return page_number
    return 1


def chunk_by_headings(elements: List[Any], source_file: str) -> List[Dict[str, Any]]:
    """Chunk document content by title/header boundaries with recursive splitting."""
    text_splitter = RecursiveTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

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
                section_text = "\n".join(current_chunk_lines)
                
                if len(section_text) > config.CHUNK_SIZE:
                    sub_chunks = text_splitter.split_text(section_text)
                    for sub_chunk in sub_chunks:
                        if sub_chunk.strip():
                            chunks.append(
                                {
                                    "text": sub_chunk.strip(),
                                    "metadata": {
                                        "source_file": source_file,
                                        "page_number": current_page,
                                        "heading": current_heading,
                                        "chunk_index": chunk_index,
                                    },
                                }
                            )
                            chunk_index += 1
                else:
                    chunks.append(
                        {
                            "text": section_text,
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
        section_text = "\n".join(current_chunk_lines)
        
        if len(section_text) > config.CHUNK_SIZE:
            sub_chunks = text_splitter.split_text(section_text)
            for sub_chunk in sub_chunks:
                if sub_chunk.strip():
                    chunks.append(
                        {
                            "text": sub_chunk.strip(),
                            "metadata": {
                                "source_file": source_file,
                                "page_number": current_page,
                                "heading": current_heading,
                                "chunk_index": chunk_index,
                            },
                        }
                    )
                    chunk_index += 1
        else:
            chunks.append(
                {
                    "text": section_text,
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
) -> List[Dict[str, Any]]:
    """Chunk text using recursive splitting when heading signals are absent."""
    text_splitter = RecursiveTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )

    sub_chunks = text_splitter.split_text(text)
    chunks: List[Dict[str, Any]] = []

    for chunk_index, chunk_text in enumerate(sub_chunks):
        if chunk_text.strip():
            chunks.append(
                {
                    "text": chunk_text.strip(),
                    "metadata": {
                        "source_file": source_file,
                        "page_number": 1,
                        "heading": "Document Section",
                        "chunk_index": chunk_index,
                    },
                }
            )

    return chunks


def process_pdf(file_path: str, filename: str, chroma_client: Any) -> Dict[str, Any]:
    """Parse, chunk, embed, and index a PDF document in ChromaDB."""
    try:
        elements = partition_pdf(
            file_path,
            strategy="fast",
            extract_images_in_pdf=False,
            infer_table_structure=False,
        )
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
