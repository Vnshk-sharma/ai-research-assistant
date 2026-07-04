"""
Analysis service — implements the higher-level research-assistant features
that operate on whole papers rather than a single retrieved chunk:
summarize, compare, explain, extract contributions/limitations, suggest
future work, generate notes/quizzes, and recommend related papers.
"""

import numpy as np
from sqlalchemy.orm import Session

from services.paper_service import get_paper_service
from summarization.reasoning_engine import get_reasoning_engine
from embeddings.embedder import get_embedder
from models.db_models import Paper, Chunk


class AnalysisService:
    def __init__(self):
        self.paper_service = get_paper_service()
        self.reasoner = get_reasoning_engine()
        self.embedder = get_embedder()

    def _paper_or_404(self, db: Session, paper_id: str) -> Paper:
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if paper is None:
            raise ValueError(f"Paper {paper_id} not found")
        return paper

    def summarize(self, db: Session, paper_id: str, length: str = "medium") -> str:
        self._paper_or_404(db, paper_id)
        text = self.paper_service.get_full_text(db, paper_id)
        return self.reasoner.summarize(text, length=length)

    def explain_paragraph(self, paragraph: str) -> str:
        return self.reasoner.explain_paragraph(paragraph)

    def compare(self, db: Session, paper_id_a: str, paper_id_b: str) -> str:
        paper_a = self._paper_or_404(db, paper_id_a)
        paper_b = self._paper_or_404(db, paper_id_b)
        text_a = self.paper_service.get_full_text(db, paper_id_a, max_chars=3000)
        text_b = self.paper_service.get_full_text(db, paper_id_b, max_chars=3000)
        return self.reasoner.compare_papers(text_a, text_b, paper_a.title, paper_b.title)

    def keywords(self, db: Session, paper_id: str) -> list[str]:
        self._paper_or_404(db, paper_id)
        text = self.paper_service.get_full_text(db, paper_id)
        raw = self.reasoner.extract_keywords(text)
        return [k.strip() for k in raw.split(",") if k.strip()]

    def contributions(self, db: Session, paper_id: str) -> str:
        self._paper_or_404(db, paper_id)
        text = self.paper_service.get_full_text(db, paper_id)
        return self.reasoner.extract_contributions(text)

    def limitations(self, db: Session, paper_id: str) -> str:
        self._paper_or_404(db, paper_id)
        text = self.paper_service.get_full_text(db, paper_id)
        return self.reasoner.extract_limitations(text)

    def future_work(self, db: Session, paper_id: str) -> str:
        self._paper_or_404(db, paper_id)
        text = self.paper_service.get_full_text(db, paper_id)
        return self.reasoner.suggest_future_work(text)

    def reading_notes(self, db: Session, paper_id: str) -> str:
        self._paper_or_404(db, paper_id)
        text = self.paper_service.get_full_text(db, paper_id)
        return self.reasoner.generate_reading_notes(text)

    def quiz(self, db: Session, paper_id: str, num_questions: int = 5) -> str:
        self._paper_or_404(db, paper_id)
        text = self.paper_service.get_full_text(db, paper_id)
        return self.reasoner.generate_quiz(text, num_questions=num_questions)

    def related_papers(self, db: Session, paper_id: str, top_k: int = 3) -> list[dict]:
        """
        Recommend other uploaded papers whose chunk embeddings are, on
        average, most similar to this paper's chunk embeddings — a cheap
        proxy for topical similarity without a separate document-level
        embedding index.
        """
        self._paper_or_404(db, paper_id)
        target_chunks = db.query(Chunk).filter(Chunk.paper_id == paper_id).all()
        if not target_chunks:
            return []

        target_vecs = self.embedder.embed_texts([c.text for c in target_chunks[:20]])
        target_centroid = target_vecs.mean(axis=0)
        target_centroid /= np.linalg.norm(target_centroid) + 1e-8

        other_papers = db.query(Paper).filter(Paper.id != paper_id, Paper.status == "ready").all()
        scored = []
        for other in other_papers:
            other_chunks = db.query(Chunk).filter(Chunk.paper_id == other.id).limit(20).all()
            if not other_chunks:
                continue
            other_vecs = self.embedder.embed_texts([c.text for c in other_chunks])
            other_centroid = other_vecs.mean(axis=0)
            other_centroid /= np.linalg.norm(other_centroid) + 1e-8
            similarity = float(np.dot(target_centroid, other_centroid))
            scored.append({"paper_id": other.id, "title": other.title, "similarity_score": round(similarity, 4)})

        scored.sort(key=lambda x: x["similarity_score"], reverse=True)
        return scored[:top_k]


_analysis_service_instance: AnalysisService | None = None


def get_analysis_service() -> AnalysisService:
    global _analysis_service_instance
    if _analysis_service_instance is None:
        _analysis_service_instance = AnalysisService()
    return _analysis_service_instance
