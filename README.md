# SGS policy chatbot

Static marketing site plus a chatbot that answers from your own content: the HTML pages in `frontend/` and PDFs you add through `/admin`. Built for **local** use — FastAPI serves the site, Chroma stores embeddings, Ollama runs **`qwen3:8b`** by default.

The widget talks to the backend; answers come back with **source cards** so you can see what chunk they came from. There’s a non-streaming `POST /chat` and a streaming `POST /chat/stream`.

## How it fits together

Visitors use the site and chat. Admins use `/admin` to upload PDFs and approve them. On startup the app re-indexes the listed HTML files into Chroma, checks Ollama, and starts a file watcher so when you save an HTML file it gets re-embedded. Approved PDFs get chunked and embedded when you approve them. When someone asks a question, the backend embeds the query, pulls relevant chunks, filters and dedupes a bit, then sends context + question to Ollama.

No React build step — just HTML, CSS, and JS.

## What you need

- Python **3.9+**
- **[Ollama](https://ollama.com)** on your PATH  
- First run will download deps, the embedding model **`BAAI/bge-large-en-v1.5`**, and pull **`qwen3:8b`** — can take a while.

## Run it

From this folder (`policy-chatbot/`):

```bash
bash run.sh
```

That creates `venv` if needed, installs `backend/requirements.txt`, tries to start `ollama serve` if nothing’s running, pulls the model, then runs Uvicorn on **port 8000**. Use `chmod +x run.sh` if you want `./run.sh`.

**Manual option:** activate a venv, `pip install -r backend/requirements.txt`, run `ollama serve` in one terminal, then:

```bash
ollama pull qwen3:8b
cd backend && python3 -m uvicorn main:app --reload --port 8000
```

On Windows, use Git Bash/WSL for `run.sh` or mirror the same steps in PowerShell.

## URLs

Main pages: `/`, `/about`, `/services`, `/contact`, `/careers`, `/products`, `/testimonials`, `/software-engineering`, `/cloud-services`, `/cyber-security`, `/data-engineering`.

**`/admin`** — upload / approve PDFs, reindex, purge.  
**`/api/docs`** and **`/api/redoc`** — API reference.

## What gets indexed for the bot

These HTML files are what the chatbot searches for “website” answers (not `admin.html`):

`index.html`, `about.html`, `services.html`, `contact.html`, `careers.html`, `products.html`, `testimonials.html`, `software-engineering.html`, `cloud-services.html`, `cyber-security.html`, `data-engineering.html`.

## PDFs and admin key

1. Open `/admin`.  
2. Upload PDFs, then **Approve** the ones you want in the index.  
3. Until they’re approved, the bot won’t use them.

Admin requests need header **`X-Admin-Key`**. Default matches **`backend/security.py`** — usually `localdev123` unless you set **`ADMIN_KEY`**. Keep **`frontend/admin.js`** in sync if you change it.

Registry file: **`backend/approved_docs.json`**. Rough flow: `pending` → `processing` → `approved` (or `rejected` / `error`).

**Danger buttons (same key):**  
`POST /reindex-site` — rebuild site chunks from HTML.  
`POST /purge-database` — wipe PDF vectors + uploads; **keeps** site index.  
`POST /purge-all` — wipes **everything** in the collection + uploads; you’ll need to reindex and re-approve PDFs.

## Chat behavior (short)

- Rate limit on chat: **10/minute** (and uploads/contact have their own limits — see `security.py`).
- Questions are trimmed and checked for obvious junk patterns.
- Only **approved** PDFs join retrieval; site chunks are always in play for the pages above.
- If grounding is weak, you may get the canned “contact us” style fallback.

## Check it’s up

```bash
source venv/bin/activate
python verify_backend.py
```

Hits `/api/docs` and a few main routes.

## The question set (`sgs_qa_evaluation.txt`)

There’s a file of **30 hand-written Q&As** used to sanity-check the bot against real SGS policy PDFs and the live website copy. They’re grouped into five blocks of five: single-PDF questions, cross-document PDF questions, website-only questions, hybrid (site + PDF), and a last mix that stresses retrieval across sources. Each line has a difficulty tag (easy / medium / hard) and a golden answer plus where it should have come from (PDF section or HTML page).

It’s basically a gold set — useful when you’re tuning retrieval or comparing answers, not something you have to run to use the app day to day.

## Env vars worth knowing

- **`ADMIN_KEY`** — admin auth (default `localdev123`).
- **`OLLAMA_URL`** — default `http://localhost:11434/api/chat`.
- **`OLLAMA_MODEL`** — default `qwen3:8b`.
- **`OLLAMA_TIMEOUT_SECONDS`** / **`OLLAMA_STREAM_TIMEOUT_SECONDS`** — request timeouts.
- **`RETRIEVAL_*`** — thresholds and chunk caps in `retrieval.py` if you’re tuning search.

If you change the embedding model in **`embeddings.py`**, the app can reset Chroma, reindex the site, and re-ingest approved PDFs.

## Where files land

- **`backend/chroma_db/`** — vector DB  
- **`backend/uploads/`** — PDFs on disk  
- **`backend/approved_docs.json`** — doc list + status  
- **`backend/.embedding_model`** — tracks embedding model for migrations  

These are local/runtime stuff; they’re gitignored.

## Folder map

- **`backend/`** — `main.py` (app), `retrieval.py`, `ingestion.py`, `site_indexer.py`, `db.py`, `doc_registry.py`, `security.py`, `embeddings.py`, `requirements.txt`
- **`frontend/`** — pages, `widget.js`, `admin.js`, `style.css`, `theme.js`
- **`run.sh`**, **`verify_backend.py`**, **`sgs_qa_evaluation.txt`** (Q&A gold set), **`ppt_generation_brief.txt`**

## When something breaks

- **Chat errors** — Is Ollama up? Try `http://localhost:11434`.
- **First answer takes forever** — cold start / model load is normal.
- **PDFs ignored** — Did you **approve** them in `/admin`?
- **Stale website answers** — Wait for startup index or call `POST /reindex-site` after editing HTML.
- **Only HTML text is indexed** — changing CSS/JS alone won’t change what the bot “reads.”
- **403 on admin** — Wrong `X-Admin-Key`.
- **Port 8000 busy** — Kill the other process or pick another port for Uvicorn.

Dev tip: Uvicorn `--reload` picks up Python changes; saving a tracked `.html` file triggers a reindex via the watcher.
