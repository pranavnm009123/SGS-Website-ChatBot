import json
import logging
import re
import requests
from db import get_db
from doc_registry import get_approved_doc_ids
from embeddings import get_model

log = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3:8b"
OLLAMA_OPTIONS = {
    "temperature": 0.15,
    "top_p": 0.85,
    "top_k": 20,
    "repeat_penalty": 1.15,
    "num_ctx": 4096,
    "num_predict": 512,
}
SITE_DOC_IDS = ["site_home", "site_about", "site_services", "site_contact"]

PDF_GAP_THRESHOLD   = 0.08  # PDFs included only if within this gap of best site match
PDF_ABS_THRESHOLD   = 0.35  # PDFs never included if best PDF distance exceeds this (not relevant enough)
SITE_ABS_THRESHOLD  = 0.60  # site chunks ignored if best site chunk is too weak
SITE_CONTEXT_MARGIN = 0.15  # how far from best site chunk to include in LLM context
PDF_MARGIN          = 0.06  # within PDF pool, keep chunks within this of best PDF match
MAX_SITE_CONTEXT_CHUNKS = 6
MAX_PDF_CONTEXT_CHUNKS = 4
PER_SOURCE_CHUNK_CAP = 2


def _query_pool(db, query_embedding, doc_ids, n):
    if not doc_ids:
        return []
    try:
        r = db.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n, 100),
            where={"doc_id": {"$in": doc_ids}},
            include=["documents", "metadatas", "distances"],
        )
        docs = r.get("documents", [[]])[0] or []
        metas = r.get("metadatas", [[]])[0] or []
        dists = r.get("distances", [[]])[0] or []
        ids = r.get("ids", [[]])[0] or []
        rows = []
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, dists)):
            rows.append({
                "id": ids[i] if i < len(ids) else "",
                "text": doc,
                "meta": meta or {},
                "distance": float(dist),
            })
        return rows
    except Exception:
        return []


def _apply_margin(rows, margin):
    if not rows:
        return []
    cutoff = rows[0]["distance"] + margin
    return [row for row in rows if row["distance"] <= cutoff]


def _normalized_text(text):
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


def _source_key(row):
    meta = row["meta"]
    if meta.get("source_type") == "pdf":
        return ("pdf", meta.get("filename", "document"))
    return ("website", meta.get("url", "/"))


def _select_diverse(rows, max_chunks):
    if not rows:
        return []
    selected = []
    per_source = {}
    seen_text = set()

    for row in rows:
        if len(selected) >= max_chunks:
            break
        key = _source_key(row)
        if per_source.get(key, 0) >= PER_SOURCE_CHUNK_CAP:
            continue
        text_key = _normalized_text(row["text"])
        if text_key in seen_text:
            continue
        seen_text.add(text_key)
        per_source[key] = per_source.get(key, 0) + 1
        selected.append(row)
    return selected


def _relevance(distance):
    # Chroma cosine distance: lower is better; convert to a stable 0..1 score.
    return round(1.0 / (1.0 + max(distance, 0.0)), 3)


def _snippet(text, limit=180):
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


SYSTEM_PROMPT = """You are Alex, a virtual assistant for SGS Technologies. You are part of the team.

RULES:
- Your name is **Alex**. ONLY introduce yourself if the user specifically asks who you are, what your name is, or what you do. For all other questions, just answer directly.
- Speak in first-person plural ("we", "our", "us") as a company representative.
- Answer using ONLY the provided context. Never invent, guess, or paraphrase vaguely.
- When the context contains numbers, prices, or specific details, lead with those — quote them exactly.
- Be concise and professional. Use short paragraphs.
- Use **bold** for key terms or names. Use bullet points when listing 3+ items.
- Do NOT include source citations, bracketed references, or filenames — sources are shown separately in the UI.

FALLBACK (use when the context does not contain specific facts to answer the question):
- Say EXACTLY: "I don't have that information right now — feel free to reach out to us at hello@sgstech.com and we'll be happy to help!"
- If you use this fallback, output ONLY that sentence. Do not add anything before or after it. Do not combine it with partial answers or guesses."""


def _build_messages(question, context):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question} /no_think"},
    ]


_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.DOTALL)


def _build_context_and_sources(question):
    query_embedding = get_model().encode(question).tolist()
    db = get_db()
    approved_pdf_ids = get_approved_doc_ids()

    site_rows = _query_pool(db, query_embedding, SITE_DOC_IDS, 10)
    pdf_rows = _query_pool(db, query_embedding, approved_pdf_ids, 8)

    site_best = site_rows[0]["distance"] if site_rows else 1.0
    pdf_best  = pdf_rows[0]["distance"] if pdf_rows else 1.0

    include_pdfs = (
        bool(approved_pdf_ids)
        and pdf_best <= PDF_ABS_THRESHOLD
        and pdf_best <= site_best + PDF_GAP_THRESHOLD
    )

    raw_site = _apply_margin(site_rows, SITE_CONTEXT_MARGIN)
    raw_pdf = _apply_margin(pdf_rows, PDF_MARGIN) if include_pdfs else []

    site_context_chunks = _select_diverse(raw_site, MAX_SITE_CONTEXT_CHUNKS) if site_best <= SITE_ABS_THRESHOLD else []
    pdf_chunks = _select_diverse(raw_pdf, MAX_PDF_CONTEXT_CHUNKS)

    if not site_context_chunks and not pdf_chunks:
        return None, []

    # ── Build context for LLM ─────────────────────────────────────────────────
    context_parts = []
    used_chunks = []

    for row in pdf_chunks:
        text = row["text"]
        meta = row["meta"]
        filename = meta.get("filename", "document")
        page     = meta.get("page", "?")
        context_parts.append(f"[{filename} — Page {page}]: {text}")
        used_chunks.append(row)

    for row in site_context_chunks:
        text = row["text"]
        meta = row["meta"]
        page_name = meta.get("page_name", "")
        context_parts.append(f"[{page_name} Page]: {text}")
        used_chunks.append(row)

    context = "\n\n---\n\n".join(context_parts)

    # ── Sources = exactly what was used as context ────────────────────────────
    sources = []
    source_index = {}
    ordered_keys = []

    for row in used_chunks:
        meta = row["meta"]
        key = _source_key(row)
        if key not in source_index:
            ordered_keys.append(key)
            if key[0] == "pdf":
                filename = meta.get("filename", "document")
                source_index[key] = {
                    "type": "pdf",
                    "filename": filename,
                    "url": f"/pdf/{filename}",
                    "source_id": f"pdf::{filename}",
                    "distance": row["distance"],
                    "relevance": _relevance(row["distance"]),
                    "snippet": _snippet(row["text"]),
                    "chunk_count": 1,
                    "pages": [meta.get("page", "?")],
                }
            else:
                url = meta.get("url", "/")
                page_name = meta.get("page_name", "Website")
                source_index[key] = {
                    "type": "website",
                    "page_name": page_name,
                    "url": url,
                    "source_id": f"web::{url}",
                    "distance": row["distance"],
                    "relevance": _relevance(row["distance"]),
                    "snippet": _snippet(row["text"]),
                    "chunk_count": 1,
                }
            continue

        src = source_index[key]
        src["chunk_count"] += 1
        if row["distance"] < src["distance"]:
            src["distance"] = row["distance"]
            src["relevance"] = _relevance(row["distance"])
            src["snippet"] = _snippet(row["text"])
        if src["type"] == "pdf":
            page = meta.get("page", "?")
            if page not in src["pages"]:
                src["pages"].append(page)

    for key in ordered_keys:
        src = source_index[key]
        if src["type"] == "pdf":
            src["pages"] = sorted(src["pages"], key=lambda p: (str(type(p)), p))
        sources.append(src)

    return context, sources


def answer_question(question):
    context, sources = _build_context_and_sources(question)

    if context is None:
        return {
            "answer": "I couldn't find anything relevant to that question in the available content.",
            "sources": []
        }

    messages = _build_messages(question, context)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False, "options": OLLAMA_OPTIONS},
            timeout=60,
        )
        response.raise_for_status()
        answer = response.json().get("message", {}).get("content", "")
        answer = _THINK_RE.sub("", answer).strip()
        return {"answer": answer, "sources": sources}
    except Exception as e:
        log.error("Error calling Ollama: %s", e)
        return {
            "answer": "I encountered an error while generating an answer. Please make sure Ollama is running.",
            "sources": []
        }


def answer_question_stream(question):
    """Generator that yields SSE events: token chunks, then a final sources event."""
    context, sources = _build_context_and_sources(question)

    if context is None:
        msg = json.dumps({"type": "token", "content": "I couldn't find anything relevant to that question in the available content."})
        yield f"data: {msg}\n\n"
        src_msg = json.dumps({"type": "sources", "sources": []})
        yield f"data: {src_msg}\n\n"
        yield "data: [DONE]\n\n"
        return

    messages = _build_messages(question, context)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": True, "options": OLLAMA_OPTIONS},
            timeout=120,
            stream=True,
        )

        response.raise_for_status()

        in_think = False
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                token = chunk.get("message", {}).get("content", "")
                # Filter out <think>...</think> blocks
                if "<think>" in token:
                    in_think = True
                if in_think:
                    if "</think>" in token:
                        in_think = False
                        token = token.split("</think>", 1)[1]
                        if not token:
                            continue
                    else:
                        continue
                if token:
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                if chunk.get("done"):
                    break

        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        log.error("Error streaming from Ollama: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'content': 'I encountered an error while generating an answer. Please make sure Ollama is running.'})}\n\n"
        yield "data: [DONE]\n\n"
