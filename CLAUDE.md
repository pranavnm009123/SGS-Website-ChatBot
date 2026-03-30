# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Server

```bash
# Full startup (creates venv, installs deps, starts Ollama, runs server)
cd policy-chatbot
bash run.sh

# If venv already exists and deps are installed:
cd policy-chatbot
source venv/bin/activate
cd backend
python3 -m uvicorn main:app --reload --port 8000
```

The server runs at `http://localhost:8000`. Uvicorn watches only the `backend/` directory for reloads — frontend changes are served immediately without restart.

**Kill a stuck server:** `lsof -ti :8000 | xargs kill -9`

## Architecture

**Stack:** FastAPI backend + vanilla HTML/CSS/JS frontend + ChromaDB (local vector DB) + Ollama (local LLM, `llama3.1` model = LLaMA 3.1 8B) + SentenceTransformers (`BAAI/bge-large-en-v1.5` for embeddings, 1024 dims).

**Two content sources feed the chatbot:**
1. **PDFs** — uploaded via `/upload`, approved by admin, ingested into ChromaDB via `ingestion.py`
2. **Website pages** — the 4 HTML pages (Home, About, Services, Contact) are indexed into ChromaDB on startup via `site_indexer.py`

Both sources are disambiguated by `source_type` metadata (`"pdf"` or `"website"`) stored in ChromaDB. `retrieval.py` queries both and returns typed source citations.

**Request flow:**
```
POST /chat        → retrieval.py → embed question → query ChromaDB → Ollama → return {answer, sources}
POST /chat/stream → same retrieval → Ollama (stream: true) → SSE events (token chunks + sources)
```
The widget uses `/chat/stream` by default for real-time token streaming.

**Document approval workflow:**
```
POST /upload → add_doc() [registry] → POST /documents/{id}/approve
             → ingest_document() [background] → ChromaDB
```

**Key backend files:**
- `main.py` — all routes; uses `lifespan` context manager for startup (Ollama check + site indexing)
- `embeddings.py` — shared lazy-loaded `SentenceTransformer` singleton (used by ingestion, retrieval, and site_indexer)
- `ingestion.py` — PDF → chunks → embeddings → ChromaDB (metadata: `source_type: "pdf"`)
- `site_indexer.py` — HTML pages → stripped text → chunks → ChromaDB (metadata: `source_type: "website"`, fixed `doc_id`s: `site_home`, `site_about`, `site_services`, `site_contact`). Also exports `start_site_watcher()` (watchdog-based auto re-index on HTML file changes) and `index_one_page()` (per-page re-index used by the watcher).
- `retrieval.py` — combines approved PDF doc_ids + site doc_ids for ChromaDB `$in` filter
- `doc_registry.py` — JSON-backed registry at `backend/approved_docs.json`; tracks PDF status (`pending → processing → approved`)
- `db.py` — thread-safe ChromaDB singleton, collection `"approved_docs"`, cosine similarity, persisted at `backend/chroma_db/`. Also exports `check_and_migrate(model_name)` — called on startup to detect embedding model changes; resets the collection and returns `True` if a reset was done (triggers automatic PDF re-ingestion in `main.py`).
- `security.py` — admin key (timing-safe comparison), rate limiting, input sanitization, file validation

**Frontend:**
- All pages share `style.css` + `widget.js` (floating chat, bottom-right)
- `widget.js` — self-contained IIFE; chat history in `sessionStorage`, open/closed state in `localStorage`
- Admin panel at `/admin` (no widget); uses `X-Admin-Key: localdev123` header
- Static files served from `frontend/` at `/static/*`

## Auth & Security

- Admin key: `ADMIN_KEY` env var, default `localdev123`
- Rate limit: 10/min on `/chat` and `/upload`, 5/min on `/submit-contact` (slowapi)
- Input sanitized in `security.py` (jailbreak phrase blocking, 500-char truncation)
- File validation: PDF only, max 50 MB

## PDF Document Lifecycle (curl reference)

```bash
ADMIN="X-Admin-Key: localdev123"

# Upload a PDF (returns doc_id)
curl -X POST http://localhost:8000/upload -F "file=@yourfile.pdf"

# List all documents + statuses
curl http://localhost:8000/documents

# Approve → triggers background ingestion into ChromaDB
curl -X POST http://localhost:8000/documents/{doc_id}/approve -H "$ADMIN"

# Reject → deletes file, removes from ChromaDB if already approved
curl -X POST http://localhost:8000/documents/{doc_id}/reject -H "$ADMIN"

# Delete → removes file, vectors, and registry entry entirely
curl -X DELETE http://localhost:8000/documents/{doc_id} -H "$ADMIN"
```

**Status flow:** `pending → processing → approved` (or `rejected` / `error`)
PDFs are stored in `backend/uploads/`. The registry (`backend/approved_docs.json`) is the source of truth for which doc_ids get included in ChromaDB queries. Deleting a doc via the API removes both the file and its vectors from ChromaDB.

## Re-indexing Website Content

Website pages are **automatically re-indexed** when any HTML file in `frontend/` is saved — the watchdog background thread detects the change and re-indexes just that page within ~1 second. No manual action needed.

Manual re-index is still available via the Admin panel ("↺ Re-index Website" button) or:
```bash
curl -X POST http://localhost:8000/reindex-site -H "X-Admin-Key: localdev123"
```

Site pages use fixed `doc_id`s (`site_home`, `site_about`, `site_services`, `site_contact`) — re-indexing deletes old vectors and re-adds them, so it's always idempotent.

## Embedding Model & DB Migration

The active embedding model is stored in `backend/chroma_db/.embedding_model`. On startup, if this marker is missing or the model name doesn't match `EMBEDDING_MODEL` in `embeddings.py`, the ChromaDB collection is wiped and all content is re-indexed from scratch (site pages immediately, approved PDFs in background tasks). This migration is automatic — just restart the server after changing `EMBEDDING_MODEL`.
@