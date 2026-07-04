"""
Chat + semantic search endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from models.schemas import ChatRequest, ChatResponse, SearchResult
from services.chat_service import get_chat_service
from retrieval.retriever import get_retriever
from utils.citation import SNIPPET_LEN

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="query must not be empty")
    service = get_chat_service()
    return service.ask(db, request.query, request.paper_id, request.top_k)


@router.get("/search", response_model=list[SearchResult])
def semantic_search(q: str, paper_id: str | None = None, top_k: int = 5, db: Session = Depends(get_db)):
    if not q.strip():
        raise HTTPException(status_code=400, detail="q must not be empty")
    retriever = get_retriever()
    results = retriever.retrieve(db, q, top_k=top_k, paper_id=paper_id)
    return [
        SearchResult(
            paper_id=r.paper_id,
            paper_title=r.paper_title,
            section=r.section,
            page_number=r.page_number,
            similarity_score=round(r.similarity_score, 4),
            snippet=(r.text[:SNIPPET_LEN] + "…") if len(r.text) > SNIPPET_LEN else r.text,
        )
        for r in results
    ]
