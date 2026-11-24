import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from agents.rag.embedder import DenseEmbedder
from agents.rag.vector_store import VectorStore

logger = logging.getLogger("RAGTools")

def search_codebase(
    db: Session,
    submission_id: str,
    query: str,
    top_k: int = 5,
    min_score: float = 0.0,
    symbol_type: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Semantic Code Search Tool for Agentic Evaluation Council.
    Enables agents to query large multi-file codebases without context window overflow.
    Returns ranked code snippets with exact file and line citations.
    """
    if not query or not query.strip():
        return []

    # 1. Embed query
    query_vector = DenseEmbedder.embed_text(query)

    # 2. Ranked similarity retrieval
    results = VectorStore.similarity_search(
        db=db,
        submission_id=submission_id,
        query_vector=query_vector,
        top_k=top_k,
        min_score=min_score,
        symbol_type=symbol_type
    )

    logger.debug(f"Retrieved {len(results)} chunks for query '{query}' in submission '{submission_id}'.")
    return results
