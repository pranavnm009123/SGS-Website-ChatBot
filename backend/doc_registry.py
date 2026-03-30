import json
import os
from datetime import datetime
import uuid

REGISTRY_FILE = os.path.join(os.path.dirname(__file__), "approved_docs.json")

def get_docs():
    if not os.path.exists(REGISTRY_FILE):
        return []
    with open(REGISTRY_FILE, "r") as f:
        return json.load(f)

def save_docs(docs):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(docs, f, indent=2)

def add_doc(filename, filepath, page_count):
    docs = get_docs()
    new_doc = {
        "doc_id": str(uuid.uuid4()),
        "filename": filename,
        "filepath": filepath,
        "status": "pending",
        "page_count": page_count,
        "chunk_count": 0,
        "uploaded_at": datetime.now().isoformat()
    }
    docs.append(new_doc)
    save_docs(docs)
    return new_doc

def update_doc_status(doc_id, status, chunk_count=None):
    docs = get_docs()
    for doc in docs:
        if doc["doc_id"] == doc_id:
            doc["status"] = status
            if chunk_count is not None:
                doc["chunk_count"] = chunk_count
            break
    save_docs(docs)

def delete_doc(doc_id):
    docs = get_docs()
    docs = [doc for doc in docs if doc["doc_id"] != doc_id]
    save_docs(docs)

def get_doc_by_id(doc_id):
    docs = get_docs()
    for doc in docs:
        if doc["doc_id"] == doc_id:
            return doc
    return None

def get_approved_doc_ids():
    return [doc["doc_id"] for doc in get_docs() if doc["status"] == "approved"]
