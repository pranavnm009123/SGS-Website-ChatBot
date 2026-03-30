import html.parser
import logging
import os
import threading

from langchain.text_splitter import RecursiveCharacterTextSplitter
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from db import get_db
from embeddings import get_model

log = logging.getLogger(__name__)

SITE_PAGES = [
    {"name": "Home",     "url": "/",          "file": "index.html",    "doc_id": "site_home"},
    {"name": "About",    "url": "/about",     "file": "about.html",    "doc_id": "site_about"},
    {"name": "Services", "url": "/services",  "file": "services.html", "doc_id": "site_services"},
    {"name": "Contact",  "url": "/contact",   "file": "contact.html",  "doc_id": "site_contact"},
]

_FILE_TO_PAGE = {p["file"]: p for p in SITE_PAGES}


class _TextExtractor(html.parser.HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript"}

    def __init__(self):
        super().__init__()
        self._skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP_TAGS:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in self.SKIP_TAGS and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            stripped = data.strip()
            if stripped:
                self.parts.append(stripped)

    def get_text(self):
        return " ".join(self.parts)


def _extract_text(html_content: str) -> str:
    parser = _TextExtractor()
    parser.feed(html_content)
    return parser.get_text()


def index_one_page(frontend_dir: str, page: dict):
    """Extract text from a single HTML page and upsert its chunks into ChromaDB."""
    db = get_db()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    filepath = os.path.join(frontend_dir, page["file"])
    if not os.path.exists(filepath):
        log.warning("Skipping %s — not found", page["file"])
        return

    with open(filepath, "r", encoding="utf-8") as f:
        html_content = f.read()

    text = _extract_text(html_content)
    chunks = splitter.split_text(text)
    if not chunks:
        return

    # Remove old vectors for this page (idempotent)
    try:
        db.collection.delete(where={"doc_id": page["doc_id"]})
    except Exception:
        pass

    embeddings = get_model().encode(chunks).tolist()
    metadatas = [
        {
            "doc_id": page["doc_id"],
            "source_type": "website",
            "page_name": page["name"],
            "url": page["url"],
        }
        for _ in chunks
    ]
    ids = [f"{page['doc_id']}_{i}" for i in range(len(chunks))]

    db.collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )
    log.info("Indexed %s: %d chunks", page["name"], len(chunks))


def index_site_pages(frontend_dir: str):
    """Index all site pages. Called on startup and manual re-index."""
    for page in SITE_PAGES:
        index_one_page(frontend_dir, page)


# ── File watcher ─────────────────────────────────────────────────────────────

class _HtmlChangeHandler(FileSystemEventHandler):
    """Watches frontend/ for HTML changes and re-indexes affected pages automatically."""

    def __init__(self, frontend_dir: str):
        self._frontend_dir = frontend_dir
        self._timers: dict[str, threading.Timer] = {}

    def on_modified(self, event):
        if event.is_directory:
            return
        filename = os.path.basename(event.src_path)
        if not filename.endswith(".html") or filename not in _FILE_TO_PAGE:
            return

        # Debounce: if the file is saved multiple times in quick succession (e.g.
        # editor autosave), only re-index once after the last write settles.
        if filename in self._timers:
            self._timers[filename].cancel()

        page = _FILE_TO_PAGE[filename]
        t = threading.Timer(1.0, index_one_page, args=[self._frontend_dir, page])
        self._timers[filename] = t
        t.start()
        log.info("Change detected in %s — re-indexing in 1 s", filename)


def start_site_watcher(frontend_dir: str) -> Observer:
    """Start a background watchdog observer. Returns the observer so the caller can stop it."""
    observer = Observer()
    observer.schedule(_HtmlChangeHandler(frontend_dir), frontend_dir, recursive=False)
    observer.start()
    log.info("Auto re-index watcher started on %s", frontend_dir)
    return observer
