import hmac
import os
from typing import Optional

from fastapi import HTTPException, Header
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

ADMIN_KEY = os.environ.get("ADMIN_KEY", "localdev123")

BLOCK_PHRASES = [
    "ignore previous", "forget instructions", "system:", "you are now",
    "jailbreak", "ignore above", "disregard previous", "override prompt",
    "new instructions", "act as if", "pretend you are",
]

def sanitize_input(text: str) -> str:
    text = text.strip()[:500]
    lower_text = text.lower()
    for phrase in BLOCK_PHRASES:
        if phrase in lower_text:
            raise HTTPException(status_code=400, detail="Invalid input.")
    return text

def validate_admin(x_admin_key: str = Header(None)):
    if x_admin_key is None or not hmac.compare_digest(x_admin_key, ADMIN_KEY):
        raise HTTPException(status_code=403, detail="Forbidden: Invalid Admin Key")

def validate_file(filename: str, content_type: str, file_size: int, content: Optional[bytes] = None):
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    if file_size > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="File size exceeds 50MB limit.")

    allowed_types = {
        None,
        "",
        "application/pdf",
        "application/x-pdf",
        "application/acrobat",
        "applications/vnd.pdf",
        "text/pdf",
        "application/octet-stream",
    }
    if content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PDF document.")

    if content is not None and not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Uploaded file does not appear to be a valid PDF.")
