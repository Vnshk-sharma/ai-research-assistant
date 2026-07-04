"""
Paper management endpoints: upload, list, retrieve, delete, notes,
reading-progress tracking.
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from database.database import get_db
from models.db_models import Paper, Note
from models.schemas import PaperOut, NoteCreate, NoteOut
from services.paper_service import get_paper_service

router = APIRouter(prefix="/api/papers", tags=["papers"])


@router.post("/upload", response_model=PaperOut)
async def upload_paper(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    service = get_paper_service()
    try:
        paper = service.ingest(db, file)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Failed to process PDF: {exc}")
    return paper


@router.get("", response_model=list[PaperOut])
def list_papers(db: Session = Depends(get_db)):
    return db.query(Paper).order_by(Paper.upload_date.desc()).all()


@router.get("/{paper_id}", response_model=PaperOut)
def get_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    return paper


@router.delete("/{paper_id}")
def delete_paper(paper_id: str, db: Session = Depends(get_db)):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    db.delete(paper)
    db.commit()
    return {"deleted": paper_id}


@router.patch("/{paper_id}/progress")
def update_reading_progress(paper_id: str, progress: int, db: Session = Depends(get_db)):
    if not 0 <= progress <= 100:
        raise HTTPException(status_code=400, detail="progress must be between 0 and 100")
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if paper is None:
        raise HTTPException(status_code=404, detail="Paper not found")
    paper.reading_progress = progress
    db.commit()
    return {"paper_id": paper_id, "reading_progress": progress}


@router.post("/notes", response_model=NoteOut)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    db_note = Note(paper_id=note.paper_id, title=note.title, content=note.content)
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


@router.get("/{paper_id}/notes", response_model=list[NoteOut])
def list_notes(paper_id: str, db: Session = Depends(get_db)):
    return db.query(Note).filter(Note.paper_id == paper_id).all()
