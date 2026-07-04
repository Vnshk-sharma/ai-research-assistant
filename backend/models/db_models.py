"""
ORM models: Paper, Chunk, ChatMessage, Note.
"""

import uuid
from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from database.database import Base


def gen_uuid() -> str:
    return str(uuid.uuid4())


class Paper(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True, default=gen_uuid)
    filename = Column(String, nullable=False)
    title = Column(String, nullable=True)
    authors = Column(String, nullable=True)   # comma-separated
    year = Column(String, nullable=True)
    num_pages = Column(Integer, default=0)
    upload_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="processing")  # processing | ready | failed
    reading_progress = Column(Integer, default=0)   # 0-100 percent

    chunks = relationship("Chunk", back_populates="paper", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="paper", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=gen_uuid)
    paper_id = Column(String, ForeignKey("papers.id"), nullable=False)
    section = Column(String, nullable=True)
    page_number = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)
    vector_index = Column(Integer, nullable=False)  # position inside the FAISS index

    paper = relationship("Paper", back_populates="chunks")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=gen_uuid)
    paper_id = Column(String, ForeignKey("papers.id"), nullable=True)
    role = Column(String, nullable=False)   # user | assistant
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Note(Base):
    __tablename__ = "notes"

    id = Column(String, primary_key=True, default=gen_uuid)
    paper_id = Column(String, ForeignKey("papers.id"), nullable=False)
    title = Column(String, default="Untitled Note")
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    paper = relationship("Paper", back_populates="notes")
