"""
Centralized application configuration.

All tunable parameters (model names, chunk sizes, storage paths) live here so
the rest of the codebase never hardcodes magic values.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Paths -----------------------------------------------------------
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "storage" / "uploads"
    FAISS_DIR: Path = BASE_DIR / "storage" / "faiss_index"
    DB_URL: str = f"sqlite:///{BASE_DIR / 'storage' / 'research_assistant.db'}"

    # --- Embeddings --------------------------------------------------------
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384

    # --- Reasoning / generation model --------------------------------------
    # A single instruction-tuned seq2seq model handles summarization, QA,
    # explanation, comparison, keyword extraction, etc. via task-specific
    # prompts. This keeps the "AI reasoning layer" cohesive and easy to
    # swap out (e.g. for a larger flan-t5 or a local llama.cpp model) later.
    GENERATION_MODEL: str = "google/flan-t5-base"
    MAX_NEW_TOKENS: int = 512

    # --- Chunking ------------------------------------------------------
    CHUNK_SIZE: int = 800          # characters per chunk
    CHUNK_OVERLAP: int = 150       # character overlap between consecutive chunks
    TOP_K_RETRIEVAL: int = 5

    # --- API -----------------------------------------------------------
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

# Ensure storage directories exist at import time.
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.FAISS_DIR.mkdir(parents=True, exist_ok=True)
