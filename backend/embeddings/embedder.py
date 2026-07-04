"""
Embedding module — wraps a Sentence-Transformers model.

Lazily loaded (and a process-wide singleton) so the model is only pulled
into memory once, and only when actually needed.
"""

import numpy as np
from functools import lru_cache

from utils.config import settings


class Embedder:
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self._model = None

    @property
    def model(self):
        if self._model is None:
            # Imported lazily: sentence-transformers/torch are heavy and we
            # don't want to pay that cost at API startup.
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        """Return an (N, EMBEDDING_DIM) float32 array of L2-normalized embeddings."""
        embeddings = self.model.encode(
            texts,
            batch_size=32,
            convert_to_numpy=True,
            normalize_embeddings=True,  # so inner product == cosine similarity
            show_progress_bar=False,
        )
        return embeddings.astype("float32")

    def embed_query(self, query: str) -> np.ndarray:
        return self.embed_texts([query])[0]


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return Embedder()
