# SGS Technologies — Policy chatbot and site

A small static marketing site plus a RAG chatbot. The bot uses **FastAPI**, **ChromaDB**, and **Ollama** on your machine. Answers are built from:

- HTML under `frontend/` (indexed on startup and when files change)
- PDFs you upload via the admin UI after you approve them (`backend/uploads/`)

Responses stream to the page and show source cards under each reply.

---

## Prerequisites

1. **Python 3.9+**
2. **[Ollama](https://ollama.com)** installed and on your `PATH` (so `ollama` works in a terminal)
3. **Network** the first time you run — it downloads the embedding model and the `qwen3:8b` Ollama model

---

## Run the app

All commands assume your current directory is **`policy-chatbot/`** (the folder that contains `run.sh`, `backend/`, and `frontend/`).

### Easiest: startup script

```bash
bash run.sh
```

If you prefer `./run.sh`, make it executable once: `chmod +x run.sh`.

**Windows:** `run.sh` is a bash script. Use **Git Bash**, **WSL**, or skip to [Manual start](#manual-start) and run the same steps in PowerShell where applicable (`python`, `pip`, `ollama` in PATH).

The script will:

1. Create `venv/` if it does not exist  
2. `pip install -r backend/requirements.txt`  
3. Start `ollama serve` in the background if no `ollama` process is running  
4. `ollama pull qwen3:8b`  
5. Start the API with **Uvicorn on port 8000** (from `backend/`)

When the server is up, open:

| URL | What |
|-----|------|
| [http://localhost:8000/](http://localhost:8000/) | Site home |
| [http://localhost:8000/about](http://localhost:8000/about) | About |
| [http://localhost:8000/services](http://localhost:8000/services) | Services |
| [http://localhost:8000/contact](http://localhost:8000/contact) | Contact |
| [http://localhost:8000/admin](http://localhost:8000/admin) | PDF upload / approve / indexing |
| [http://localhost:8000/api/docs](http://localhost:8000/api/docs) | OpenAPI (Swagger) |

**Stop:** Press **Ctrl+C** in the terminal where Uvicorn is running. If the script started Ollama in the background, stop it separately (e.g. quit the Ollama app or kill the `ollama` process) if you do not want it left running.

### Manual start

Use this if you are not using `run.sh` or you want full control.

1. Start Ollama yourself (`ollama serve` in another terminal, or the desktop app). Chat will not work until Ollama is up at `http://localhost:11434`.
2. From **`policy-chatbot/`**:

```bash
python3 -m venv venv
source venv/bin/activate   # Windows (cmd): venv\Scripts\activate.bat
pip install -r backend/requirements.txt
ollama pull qwen3:8b
cd backend
python3 -m uvicorn main:app --reload --port 8000
```

---

## Check that it is running

With the server still up, in **another** terminal from **`policy-chatbot/`**:

```bash
source venv/bin/activate
python verify_backend.py
```

(`requests` is already listed in `backend/requirements.txt`.)

---

## Admin: PDFs and API key

1. Open `/admin`.
2. Upload PDFs, then **Approve** each one you want in the index.
3. Wait until status is `approved`, then ask the bot; retrieval uses approved files only.

**API key:** Admin routes expect header **`X-Admin-Key`**. Default is `localdev123` in `backend/security.py` — keep the same value in `frontend/admin.js` if you change it.

**Document flow:** `pending` → `processing` → `approved` (see `backend/doc_registry.py`). Reject removes the file and sets `rejected`.

**Dangerous admin actions (require the same key):**

- `POST /reindex-site` — rebuild website chunk index from `frontend/` HTML  
- `POST /purge-database` — drop PDF vectors and uploads; website vectors stay  
- `POST /purge-all` — wipe the Chroma collection and uploads  

After a full purge, trigger a site re-index and re-approve PDFs as needed.

---

## Where data lives

| Path | Contents |
|------|----------|
| `backend/chroma_db/` | Vector store |
| `backend/uploads/` | Uploaded PDFs |

First startup can take a while (embedding model `BAAI/bge-large-en-v1.5` and Ollama pull).

---

## Chat behavior (sources)

- Sources are cards under the assistant message (not inline `[1]` citations).
- They come from the same chunks passed into the model; filtering is in `backend/retrieval.py`.

---

## Stack (reference)

- Backend: FastAPI, Uvicorn  
- Frontend: static HTML/CSS/JS (`widget.js`, `admin.js`)  
- Vectors: ChromaDB (local persistence)  
- Embeddings: SentenceTransformers — `BAAI/bge-large-en-v1.5`  
- LLM: Ollama — `qwen3:8b`  
- PDFs: PyMuPDF (`fitz`), pdfplumber  

---

## Project layout

```text
policy-chatbot/
  backend/
    main.py            # App, routes, static files
    retrieval.py       # RAG + Ollama
    ingestion.py       # PDF ingest
    site_indexer.py    # HTML index + file watcher
    db.py              # Chroma + embedding migration
    doc_registry.py    # Upload / approval state
    security.py        # Sanitization, admin auth, rate limits
    embeddings.py      # Embedding model id
    requirements.txt
  frontend/
    *.html, widget.js, admin.js, style.css
  run.sh
  verify_backend.py
```

---

## Troubleshooting

| Problem | What to try |
|---------|-------------|
| Ollama errors | Confirm something is listening on `http://localhost:11434` and `ollama serve` (or the app) is running. |
| Vague or empty answers | Let startup finish (site index runs on boot). For PDFs, they must be **approved**. |
| 401/403 on admin | `X-Admin-Key` must match `backend/security.py` (and `admin.js`). |
| Port 8000 in use | Stop the other process or run Uvicorn on another port. |
| First reply very slow | Normal while models load and warm up. |

Rate limits apply to chat, upload, and contact endpoints (`backend/security.py`).
