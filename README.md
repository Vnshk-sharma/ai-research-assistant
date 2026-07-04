# Marginal — AI Research Assistant

[![CI](https://github.com/USERNAME/REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/USERNAME/REPO/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)


A production-quality Retrieval-Augmented Generation (RAG) system for uploading, searching, and reasoning over research papers. Built as a full-stack demonstration of transformer-based NLP, vector search, and clean backend/frontend architecture.

> Upload PDFs → ask natural-language questions → get answers with paper/section/page citations → summarize, compare, and study papers with AI-generated notes and quizzes.

---

## 1. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                │
│                     React 18 + Tailwind CSS (Vite)                   │
│   Library sidebar · Chat panel · Analysis tools · Compare panel      │
└───────────────────────────────┬───────────────────────────────────--┘
                                 │ REST (fetch, JSON)
┌────────────────────────────────▼──────────────────────────────────--┐
│                              BACKEND                                 │
│                          FastAPI (async)                             │
│  ┌───────────────┐  ┌────────────────┐  ┌───────────────────────┐   │
│  │  api/          │  │  services/     │  │  Cross-cutting        │   │
│  │  routes_papers │→│  paper_service  │  │  models/ (schemas +   │   │
│  │  routes_chat   │→│  chat_service   │  │  ORM), database/,     │   │
│  │  routes_analysis│→│ analysis_service│  │  utils/ (config,      │   │
│  └───────────────┘  └────────────────┘  │  citation)            │   │
│                                          └───────────────────────┘   │
│  ┌────────────────────────┐  ┌────────────────────────────────────┐ │
│  │  preprocessing/         │  │  embeddings/  →  retrieval/        │ │
│  │  pdf_extractor (PyMuPDF)│  │  embedder.py     vector_store.py   │ │
│  │  text_cleaner           │  │  (sentence-      (FAISS IndexFlat) │ │
│  │  chunker (semantic,     │  │   transformers)  retriever.py      │ │
│  │  overlap-aware)         │  │                  (top-k + ranking) │ │
│  └────────────────────────┘  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │  summarization/reasoning_engine.py                              │ │
│  │  HF transformer (flan-t5-base) — summarize, QA, explain,        │ │
│  │  compare, keywords, contributions, limitations, future work,    │ │
│  │  notes, quiz                                                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
└───────────────────────────────┬──────────────────────────────────---┘
                                 │
                    ┌────────────▼────────────┐
                    │   SQLite (metadata)      │
                    │   FAISS index (vectors)  │
                    │   /storage/uploads (PDFs)│
                    └──────────────────────────┘
```

### Data flow (ingestion)

```
PDF Upload
   │
   ▼
PyMuPDF extraction (text per page + title/author/year heuristics)
   │
   ▼
Text cleaning (de-hyphenation, whitespace normalization) + section tagging
   │
   ▼
Semantic chunking (sentence-aware, ~800 chars, 150-char overlap)
   │
   ▼
Sentence-Transformer embeddings (all-MiniLM-L6-v2, 384-dim, normalized)
   │
   ▼
FAISS IndexFlatIP  (append vectors, cosine similarity via inner product)
   │
   ▼
SQLite (Chunk rows store paper_id, section, page_number, text, vector_index)
```

### Data flow (chat / RAG query)

```
User question
   │
   ▼
Embed query (same Sentence-Transformer model)
   │
   ▼
FAISS top-k search  →  join to Chunk/Paper metadata in SQLite
   │
   ▼
Build bounded context window from retrieved chunks
   │
   ▼
flan-t5-base generates an answer conditioned on that context
   │
   ▼
Citations built from each retrieved chunk (paper, section, page, score)
   │
   ▼
Answer + citations returned to frontend, chat turn persisted
```

### Sequence diagram (chat request)

```
Frontend         FastAPI          ChatService       Retriever      VectorStore      ReasoningEngine     SQLite
   │  POST /api/chat  │                │                │               │                  │              │
   │─────────────────>│                │                │               │                  │              │
   │                  │──ask()────────>│                │               │                  │              │
   │                  │                │──retrieve()───>│               │                  │              │
   │                  │                │                │──search()────>│                  │              │
   │                  │                │                │<──indices,scores─                │              │
   │                  │                │                │──fetch Chunk rows───────────────────────────────>│
   │                  │                │                │<─────────────────────────────────────────────────│
   │                  │                │<──chunks───────│               │                  │              │
   │                  │                │──answer_question(context)──────────────────────────>│              │
   │                  │                │<──generated answer─────────────────────────────────│              │
   │                  │                │──persist ChatMessage rows───────────────────────────────────────>│
   │                  │<──ChatResponse─│                │               │                  │              │
   │<─────JSON────────│                │                │               │                  │              │
```

---

## 2. Folder Structure

```
research-assistant/
├── backend/
│   ├── api/                  # FastAPI routers (thin — validation + delegation only)
│   │   ├── routes_papers.py
│   │   ├── routes_chat.py
│   │   └── routes_analysis.py
│   ├── services/             # Orchestration / business logic
│   │   ├── paper_service.py      # ingestion pipeline
│   │   ├── chat_service.py       # RAG loop
│   │   └── analysis_service.py   # summarize/compare/etc.
│   ├── preprocessing/        # PDF → clean, section-tagged, chunked text
│   │   ├── pdf_extractor.py
│   │   ├── text_cleaner.py
│   │   └── chunker.py
│   ├── embeddings/
│   │   └── embedder.py       # Sentence-Transformers wrapper
│   ├── retrieval/
│   │   ├── vector_store.py   # FAISS index wrapper + persistence
│   │   └── retriever.py      # query embed → search → rank → join metadata
│   ├── summarization/
│   │   └── reasoning_engine.py  # HF transformer, task-specific prompts
│   ├── models/
│   │   ├── db_models.py      # SQLAlchemy ORM (Paper, Chunk, ChatMessage, Note)
│   │   └── schemas.py        # Pydantic request/response models
│   ├── database/
│   │   └── database.py       # SQLAlchemy engine/session/init
│   ├── utils/
│   │   ├── config.py         # centralized settings
│   │   └── citation.py       # citation-building
│   ├── storage/               # uploaded PDFs, FAISS index, sqlite file (gitignored)
│   ├── main.py                # FastAPI app + router registration
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/       # UploadZone, PaperCard, ChatPanel, ChatMessage,
    │   │                      # CitationMarker, AnalysisPanel, ComparePanel
    │   ├── services/
    │   │   └── api.js        # fetch wrapper for all backend endpoints
    │   └── App.jsx            # library sidebar + tabbed workspace
    ├── index.html
    ├── tailwind.config.js
    └── package.json
```

Each module has a single responsibility: `api/` never talks to the database or FAISS directly, `services/` never parses HTTP requests, `preprocessing/` and `embeddings/` are pure and reusable outside the web app entirely (e.g. from a script or notebook).

---

## 3. Database Schema

```
papers                         chunks                        chat_messages
─────────────────────           ─────────────────────         ─────────────────────
id (PK, uuid)                   id (PK, uuid)                 id (PK, uuid)
filename                        paper_id (FK → papers.id)     paper_id (FK, nullable)
title                           section                       role  (user | assistant)
authors                         page_number                   content
year                            text                           citations (JSON)
num_pages                       vector_index (→ FAISS row)     created_at
upload_date
status (processing|ready|failed)
reading_progress (0-100)

notes
─────────────────────
id (PK, uuid)
paper_id (FK → papers.id)
title
content
created_at
```

The FAISS index itself only stores raw vectors; `chunks.vector_index` is the join key back to relational metadata (paper, section, page), which is how every generated answer can cite its source precisely.

---

## 4. API Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/papers/upload` | Upload + fully ingest a PDF (extract, chunk, embed, index) |
| GET | `/api/papers` | List all papers |
| GET | `/api/papers/{id}` | Get one paper |
| DELETE | `/api/papers/{id}` | Delete a paper and its chunks |
| PATCH | `/api/papers/{id}/progress` | Update reading-progress percentage |
| POST | `/api/papers/notes` | Create a saved note |
| GET | `/api/papers/{id}/notes` | List notes for a paper |
| POST | `/api/chat` | Ask a question (RAG) — optionally scoped to one paper |
| GET | `/api/search` | Raw semantic search (no generation), returns ranked chunks |
| POST | `/api/analysis/summarize` | Summarize a paper (short/medium/long) |
| POST | `/api/analysis/compare` | Compare two papers |
| POST | `/api/analysis/explain` | Explain a pasted paragraph in plain English |
| GET | `/api/analysis/{id}/keywords` | Extract key terms |
| GET | `/api/analysis/{id}/contributions` | Extract key contributions |
| GET | `/api/analysis/{id}/limitations` | Extract limitations |
| GET | `/api/analysis/{id}/future-work` | Suggest future research directions |
| GET | `/api/analysis/{id}/notes-auto` | Generate structured reading notes |
| GET | `/api/analysis/{id}/quiz` | Generate quiz questions + answers |
| GET | `/api/analysis/{id}/related` | Recommend topically related uploaded papers |
| GET | `/api/health` | Health check |

Full interactive docs are auto-generated by FastAPI at `/docs` once the server is running.

---

## 5. Implementation Order

This is the order the system was actually built and validated in, and the order to follow if extending it:

1. `utils/config.py`, `database/database.py`, `models/db_models.py`, `models/schemas.py` — foundation
2. `preprocessing/` (extractor → cleaner → chunker) — validated independently with a synthetic PDF
3. `embeddings/embedder.py` — Sentence-Transformers wrapper
4. `retrieval/vector_store.py` + `retrieval/retriever.py` — FAISS + metadata join
5. `summarization/reasoning_engine.py` — the HF transformer reasoning layer
6. `services/` — orchestrate the above into ingestion, chat, and analysis pipelines
7. `api/` — thin FastAPI routers over the services
8. `main.py` — wire everything together, CORS, startup DB init
9. Frontend: `services/api.js` → components → `App.jsx`

---

## 6. Installation Guide

### Prerequisites
- Python 3.10+
- Node.js 18+
- ~3 GB free disk space (PyTorch + transformer model weights)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optional — defaults work out of the box
uvicorn main:app --reload --port 8000
```

The first request that triggers embedding or generation (upload, chat, summarize, etc.) will download the `all-MiniLM-L6-v2` and `flan-t5-base` model weights from Hugging Face on first use, then cache them locally — this only happens once.

Visit `http://localhost:8000/docs` to explore the API directly.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173`. The Vite dev server proxies `/api` requests to `http://localhost:8000` (see `vite.config.js`), so both servers need to be running.

---

## 6a. Running Tests

The `preprocessing/` module (PDF extraction, text cleaning, semantic chunking) has unit test coverage since it's the pure, deterministic core of the ingestion pipeline.

```bash
cd backend
pip install -r requirements.txt   # includes pytest
pytest tests/ -v
```

CI (`.github/workflows/ci.yml`) runs this same suite plus a byte-compile check on every push/PR, and separately verifies the frontend builds with `npm run build`.

---

## 7. Deployment Guide

### Backend (containerized)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Mount `storage/` as a persistent volume (or swap SQLite/FAISS for managed services — see below) so uploaded papers and the vector index survive restarts.

### Frontend

```bash
cd frontend
npm run build        # outputs static files to dist/
```

Serve `dist/` from any static host (Nginx, Vercel, Netlify, S3+CloudFront) and set the API base URL (`src/services/api.js`) to your deployed backend's public URL, or reverse-proxy `/api` to the backend service the same way `vite.config.js` does in dev.

### Scaling beyond a single machine

- Swap `IndexFlatIP` for a FAISS `IndexIVFFlat`/HNSW index, or move to a managed vector DB (pgvector, Pinecone, Qdrant) once the corpus grows past a few thousand chunks.
- Swap SQLite for PostgreSQL (the SQLAlchemy layer makes this a connection-string change).
- Run the reasoning model behind a dedicated inference service (e.g. a GPU worker or a hosted LLM API) if generation latency becomes a bottleneck — `reasoning_engine.py` is the single seam to change.
- Move PDF ingestion to a background task queue (Celery/RQ) instead of synchronous request handling for large batch uploads.

---

## 8. Feature Checklist

| Feature | Status |
|---|---|
| PDF upload (single/multi) with metadata extraction | ✅ |
| Semantic chunking with overlap | ✅ |
| Sentence-Transformer embeddings + FAISS retrieval | ✅ |
| Chat with uploaded papers (RAG) | ✅ |
| Semantic search endpoint | ✅ |
| Paper summarization (short/medium/long) | ✅ |
| Compare two papers | ✅ |
| Explain a paragraph in plain English | ✅ |
| Extract key contributions / limitations / keywords | ✅ |
| Suggest future research directions | ✅ |
| Generate reading notes | ✅ |
| Generate quiz questions | ✅ |
| Recommend related uploaded papers | ✅ |
| Citations (paper, section, page, similarity score) | ✅ |
| Reading-progress tracking | ✅ |
| Saved notes | ✅ |
| User authentication | ⬜ not implemented — see note below |
| Export summaries as PDF | ⬜ not implemented |
| Dark mode / dashboard analytics | ⬜ not implemented |

The unchecked items are genuinely "extra" (the prompt itself listed them as optional stretch goals) and were left out to keep the core RAG system's code quality high rather than spreading thin. They're straightforward additions on top of this architecture:
- **Auth**: add a `users` table + JWT middleware in FastAPI; scope `Paper` rows by `user_id`.
- **Export as PDF**: reuse `reasoning_engine` output + a library like `reportlab` or `weasyprint`.
- **Dark mode**: the Tailwind config already uses `darkMode: "class"`; add a toggle that flips a class on `<html>`.

---

## 9. Design Notes

- **Why one general-purpose reasoning model (flan-t5-base) instead of five specialized ones?** It keeps the "AI reasoning layer" cohesive, the dependency footprint small, and CPU-inference feasible for an internship-scale demo — while still cleanly demonstrating prompt design across many NLP tasks. `reasoning_engine.py` is intentionally the single seam to swap in specialized models (e.g. a dedicated extractive-QA model, or a larger instruction-tuned LLM) later.
- **Why FAISS `IndexFlatIP` instead of an approximate index?** Exact search is simplest to reason about and fast enough for the thousands-of-chunks scale a research-assistant demo will see; the README above documents the upgrade path.
- **Why is the ingestion pipeline synchronous?** Simplicity for a submission-scale project. `services/paper_service.py` is the one place to swap in a background task queue if upload volume grows.

---

## 10. License

MIT — see [LICENSE](LICENSE).
