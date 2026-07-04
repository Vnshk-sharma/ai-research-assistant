"""
One-off migration: re-extract title/authors/year for existing papers using
the fixed PDFExtractor heuristic (font-size based title detection +
boilerplate filtering), without re-running chunking/embedding.

Run from the `backend/` directory (same place you'd run `main.py`), after
you've already replaced preprocessing/pdf_extractor.py with the fixed
version:

    cd research-assistant/backend
    python migrate_fix_titles.py

Safe to re-run: it only touches Paper.title / Paper.authors / Paper.year,
and skips any paper whose PDF file can no longer be found on disk (leaving
it untouched and printing a warning instead of failing).
"""

from pathlib import Path

from database.database import SessionLocal
from models.db_models import Paper
from preprocessing.pdf_extractor import PDFExtractor
from utils.config import settings


def find_pdf_path(paper: Paper) -> Path | None:
    """Papers are saved as `{paper_id}_{original_filename}` under
    UPLOAD_DIR. Try the exact expected name first, then fall back to a
    glob in case filenames were sanitized differently.
    """
    expected = settings.UPLOAD_DIR / f"{paper.id}_{paper.filename}"
    if expected.exists():
        return expected

    matches = list(settings.UPLOAD_DIR.glob(f"{paper.id}_*"))
    return matches[0] if matches else None


def main():
    extractor = PDFExtractor()
    db = SessionLocal()
    updated, skipped, unchanged = 0, 0, 0

    try:
        papers = db.query(Paper).all()
        print(f"Found {len(papers)} paper(s) in the database.\n")

        for paper in papers:
            pdf_path = find_pdf_path(paper)
            if pdf_path is None:
                print(f"[SKIP] {paper.id} — original PDF not found in {settings.UPLOAD_DIR}, "
                      f"old title kept: {paper.title!r}")
                skipped += 1
                continue

            old_title = paper.title
            try:
                extracted = extractor.extract(str(pdf_path))
            except Exception as e:
                print(f"[SKIP] {paper.id} — failed to re-extract ({e}), old title kept: {old_title!r}")
                skipped += 1
                continue

            if extracted.title == old_title and extracted.authors == paper.authors:
                print(f"[OK]   {paper.id} — unchanged: {old_title!r}")
                unchanged += 1
                continue

            paper.title = extracted.title
            paper.authors = extracted.authors
            paper.year = extracted.year or paper.year
            db.add(paper)
            print(f"[FIX]  {paper.id}\n         before: {old_title!r}\n         after:  {extracted.title!r}")
            updated += 1

        db.commit()
        print(f"\nDone. updated={updated} unchanged={unchanged} skipped={skipped}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
