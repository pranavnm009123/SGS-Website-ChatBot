import chromadb
import logging
import os
import threading

log = logging.getLogger(__name__)

_DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")
_MARKER_FILE = os.path.join(_DB_DIR, ".embedding_model")


class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Database, cls).__new__(cls)
                    os.makedirs(_DB_DIR, exist_ok=True)
                    cls._instance.client = chromadb.PersistentClient(path=_DB_DIR)
                    cls._instance.collection = cls._instance.client.get_or_create_collection(
                        name="approved_docs",
                        metadata={"hnsw:space": "cosine"}
                    )
        return cls._instance


def get_db():
    return Database()


def check_and_migrate(current_model: str) -> bool:
    """Check if the embedding model has changed. If so, clear the collection and return True.

    Returns True if a reset was performed (caller should re-index all content).
    Returns False if the model is unchanged (normal startup, no reset needed).
    """
    os.makedirs(_DB_DIR, exist_ok=True)

    if os.path.exists(_MARKER_FILE):
        with open(_MARKER_FILE) as f:
            stored = f.read().strip()
        if stored == current_model:
            return False  # model unchanged, nothing to do

    # Model changed or first run — wipe the collection so old incompatible vectors are gone
    db = get_db()
    try:
        db.client.delete_collection("approved_docs")
    except Exception:
        pass  # collection may not exist on first run

    db.collection = db.client.get_or_create_collection(
        name="approved_docs",
        metadata={"hnsw:space": "cosine"}
    )
    # Also update the singleton so future callers see the new collection
    Database._instance.collection = db.collection

    with open(_MARKER_FILE, "w") as f:
        f.write(current_model)

    log.info("ChromaDB reset: embedding model is now '%s'", current_model)
    return True
