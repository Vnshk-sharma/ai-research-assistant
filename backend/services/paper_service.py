"""
Paper service — orchestrates the full ingestion pipeline for an uploaded PDF:

    Upload -> PyMuPDF extraction -> cleaning/section tagging -> chunking
    -> embedding -> FAISS indexing -> persisting chunk metadata in SQLite
"""

import shutil
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.orm import Session

from preprocessing.pdf_extractor import PDFExtractor
from preprocessing.text_cleaner import TextCleaner
from preprocessing.chunker import SemanticChunker
from embeddings.embedder import get_embedder
from retrieval.vector_store import get_vector_store
from models.db_models import Paper, Chunk
from utils.config import settings


class PaperService:
    def __init__(self):
        self.extractor = PDFExtractor()
        self.cleaner = TextCleaner()
        self.chunker = SemanticChunker()
        self.embedder = get_embedder()
        self.vector_store = get_vector_store()

    def _save_upload(self, file: UploadFile, paper_id: str) -> Path:
        dest = settings.UPLOAD_DIR / f"{paper_id}_{file.filename}"
        with dest.open("wb") as out:
            shutil.copyfileobj(file.file, out)
        return dest

    def ingest(self, db: Session, file: UploadFile) -> Paper:
        """Full synchronous ingestion pipeline for one PDF upload."""
        paper = Paper(filename=file.filename, status="processing")
        db.add(paper)
        db.commit()
        db.refresh(paper)

        try:
            file_path = self._save_upload(file, paper.id)

            extracted = self.extractor.extract(str(file_path))
            paper.title = extracted.title
            paper.authors = extracted.authors
            paper.year = extracted.year
            paper.num_pages = extracted.num_pages

            chunks = self.chunker.chunk_document(extracted.pages, self.cleaner)
            if not chunks:
                raise ValueError("No extractable text found in PDF.")

            texts = [c.text for c in chunks]
            vectors = self.embedder.embed_texts(texts)
            vector_indices = self.vector_store.add(vectors)

            for chunk, vidx in zip(chunks, vector_indices):
                db.add(
                    Chunk(
                        paper_id=paper.id,
                        section=chunk.section,
                        page_number=chunk.page_number,
                        text=chunk.text,
                        vector_index=vidx,
                    )
                )

            paper.status = "ready"
            db.commit()
            db.refresh(paper)
            return paper

        except Exception:
            paper.status = "failed"
            db.commit()
            raise

    def get_full_text(self, db: Session, paper_id: str, max_chars: int = 6000) -> str:
        """
        Concatenate a paper's chunks (in order) into a bounded context
        string, used as input to the reasoning engine for whole-paper tasks
        like summarization. Bounded because the generation model has a
        limited context window.
        """
        chunks = (
            db.query(Chunk)
            .filter(Chunk.paper_id == paper_id)
            .order_by(Chunk.vector_index)
            .all()
        )
        text = "\n\n".join(c.text for c in chunks)
        return text[:max_chars]


_paper_service_instance: PaperService | None = None


def get_paper_service() -> PaperService:
    global _paper_service_instance
    if _paper_service_instance is None:
        _paper_service_instance = PaperService()
    return _paper_service_instance
