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
    "temperature": 0.3,
    "top_p": 0.85,
    "top_k": 20,
    "repeat_penalty": 1.15,
    "num_ctx": 4096,
    "num_predict": 512,
}
SITE_DOC_IDS = ["site_home", "site_about", "site_services", "site_contact"]

PDF_GAP_THRESHOLD   = 0.08  # PDFs included only if within this gap of best site match
PDF_ABS_THRESHOLD   = 0.35  # PDFs never included if best PDF distance exceeds this (not relevant enough)
SITE_CONTEXT_MARGIN = 0.15  # how far from best site chunk to include in LLM context
SITE_SOURCE_MARGIN  = 0.05  # tighter margin for which pages appear as source tags
PDF_MARGIN          = 0.06  # within PDF pool, keep chunks within this of best PDF match


def _query_pool(db, query_embedding, doc_ids, n):
    if not doc_ids:
        return [], [], []
    try:
        r = db.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(n, 100),
            where={"doc_id": {"$in": doc_ids}},
            include=["documents", "metadatas", "distances"],
        )
        return r["documents"][0], r["metadatas"][0], r["distances"][0]
    except Exception:
        return [], [], []


def _apply_margin(docs, metas, dists, margin):
    if not dists:
        return []
    cutoff = dists[0] + margin
    return [(doc, meta, dist) for doc, meta, dist in zip(docs, metas, dists) if dist <= cutoff]


SYSTEM_PROMPT = """You are Alex, a friendly and knowledgeable virtual assistant for SGS Technologies. You are part of the team.

RULES:
- Your name is **Alex**. ONLY introduce yourself if the user specifically asks who you are, what your name is, or what you do. For all other questions, just answer directly without mentioning your name or role.
- Speak in first-person plural ("we", "our", "us") as a company representative.
- Answer using ONLY the provided context. Never invent information.
- Be warm, concise, and professional. Use short paragraphs.
- Use **bold** for key terms or names. Use bullet points when listing 3+ items.
- Do NOT include source citations, bracketed references, or filenames — sources are shown separately in the UI.
- If the context contains pricing or numbers, quote them exactly.
- If comparing documents, clearly state which document each fact comes from.
- If the answer is not in the context, say: "I don't have that information right now — feel free to reach out to us at hello@sgstech.com and we'll be happy to help!\""""


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

    site_docs, site_metas, site_dists = _query_pool(db, query_embedding, SITE_DOC_IDS, 8)
    pdf_docs,  pdf_metas,  pdf_dists  = _query_pool(db, query_embedding, approved_pdf_ids, 6)

    site_best = site_dists[0] if site_dists else 1.0
    pdf_best  = pdf_dists[0]  if pdf_dists  else 1.0

    include_pdfs = (
        bool(approved_pdf_ids)
        and pdf_best <= PDF_ABS_THRESHOLD
        and pdf_best <= site_best + PDF_GAP_THRESHOLD
    )

    site_context_chunks = _apply_margin(site_docs, site_metas, site_dists, SITE_CONTEXT_MARGIN)
    site_source_chunks  = _apply_margin(site_docs, site_metas, site_dists, SITE_SOURCE_MARGIN)
    pdf_chunks          = _apply_margin(pdf_docs,  pdf_metas,  pdf_dists,  PDF_MARGIN) if include_pdfs else []

    if not site_context_chunks and not pdf_chunks:
        return None, []

    # ── Build context for LLM ─────────────────────────────────────────────────
    context_parts = []
    for text, meta, _ in pdf_chunks:
        filename = meta.get("filename", "document")
        page     = meta.get("page", "?")
        context_parts.append(f"[{filename} — Page {page}]: {text}")

    for text, meta, _ in site_context_chunks:
        page_name = meta.get("page_name", "")
        context_parts.append(f"[{page_name} Page]: {text}")

    context = "\n\n---\n\n".join(context_parts)

    # ── Build source tags for UI ──────────────────────────────────────────────
    sources = []
    seen = set()

    for _, meta, _ in pdf_chunks:
        filename = meta.get("filename", "document")
        if filename not in seen:
            sources.append({"type": "pdf", "filename": filename, "url": f"/pdf/{filename}"})
            seen.add(filename)

    for _, meta, _ in site_source_chunks:
        url       = meta.get("url", "/")
        page_name = meta.get("page_name", "")
        if url not in seen:
            sources.append({"type": "website", "page_name": page_name, "url": url})
            seen.add(url)

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
