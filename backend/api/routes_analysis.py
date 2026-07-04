"""
Higher-level research-assistant feature endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from models.schemas import SummarizeRequest, CompareRequest, ExplainRequest
from services.analysis_service import get_analysis_service

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


def _wrap(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/summarize")
def summarize(request: SummarizeRequest, db: Session = Depends(get_db)):
    service = get_analysis_service()
    summary = _wrap(service.summarize, db, request.paper_id, request.length)
    return {"paper_id": request.paper_id, "summary": summary}


@router.post("/compare")
def compare(request: CompareRequest, db: Session = Depends(get_db)):
    service = get_analysis_service()
    result = _wrap(service.compare, db, request.paper_id_a, request.paper_id_b)
    return {"paper_id_a": request.paper_id_a, "paper_id_b": request.paper_id_b, "comparison": result}


@router.post("/explain")
def explain(request: ExplainRequest, db: Session = Depends(get_db)):
    if not request.paragraph.strip():
        raise HTTPException(status_code=400, detail="paragraph must not be empty")
    service = get_analysis_service()
    return {"explanation": service.explain_paragraph(request.paragraph)}


@router.get("/{paper_id}/keywords")
def keywords(paper_id: str, db: Session = Depends(get_db)):
    service = get_analysis_service()
    return {"paper_id": paper_id, "keywords": _wrap(service.keywords, db, paper_id)}


@router.get("/{paper_id}/contributions")
def contributions(paper_id: str, db: Session = Depends(get_db)):
    service = get_analysis_service()
    return {"paper_id": paper_id, "contributions": _wrap(service.contributions, db, paper_id)}


@router.get("/{paper_id}/limitations")
def limitations(paper_id: str, db: Session = Depends(get_db)):
    service = get_analysis_service()
    return {"paper_id": paper_id, "limitations": _wrap(service.limitations, db, paper_id)}


@router.get("/{paper_id}/future-work")
def future_work(paper_id: str, db: Session = Depends(get_db)):
    service = get_analysis_service()
    return {"paper_id": paper_id, "future_work": _wrap(service.future_work, db, paper_id)}


@router.get("/{paper_id}/notes-auto")
def reading_notes(paper_id: str, db: Session = Depends(get_db)):
    service = get_analysis_service()
    return {"paper_id": paper_id, "notes": _wrap(service.reading_notes, db, paper_id)}


@router.get("/{paper_id}/quiz")
def quiz(paper_id: str, num_questions: int = 5, db: Session = Depends(get_db)):
    service = get_analysis_service()
    return {"paper_id": paper_id, "quiz": _wrap(service.quiz, db, paper_id, num_questions)}


@router.get("/{paper_id}/related")
def related(paper_id: str, top_k: int = 3, db: Session = Depends(get_db)):
    service = get_analysis_service()
    return {"paper_id": paper_id, "related": _wrap(service.related_papers, db, paper_id, top_k)}
