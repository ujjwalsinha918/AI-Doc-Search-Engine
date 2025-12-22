from backend.rag.pipeline import get_or_create_collection
from typing import List, Optional, Dict, Any


def search(query: str, document_id: int | None = None, user_email: str = "",) -> tuple[List[str] , List[Dict[str, Any]]]:
    """
    Retrieve relevant chunks from the user's Chroma collection.

    Args:
        query: The search query (semantic similarity).
        document_id: Optional filter to a specific document.
        user_email: User's email to isolate their collection.

    Returns:
        Tuple of (documents list, metadatas list) — always lists, never None.
    """
    collection = get_or_create_collection(user_email)
    where_clause = {"document_id": document_id} if document_id is not None else None
    results= collection.query(
        query_texts=[query],
        n_results=8,
        where=where_clause,
        include=["documents", "metadatas"]
    )
    
    docs = results["documents"][0] if results["documents"] and results["documents"][0] else []
    metas = results["metadatas"][0] if results["metadatas"] and results["metadatas"][0] else []
    return docs, metas

def summarize(chunks: list[str]) -> str:
    """
    Simple truncation-based summary.
    Can be upgraded to LLM-based summarization later.

    Args:
        chunks: List of text chunks.

    Returns:
        Truncated summary string.
    """
    if not chunks:
        return "No content to summarize."
    
    text = " ".join(chunks)
    # truncate to ~500 tokens (rough limit)
    return text[:2000] + ("..." if len(text) > 2000 else "")
    
def extract(chunks: list[str], field: str) -> List[str]:
    """
    Naive keyword-based extraction of a field (e.g., "email", "name").

    Args:
        chunks: List of text chunks.
        field: The keyword/field to extract.

    Returns:
        List of matching chunks.
    """
    if not chunks:
        return []
    keyword = field.lower()
    return [chunk for chunk in chunks if keyword in chunk.lower()]