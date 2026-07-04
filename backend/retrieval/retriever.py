"""
Retrieval pipeline.

Converts a natural-language query into an embedding, searches the FAISS
index for the most similar chunks, then joins those hits back to their
relational metadata (paper title, section, page number) for citation.
"""

from dataclasses import dataclass
from sqlalchemy.orm import Session

from embeddings.embedder import get_embedder
from retrieval.vector_store import get_vector_store
from models.db_models import Chunk, Paper
from utils.config import settings


@dataclass
class RetrievedChunk:
    chunk_id: str
    paper_id: str
    paper_title: str
    section: str | None
    page_number: int | None
    text: str
    similarity_score: float


class Retriever:
    def __init__(self):
        self.embedder = get_embedder()
        self.vector_store = get_vector_store()

    def retrieve(
        self,
        db: Session,
        query: str,
        top_k: int = None,
        paper_id: str | None = None,
    ) -> list[RetrievedChunk]:
        top_k = top_k or settings.TOP_K_RETRIEVAL
        query_vec = self.embedder.embed_query(query)

        # Over-fetch when filtering to a single paper, since the flat FAISS
        # index has no built-in metadata filter — we filter after the fact.
        fetch_k = top_k * 6 if paper_id else top_k
        scores, indices = self.vector_store.search(query_vec, fetch_k)

        if len(indices) == 0:
            return []

        # Bulk-fetch matching chunk rows in one query.
        vector_indices = [int(i) for i in indices if i != -1]
        chunks_by_vidx = {
            c.vector_index: c
            for c in db.query(Chunk).filter(Chunk.vector_index.in_(vector_indices)).all()
        }

        results: list[RetrievedChunk] = []
        for score, vidx in zip(scores, indices):
            chunk = chunks_by_vidx.get(int(vidx))
            if chunk is None:
                continue
            if paper_id and chunk.paper_id != paper_id:
                continue

            paper = chunk.paper
            results.append(
                RetrievedChunk(
                    chunk_id=chunk.id,
                    paper_id=chunk.paper_id,
                    paper_title=paper.title if paper else "Unknown",
                    section=chunk.section,
                    page_number=chunk.page_number,
                    text=chunk.text,
                    similarity_score=float(score),
                )
            )
            if len(results) >= top_k:
                break

        # Results already come back rank-ordered from FAISS, but re-sort
        # defensively in case of duplicate scores / filtering.
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results


_retriever_instance: Retriever | None = None


def get_retriever() -> Retriever:
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = Retriever()
    return _retriever_instance
