"""
AI Research Assistant — FastAPI application entry point.

Run with:  uvicorn main:app --reload --port 8000
(from inside the backend/ directory, with dependencies from requirements.txt installed)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.database import init_db
from utils.config import settings
from api import routes_papers, routes_chat, routes_analysis

app = FastAPI(
    title="AI Research Assistant",
    description="RAG-powered assistant for uploading, searching, and reasoning over research papers.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_papers.router)
app.include_router(routes_chat.router)
app.include_router(routes_analysis.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health_check():
    return {"status": "ok"}
