"""
Pydantic schemas used for request validation and API responses.
Kept separate from the ORM models (models/db_models.py) so the DB schema
can evolve independently of the public API contract.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PaperOut(BaseModel):
    id: str
    filename: str
    title: Optional[str]
    authors: Optional[str]
    year: Optional[str]
    num_pages: int
    status: str
    reading_progress: int
    upload_date: datetime

    class Config:
        from_attributes = True


class CitationOut(BaseModel):
    paper_id: str
    paper_title: str
    section: Optional[str]
    page_number: Optional[int]
    similarity_score: float
    snippet: str


class ChatRequest(BaseModel):
    query: str
    paper_id: Optional[str] = None   # None => search across all papers
    top_k: int = 5


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationOut]


class SummarizeRequest(BaseModel):
    paper_id: str
    length: str = "medium"   # short | medium | long


class CompareRequest(BaseModel):
    paper_id_a: str
    paper_id_b: str


class ExplainRequest(BaseModel):
    paper_id: str
    paragraph: str


class NoteCreate(BaseModel):
    paper_id: str
    title: str = "Untitled Note"
    content: str


class NoteOut(BaseModel):
    id: str
    paper_id: str
    title: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class QuizQuestion(BaseModel):
    question: str
    answer: str


class SearchResult(BaseModel):
    paper_id: str
    paper_title: str
    section: Optional[str]
    page_number: Optional[int]
    similarity_score: float
    snippet: str
