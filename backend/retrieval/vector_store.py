"""
FAISS-backed vector store.

Stores chunk embeddings in a single flat inner-product index (cosine
similarity, since embeddings are pre-normalized). The mapping from FAISS
row -> chunk metadata lives in the relational DB (Chunk.vector_index), so
this class only needs to manage the raw vectors + persistence to disk.
"""

import threading
from pathlib import Path

import numpy as np
import faiss

from utils.config import settings

_INDEX_PATH = settings.FAISS_DIR / "index.faiss"


class VectorStore:
    """A thin, thread-safe wrapper around a single FAISS IndexFlatIP."""

    def __init__(self, dim: int = None, index_path: Path = None):
        self.dim = dim or settings.EMBEDDING_DIM
        self.index_path = index_path or _INDEX_PATH
        self._lock = threading.Lock()
        self._index = self._load_or_create()

    def _load_or_create(self):
        if self.index_path.exists():
            return faiss.read_index(str(self.index_path))
        return faiss.IndexFlatIP(self.dim)

    def add(self, vectors: np.ndarray) -> list[int]:
        """Add vectors, return the row indices they were assigned."""
        with self._lock:
            start = self._index.ntotal
            self._index.add(vectors)
            self._persist()
            return list(range(start, start + vectors.shape[0]))

    def search(self, query_vector: np.ndarray, top_k: int) -> tuple[np.ndarray, np.ndarray]:
        """Returns (scores, indices), both shape (top_k,)."""
        with self._lock:
            if self._index.ntotal == 0:
                return np.array([]), np.array([])
            query_vector = query_vector.reshape(1, -1)
            scores, indices = self._index.search(query_vector, min(top_k, self._index.ntotal))
            return scores[0], indices[0]

    def _persist(self):
        faiss.write_index(self._index, str(self.index_path))

    @property
    def size(self) -> int:
        return self._index.ntotal


_store_instance: VectorStore | None = None
_store_lock = threading.Lock()


def get_vector_store() -> VectorStore:
    global _store_instance
    if _store_instance is None:
        with _store_lock:
            if _store_instance is None:
                _store_instance = VectorStore()
    return _store_instance
