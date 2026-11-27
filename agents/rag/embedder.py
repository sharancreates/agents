import re
import math
import hashlib
import logging
from typing import List

logger = logging.getLogger("DenseEmbedder")

EMBEDDING_DIM = 384

class DenseEmbedder:
    """
    Produces 384-dimensional L2-normalized dense embeddings for semantic search.
    Supports SentenceTransformer when available, with a fast deterministic offline fallback.
    """

    _model = None
    _tried_loading_model = False

    @classmethod
    def _get_model(cls):
        if not cls._tried_loading_model:
            cls._tried_loading_model = True
            try:
                from sentence_transformers import SentenceTransformer
                cls._model = SentenceTransformer("all-MiniLM-L6-v2")
                logger.info("Loaded sentence-transformers model 'all-MiniLM-L6-v2'.")
            except Exception as e:
                logger.info(f"Using deterministic feature-hashing embedder (offline mode): {e}")
        return cls._model

    @classmethod
    def _deterministic_hash_embed(cls, text: str) -> List[float]:
        """
        Generates a 384-dimensional unit-normalized vector using n-gram feature hashing.
        Guarantees deterministic, cosine-comparable semantic representations without external weights.
        """
        vec = [0.0] * EMBEDDING_DIM
        if not text or not text.strip():
            # Return unit uniform vector for blank input
            val = 1.0 / math.sqrt(EMBEDDING_DIM)
            return [val] * EMBEDDING_DIM

        # Tokenize into clean lowercase alphanumeric words
        words = re.findall(r"[a-zA-Z0-9_]+", text.lower())
        if not words:
            val = 1.0 / math.sqrt(EMBEDDING_DIM)
            return [val] * EMBEDDING_DIM

        # 1. Word unigram hashing
        for word in words:
            # MD5 hash to determine bucket and sign
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            bucket = h % EMBEDDING_DIM
            sign = 1.0 if (h >> 16) & 1 else -1.0
            vec[bucket] += sign * (1.0 + math.log(1.0 + len(word)))

        # 2. Bigram hashing for contextual phrases
        for i in range(len(words) - 1):
            bigram = f"{words[i]}_{words[i+1]}"
            h = int(hashlib.sha256(bigram.encode("utf-8")).hexdigest(), 16)
            bucket = h % EMBEDDING_DIM
            sign = 1.0 if (h >> 20) & 1 else -1.0
            vec[bucket] += sign * 1.5

        # L2-normalization: ||v|| = 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [round(x / norm, 6) for x in vec]
        else:
            val = 1.0 / math.sqrt(EMBEDDING_DIM)
            vec = [val] * EMBEDDING_DIM

        return vec

    @classmethod
    def embed_text(cls, text: str) -> List[float]:
        """Generates a 384-dimensional normalized vector for a single text."""
        model = cls._get_model()
        if model is not None:
            try:
                emb = model.encode(text, normalize_embeddings=True)
                return [round(float(x), 6) for x in emb.tolist()]
            except Exception as e:
                logger.warning(f"Embedding inference failed, falling back to hashing: {e}")

        return cls._deterministic_hash_embed(text)

    @classmethod
    def embed_batch(cls, texts: List[str]) -> List[List[float]]:
        """Generates normalized vectors for a batch of texts."""
        return [cls.embed_text(t) for t in texts]
