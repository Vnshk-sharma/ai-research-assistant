"""
Database engine + session management (SQLite via SQLAlchemy).
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from utils.config import settings

engine = create_engine(
    settings.DB_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and guarantees closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables. Called once on application startup."""
    from models import db_models  # noqa: F401 - ensures models are registered
    Base.metadata.create_all(bind=engine)
