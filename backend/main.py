import asyncio
import logging
import os
from contextlib import asynccontextmanager

import requests
from fastapi import FastAPI, UploadFile, File, Header, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, StreamingResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.responses import Response as StarletteResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler

from doc_registry import get_docs, add_doc, update_doc_status, delete_doc, get_doc_by_id
from ingestion import ingest_document
from retrieval import answer_question, answer_question_stream
from security import limiter, sanitize_input, validate_admin, validate_file
from db import get_db, check_and_migrate, Database
from embeddings import EMBEDDING_MODEL
from site_indexer import index_site_pages, start_site_watcher

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
OLLAMA_URL = "http://localhost:11434"


def _check_ollama():
    try:
        r = requests.get(OLLAMA_URL, timeout=5)
        r.raise_for_status()
        log.info("Ollama is reachable")
    except Exception:
        log.warning("Ollama is not reachable at %s — chat will fail until it's started", OLLAMA_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    _check_ollama()

    # Detect embedding model change; reset ChromaDB collection if needed
    was_reset = await asyncio.to_thread(check_and_migrate, EMBEDDING_MODEL)

    # Always re-index website pages (idempotent; also required after a DB reset)
    await asyncio.to_thread(index_site_pages, FRONTEND_DIR)

    # After a DB reset, automatically re-ingest all previously approved PDFs
    if was_reset:
        for doc in get_docs():
            if doc["status"] == "approved" and os.path.exists(doc["filepath"]):
                log.info("Re-ingesting '%s' after DB reset", doc["filename"])
                asyncio.create_task(
                    asyncio.to_thread(ingest_document, doc["doc_id"], doc["filepath"], doc["filename"])
                )

    # Start background file watcher — auto re-indexes any HTML page that changes
    observer = start_site_watcher(FRONTEND_DIR)

    yield

    observer.stop()
    observer.join()


app = FastAPI(
    title="SGS Technologies API",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, *args, **kwargs) -> StarletteResponse:
        resp = await super().get_response(*args, **kwargs)
        resp.headers["Cache-Control"] = "no-cache, must-revalidate"
        return resp

app.mount("/static", NoCacheStaticFiles(directory=FRONTEND_DIR), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)


# ── Pydantic models ─────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    question: str

class ContactRequest(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    subject: str = ""
    message: str


# ── Page routes ──────────────────────────────────────────────────────────────

@app.get("/")
async def read_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/about")
async def read_about():
    return FileResponse(os.path.join(FRONTEND_DIR, "about.html"))

@app.get("/services")
async def read_services():
    return FileResponse(os.path.join(FRONTEND_DIR, "services.html"))

@app.get("/contact")
async def read_contact():
    return FileResponse(os.path.join(FRONTEND_DIR, "contact.html"))

@app.get("/admin")
async def read_admin():
    return FileResponse(os.path.join(FRONTEND_DIR, "admin.html"))


# ── Contact form ─────────────────────────────────────────────────────────────

@app.post("/submit-contact")
@limiter.limit("5/minute")
async def submit_contact(request: Request, body: ContactRequest):
    log.info(
        "Contact form submission from %s %s <%s> — subject: %s",
        body.first_name, body.last_name, body.email, body.subject,
    )
    # In production, send an email or store in a database here.
    return {"status": "ok", "message": "Message received. We'll get back to you within one business day."}


# ── PDF serving ──────────────────────────────────────────────────────────────

@app.get("/pdf/{filename}")
async def serve_pdf(filename: str):
    safe_filename = os.path.basename(filename)  # prevent path traversal
    filepath = os.path.join(UPLOAD_DIR, safe_filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="PDF not found")
    return FileResponse(filepath, media_type="application/pdf", headers={
        "Content-Disposition": f'inline; filename="{safe_filename}"'
    })


# ── Document management ─────────────────────────────────────────────────────

@app.post("/upload")
@limiter.limit("10/minute")
async def upload_pdf(request: Request, file: UploadFile = File(...)):
    content = await file.read()
    file_size = len(content)
    validate_file(file.filename, file.content_type, file_size)

    safe_filename = os.path.basename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, safe_filename)
    with open(filepath, "wb") as f:
        f.write(content)

    import fitz
    doc = fitz.open(filepath)
    page_count = len(doc)
    doc.close()

    doc_info = add_doc(safe_filename, filepath, page_count)
    return doc_info

@app.get("/documents")
async def list_docs():
    return get_docs()

@app.post("/documents/{doc_id}/approve")
async def approve_doc(doc_id: str, background_tasks: BackgroundTasks, x_admin_key: str = Header(None)):
    validate_admin(x_admin_key)
    doc = get_doc_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    update_doc_status(doc_id, "processing")
    background_tasks.add_task(ingestion_wrapper, doc_id, doc["filepath"], doc["filename"])
    return {"doc_id": doc_id, "status": "processing"}

async def ingestion_wrapper(doc_id, filepath, filename):
    await asyncio.to_thread(ingest_document, doc_id, filepath, filename)

@app.post("/documents/{doc_id}/reject")
async def reject_doc(doc_id: str, x_admin_key: str = Header(None)):
    validate_admin(x_admin_key)
    doc = get_doc_by_id(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc["filepath"]):
        os.remove(doc["filepath"])

    if doc["status"] == "approved":
        db = get_db()
        db.collection.delete(where={"doc_id": doc_id})

    update_doc_status(doc_id, "rejected")
    return {"doc_id": doc_id, "status": "rejected"}

@app.delete("/documents/{doc_id}")
async def remove_doc(doc_id: str, x_admin_key: str = Header(None)):
    validate_admin(x_admin_key)
    doc = get_doc_by_id(doc_id)
    if doc:
        if os.path.exists(doc["filepath"]):
            os.remove(doc["filepath"])
        db = get_db()
        db.collection.delete(where={"doc_id": doc_id})
        delete_doc(doc_id)
    return {"status": "success"}


# ── Database purge ───────────────────────────────────────────────────────────

@app.post("/purge-database")
async def purge_database(x_admin_key: str = Header(None)):
    """Wipe all PDF documents from ChromaDB and clear the uploads directory."""
    validate_admin(x_admin_key)
    db = get_db()

    # Delete all PDF vectors (keep site vectors)
    for doc in get_docs():
        try:
            db.collection.delete(where={"doc_id": doc["doc_id"]})
        except Exception:
            pass
        if os.path.exists(doc["filepath"]):
            os.remove(doc["filepath"])

    # Reset registry
    from doc_registry import save_docs
    save_docs([])

    # Clean uploads dir
    for f in os.listdir(UPLOAD_DIR):
        fp = os.path.join(UPLOAD_DIR, f)
        if os.path.isfile(fp):
            os.remove(fp)

    log.info("Database purged: all PDF documents removed")
    return {"status": "ok", "message": "All PDF documents and vectors have been purged."}


# ── Full database purge ─────────────────────────────────────────────────────

@app.post("/purge-all")
async def purge_all(x_admin_key: str = Header(None)):
    """Wipe EVERYTHING from ChromaDB (PDFs + website vectors) and clear uploads."""
    validate_admin(x_admin_key)
    db = get_db()

    # Drop and recreate the entire collection
    try:
        db.client.delete_collection("approved_docs")
    except Exception:
        pass
    db.collection = db.client.get_or_create_collection(
        name="approved_docs",
        metadata={"hnsw:space": "cosine"}
    )
    Database._instance.collection = db.collection

    # Clear document registry
    from doc_registry import save_docs
    save_docs([])

    # Clean uploads dir
    for f in os.listdir(UPLOAD_DIR):
        fp = os.path.join(UPLOAD_DIR, f)
        if os.path.isfile(fp):
            os.remove(fp)

    log.info("Full database purge: all vectors, PDFs, and site index removed")
    return {"status": "ok", "message": "Entire database wiped — PDFs and website vectors removed."}


# ── Site re-index ────────────────────────────────────────────────────────────

@app.post("/reindex-site")
async def reindex_site(x_admin_key: str = Header(None)):
    validate_admin(x_admin_key)
    await asyncio.to_thread(index_site_pages, FRONTEND_DIR)
    return {"status": "ok", "message": "Website pages re-indexed"}


# ── Chat ─────────────────────────────────────────────────────────────────────

@app.post("/chat")
@limiter.limit("10/minute")
async def chat(request: Request, chat_req: ChatRequest):
    question = sanitize_input(chat_req.question)
    result = answer_question(question)
    return result


@app.post("/chat/stream")
@limiter.limit("10/minute")
async def chat_stream(request: Request, chat_req: ChatRequest):
    question = sanitize_input(chat_req.question)
    return StreamingResponse(
        answer_question_stream(question),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
