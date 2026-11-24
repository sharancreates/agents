import os
import logging
from typing import Dict, Any
from sqlalchemy.orm import Session

from agents.rag.chunker import ASTCodeChunker
from agents.rag.embedder import DenseEmbedder
from agents.rag.vector_store import VectorStore

logger = logging.getLogger("CodebaseIndexer")

class CodebaseIndexer:
    """
    Coordinates scanning, chunking, embedding, and storing repository vector indices.
    """

    @classmethod
    def index_submission(
        cls,
        db: Session,
        submission_id: str,
        repo_path: str,
        delete_existing: bool = True
    ) -> Dict[str, Any]:
        """
        Parses repository into AST chunks, embeds each chunk, and persists to VectorStore.
        """
        if not os.path.exists(repo_path):
            raise FileNotFoundError(f"Repository path '{repo_path}' does not exist.")

        if delete_existing:
            VectorStore.delete_submission_embeddings(db, submission_id)

        # 1. Chunk files
        raw_chunks = ASTCodeChunker.chunk_directory(repo_path)
        if not raw_chunks:
            logger.warning(f"No source files extracted from {repo_path}.")
            return {"submission_id": submission_id, "chunks_indexed": 0, "status": "empty"}

        # 2. Dense Embedding in batch
        texts_to_embed = [c["content"] for c in raw_chunks]
        embeddings = DenseEmbedder.embed_batch(texts_to_embed)

        for chunk, emb in zip(raw_chunks, embeddings):
            chunk["embedding"] = emb

        # 3. Store in database
        stored_count = VectorStore.store_embeddings(db, submission_id, raw_chunks)

        logger.info(f"Indexed {stored_count} chunks for submission '{submission_id}'.")
        return {
            "submission_id": submission_id,
            "chunks_indexed": stored_count,
            "repo_path": repo_path,
            "status": "complete"
        }
