import math
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from api import models

logger = logging.getLogger("VectorStore")

def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Computes cosine similarity between two numeric vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)

class VectorStore:
    """
    Hybrid Vector Store providing sub-second semantic retrieval across codebases.
    Maintains compatibility with PostgreSQL (pgvector) and SQLite in-memory databases.
    """

    @staticmethod
    def store_embeddings(
        db: Session,
        submission_id: str,
        chunks: List[Dict[str, Any]]
    ) -> int:
        """
        Persists a batch of code chunk embeddings into the database.
        """
        if not chunks:
            return 0

        embedding_records = []
        for ch in chunks:
            rec = models.CodeEmbedding(
                submission_id=submission_id,
                file_path=ch.get("file_path", "unknown"),
                symbol_name=ch.get("symbol_name"),
                symbol_type=ch.get("symbol_type", "block"),
                start_line=ch.get("start_line", 1),
                end_line=ch.get("end_line", 1),
                content=ch.get("content", ""),
                embedding_json=ch.get("embedding", [])
            )
            embedding_records.append(rec)

        db.add_all(embedding_records)
        db.commit()
        logger.info(f"Stored {len(embedding_records)} vector embeddings for submission '{submission_id}'.")
        return len(embedding_records)

    @staticmethod
    def similarity_search(
        db: Session,
        submission_id: str,
        query_vector: List[float],
        top_k: int = 5,
        min_score: float = 0.0,
        symbol_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs ranked nearest-neighbor cosine similarity search.
        Returns top-k code chunks with exact line citations.
        """
        query = db.query(models.CodeEmbedding).filter(
            models.CodeEmbedding.submission_id == submission_id
        )

        if symbol_type:
            query = query.filter(models.CodeEmbedding.symbol_type == symbol_type)

        candidates = query.all()
        if not candidates:
            return []

        scored = []
        for cand in candidates:
            cand_vec = cand.embedding_json or []
            score = cosine_similarity(query_vector, cand_vec)
            if score >= min_score:
                scored.append({
                    "id": cand.id,
                    "submission_id": cand.submission_id,
                    "file_path": cand.file_path,
                    "symbol_name": cand.symbol_name,
                    "symbol_type": cand.symbol_type,
                    "start_line": cand.start_line,
                    "end_line": cand.end_line,
                    "content": cand.content,
                    "score": round(float(score), 4),
                    "citation": f"{cand.file_path}:{cand.start_line}-{cand.end_line}"
                })

        # Rank descending by cosine similarity score
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]

    @staticmethod
    def delete_submission_embeddings(db: Session, submission_id: str) -> int:
        """Removes existing indexed embeddings for re-indexing idempotency."""
        deleted = db.query(models.CodeEmbedding).filter(
            models.CodeEmbedding.submission_id == submission_id
        ).delete()
        db.commit()
        return deleted
