import json
import logging
import os
import re
from urllib.parse import quote
import requests
from db import get_db
from doc_registry import get_approved_doc_ids
from embeddings import get_model

log = logging.getLogger(__name__)


def _env_float(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return float(value)
    except ValueError:
        log.warning("Invalid float for %s=%r, using default %s", name, value, default)
        return default


def _env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        log.warning("Invalid int for %s=%r, using default %s", name, value, default)
        return default


FALLBACK_ANSWER = (
    "I don't have that information right now — feel free to reach out to us at "
    "info@sgstechnologies.net or call (904) 332-4534 and we'll be happy to help!"
)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")
OLLAMA_TIMEOUT_SECONDS = _env_int("OLLAMA_TIMEOUT_SECONDS", 180)
OLLAMA_STREAM_TIMEOUT_SECONDS = _env_int("OLLAMA_STREAM_TIMEOUT_SECONDS", 240)
OLLAMA_OPTIONS = {
    "temperature": _env_float("OLLAMA_TEMPERATURE", 0.15),
    "top_p": _env_float("OLLAMA_TOP_P", 0.85),
    "top_k": _env_int("OLLAMA_TOP_K", 20),
    "repeat_penalty": _env_float("OLLAMA_REPEAT_PENALTY", 1.15),
    "num_ctx": _env_int("OLLAMA_NUM_CTX", 4096),
    "num_predict": _env_int("OLLAMA_NUM_PREDICT", 512),
}
SITE_DOC_IDS = [
    "site_home", "site_about", "site_services", "site_contact",
    "site_careers", "site_products", "site_testimonials",
    "site_software_engineering", "site_cloud_services",
    "site_cyber_security", "site_data_engineering",
]

PDF_ABS_THRESHOLD = _env_float("RETRIEVAL_PDF_ABS_THRESHOLD", 0.48)
SITE_ABS_THRESHOLD = _env_float("RETRIEVAL_SITE_ABS_THRESHOLD", 0.60)
SITE_CONTEXT_MARGIN = _env_float("RETRIEVAL_SITE_MARGIN", 0.15)
PDF_MARGIN = _env_float("RETRIEVAL_PDF_MARGIN", 0.10)
MAX_SITE_CONTEXT_CHUNKS = _env_int("RETRIEVAL_MAX_SITE_CHUNKS", 6)
MAX_PDF_CONTEXT_CHUNKS = _env_int("RETRIEVAL_MAX_PDF_CHUNKS", 6)
MAX_SITE_CONTEXT_CHUNKS_MULTI = _env_int("RETRIEVAL_MAX_SITE_CHUNKS_MULTI", 5)
MAX_PDF_CONTEXT_CHUNKS_MULTI = _env_int("RETRIEVAL_MAX_PDF_CHUNKS_MULTI", 8)
PER_SOURCE_CHUNK_CAP = _env_int("RETRIEVAL_PER_SOURCE_CHUNK_CAP", 2)
PER_SOURCE_CHUNK_CAP_MULTI = _env_int("RETRIEVAL_PER_SOURCE_CHUNK_CAP_MULTI", 3)


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
        log.exception("Vector query failed for doc_ids=%s", doc_ids[:5])
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


def _select_diverse(rows, max_chunks, per_source_cap=PER_SOURCE_CHUNK_CAP, prioritize_source_diversity=False):
    if not rows:
        return []

    deduped = []
    seen_text = set()
    for row in rows:
        text_key = _normalized_text(row["text"])
        if text_key in seen_text:
            continue
        seen_text.add(text_key)
        deduped.append(row)

    if not prioritize_source_diversity:
        selected = []
        per_source = {}
        for row in deduped:
            if len(selected) >= max_chunks:
                break
            key = _source_key(row)
            if per_source.get(key, 0) >= per_source_cap:
                continue
            per_source[key] = per_source.get(key, 0) + 1
            selected.append(row)
        return selected

    grouped = {}
    ordered_keys = []
    for row in deduped:
        key = _source_key(row)
        if key not in grouped:
            grouped[key] = []
            ordered_keys.append(key)
        grouped[key].append(row)

    selected = []
    per_source = {key: 0 for key in ordered_keys}
    while len(selected) < max_chunks:
        added = False
        for key in ordered_keys:
            if len(selected) >= max_chunks:
                break
            if per_source[key] >= per_source_cap:
                continue
            bucket = grouped[key]
            if not bucket:
                continue
            selected.append(bucket.pop(0))
            per_source[key] += 1
            added = True
        if not added:
            break
    return selected


def _relevance(distance):
    # Chroma cosine distance: lower is better; convert to a stable 0..1 score.
    return round(1.0 / (1.0 + max(distance, 0.0)), 3)


def _snippet(text, limit=180):
    cleaned = re.sub(r"\s+", " ", (text or "")).strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


_SOURCE_WORD_RE = re.compile(r"[a-z0-9]+")
_SOURCE_STOPWORDS = {
    "sgs",
    "pdf",
    "page",
    "pages",
    "document",
    "documents",
    "policy",
    "plan",
    "framework",
    "guidelines",
    "standards",
    "charter",
    "manual",
    "protocol",
}
_QUESTION_STOPWORDS = {
    "across",
    "about",
    "what",
    "which",
    "where",
    "when",
    "their",
    "there",
    "these",
    "those",
    "using",
    "within",
    "trace",
    "full",
    "lifecycle",
    "global",
    "considerations",
    "question",
    "production",
    "review",
}
_QUESTION_SOURCE_CUES = {
    "pdf",
    "document",
    "documents",
    "policy",
    "plan",
    "framework",
    "guidelines",
    "standards",
    "charter",
    "manual",
    "protocol",
    "page",
    "pages",
    "website",
    "homepage",
    "site",
}
_PDF_SOURCE_CUES = {
    "pdf",
    "document",
    "documents",
    "policy",
    "plan",
    "framework",
    "guidelines",
    "standards",
    "charter",
    "manual",
    "protocol",
}
_WEBSITE_SOURCE_CUES = {
    "page",
    "pages",
    "website",
    "homepage",
    "site",
}


def _tokens(text):
    return _SOURCE_WORD_RE.findall(_normalized_text(text))


def _question_source_terms(question):
    normalized = _normalized_text(question)
    terms = set(_tokens(question))
    if "homepage" in terms or "home page" in normalized:
        terms.add("home")
    return terms


def _source_terms(row):
    meta = row["meta"]
    if meta.get("source_type") == "pdf":
        text = meta.get("filename", "")
    else:
        text = f"{meta.get('page_name', '')} {meta.get('url', '')}"

    terms = []
    for token in _tokens(text):
        if token in _SOURCE_STOPWORDS or token.isdigit() or len(token) < 4:
            continue
        terms.append(token)
    return set(terms)


def _question_mentions_source(question, row):
    question_terms = _question_source_terms(question)
    source_terms = _source_terms(row)
    if not source_terms:
        return False
    overlap = question_terms & source_terms
    threshold = 2 if len(source_terms) >= 2 else 1
    return len(overlap) >= threshold


def _question_has_explicit_source_reference(question):
    normalized = _normalized_text(question)
    question_tokens = _question_source_terms(question)
    if question_tokens & _QUESTION_SOURCE_CUES:
        return True
    if any(phrase in normalized for phrase in ("according to", "from the ", "on the ", "in the ")):
        return True
    return False


def _question_explicitly_targets_pdf(question):
    return bool(_question_source_terms(question) & _PDF_SOURCE_CUES)


def _question_explicitly_targets_website(question):
    return bool(_question_source_terms(question) & _WEBSITE_SOURCE_CUES)


def _question_source_overlap(question, row):
    question_terms = _question_source_terms(question)
    overlap = len(question_terms & _source_terms(row))
    meta = row["meta"]
    if meta.get("source_type") == "website" and _normalized_text(meta.get("page_name", "")) == "home" and "home" in question_terms:
        overlap += 1
    return overlap


def _filter_to_named_sources(question, rows):
    if not rows:
        return []
    matching = [row for row in rows if _question_mentions_source(question, row)]
    if matching:
        best_overlap = max(_question_source_overlap(question, row) for row in matching)
        return [row for row in matching if _question_source_overlap(question, row) == best_overlap]

    if not _question_has_explicit_source_reference(question):
        return rows

    source_type = rows[0]["meta"].get("source_type")
    if source_type == "website" and _question_explicitly_targets_pdf(question) and not _question_explicitly_targets_website(question):
        return []

    best_overlap = max(_question_source_overlap(question, row) for row in rows)
    if best_overlap <= 0:
        return []
    return [row for row in rows if _question_source_overlap(question, row) == best_overlap]


def _question_terms(question):
    return {
        token
        for token in _tokens(question)
        if token not in _QUESTION_STOPWORDS and len(token) >= 4
    }


def _row_text_terms(row):
    return {
        token
        for token in _tokens(row["text"])
        if token not in _QUESTION_STOPWORDS and len(token) >= 4
    }


def _row_text_overlap(question, row):
    return len(_question_terms(question) & _row_text_terms(row))


def _row_priority(question, row):
    question_terms = _question_terms(question)
    if not question_terms:
        return (0, 0, -row["distance"])

    text_terms = _row_text_terms(row)
    overlap = len(question_terms & text_terms)
    source_overlap = len(question_terms & _source_terms(row))
    text = _normalized_text(row["text"])
    penalty = 0
    if "revision history" in text or "official executive publication" in text:
        penalty += 2
    if "this document defines the official" in text:
        penalty += 1
    return (source_overlap, overlap - penalty, -row["distance"])


def _rank_rows(question, rows):
    return sorted(rows, key=lambda row: _row_priority(question, row), reverse=True)


def _is_low_signal_chunk(text):
    normalized = _normalized_text(text)
    low_signal_phrases = (
        "official executive publication",
        "this document defines the official",
        "appendix: revision history",
        "initial publication. approved by the board of directors",
    )
    return any(phrase in normalized for phrase in low_signal_phrases)


def _prune_low_signal_rows(rows):
    high_signal = [row for row in rows if not _is_low_signal_chunk(row["text"])]
    return high_signal if high_signal else rows


def _filter_selected_chunks(question, rows):
    if not rows or _looks_multi_source(question):
        return rows

    explicit_source = _question_has_explicit_source_reference(question)
    aligned = []
    for row in rows:
        source_overlap = _question_source_overlap(question, row)
        text_overlap = _row_text_overlap(question, row)
        if source_overlap > 0 or text_overlap > 0:
            aligned.append(row)

    if not aligned:
        return rows[:1]

    if not explicit_source:
        return aligned

    strong_source_rows = [row for row in aligned if _question_source_overlap(question, row) > 0]
    if strong_source_rows:
        return strong_source_rows

    strong_text_rows = [row for row in aligned if _row_text_overlap(question, row) >= 2]
    return strong_text_rows or aligned[:1]


def _question_prefers_pdfs(question):
    normalized = _normalized_text(question)
    website_cues = ("website", "homepage", "home page", "advertises", "mentions", "site")
    if any(cue in normalized for cue in website_cues):
        return False
    return any(
        cue in normalized
        for cue in (
            "across the ",
            "using the ",
            "compare ",
            "within the ",
            "from the ",
        )
    )


def _looks_multi_source(question):
    normalized = _normalized_text(question)
    cues = [
        "across ",
        "compare ",
        "both ",
        "trace ",
        "full lifecycle",
        "full picture",
        "using the ",
        "interact ",
    ]
    if any(cue in normalized for cue in cues):
        return True
    return normalized.count(",") >= 2 and " and " in normalized


def _context_limits(question):
    if _looks_multi_source(question):
        return {
            "site_chunks": MAX_SITE_CONTEXT_CHUNKS_MULTI,
            "pdf_chunks": MAX_PDF_CONTEXT_CHUNKS_MULTI,
            "pdf_per_source_cap": PER_SOURCE_CHUNK_CAP_MULTI,
        }
    return {
        "site_chunks": MAX_SITE_CONTEXT_CHUNKS,
        "pdf_chunks": MAX_PDF_CONTEXT_CHUNKS,
        "pdf_per_source_cap": PER_SOURCE_CHUNK_CAP,
    }


SYSTEM_PROMPT = """You are Alex, a virtual assistant for SGS Technologie, a software development company headquartered in Jacksonville, Florida. You are part of the team.

RULES:
- Your name is **Alex**. ONLY introduce yourself if the user specifically asks who you are, what your name is, or what you do. For all other questions, just answer directly.
- Speak in first-person plural ("we", "our", "us") as a company representative.
- Answer using ONLY the provided context. Never invent, guess, or paraphrase vaguely.
- If the answer requires combining facts from multiple context blocks or documents, synthesize them into one grounded response instead of using the fallback.
- If relevant facts are present anywhere in the context, answer with those facts. Do not use the fallback just because the answer spans multiple snippets.
- When the context contains numbers, prices, or specific details, lead with those — quote them exactly.
- Be concise and professional. Use short paragraphs.
- Use **bold** for key terms or names. Use bullet points when listing 3+ items.
- Do NOT include source citations, bracketed references, or filenames — sources are shown separately in the UI.

FALLBACK (use when the context does not contain specific facts to answer the question):
- Say EXACTLY: "I don't have that information right now — feel free to reach out to us at info@sgstechnologies.net or call (904) 332-4534 and we'll be happy to help!"
- If you use this fallback, output ONLY that sentence. Do not add anything before or after it. Do not combine it with partial answers or guesses."""


def _build_messages(question, context):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Use the context below to answer the question. "
                "If the needed facts appear across multiple snippets, combine them into one answer.\n\n"
                f"Context:\n{context}\n\nQuestion: {question}"
            ),
        },
    ]


_THINK_RE = re.compile(r"<think>[\s\S]*?</think>", re.DOTALL)


def _finalize_answer(answer):
    cleaned = _THINK_RE.sub("", answer or "").strip()
    return cleaned or FALLBACK_ANSWER


def _split_sentences(text):
    pieces = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())
    return [piece.strip() for piece in pieces if piece.strip()]


def _extractive_answer_from_context(question, context, max_sentences=5):
    question_terms = _question_terms(question)
    scored = []
    seen = set()

    for block in context.split("\n\n---\n\n"):
        if ": " in block:
            _, text = block.split(": ", 1)
        else:
            text = block

        for sentence in _split_sentences(text):
            normalized = _normalized_text(sentence)
            if normalized in seen or _is_low_signal_chunk(sentence):
                continue
            seen.add(normalized)

            sentence_terms = {
                token for token in _tokens(sentence)
                if token not in _QUESTION_STOPWORDS and len(token) >= 4
            }
            overlap = len(question_terms & sentence_terms)
            if overlap == 0:
                continue

            bonus = 0
            if re.search(r"\b\d", sentence):
                bonus += 1
            if any(char in sentence for char in ("%","$",":")):
                bonus += 1
            scored.append((overlap + bonus, sentence))

    if not scored:
        return None

    scored.sort(key=lambda item: item[0], reverse=True)
    selected = [sentence for _, sentence in scored[:max_sentences]]
    if len(selected) == 1:
        return selected[0]
    return "\n".join(f"- {sentence}" for sentence in selected)


def _page_number(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _page_sort_key(value):
    page = _page_number(value)
    if page is not None:
        return (0, page)
    return (1, str(value))


def _pdf_source_url(filename, pages):
    base_url = f"/pdf/{quote(filename)}"
    first_page = next((page for page in (_page_number(value) for value in pages) if page is not None), None)
    if first_page is None:
        return base_url
    return f"{base_url}#page={first_page}"


def _build_context_and_sources(question):
    query_embedding = get_model().encode(question).tolist()
    db = get_db()
    approved_pdf_ids = get_approved_doc_ids()
    limits = _context_limits(question)

    site_rows = _query_pool(db, query_embedding, SITE_DOC_IDS, 12)
    pdf_rows = _query_pool(db, query_embedding, approved_pdf_ids, 18)

    site_best = site_rows[0]["distance"] if site_rows else 1.0
    pdf_best  = pdf_rows[0]["distance"] if pdf_rows else 1.0

    raw_site = _apply_margin(site_rows, SITE_CONTEXT_MARGIN) if site_best <= SITE_ABS_THRESHOLD else []
    raw_pdf = _apply_margin(pdf_rows, PDF_MARGIN) if approved_pdf_ids and pdf_best <= PDF_ABS_THRESHOLD else []

    raw_pdf = _rank_rows(question, _prune_low_signal_rows(_filter_to_named_sources(question, raw_pdf)))
    raw_site = _rank_rows(question, _prune_low_signal_rows(_filter_to_named_sources(question, raw_site)))

    if raw_pdf and _question_prefers_pdfs(question):
        raw_site = []

    site_context_chunks = _select_diverse(raw_site, limits["site_chunks"])
    pdf_chunks = _select_diverse(
        raw_pdf,
        limits["pdf_chunks"],
        per_source_cap=limits["pdf_per_source_cap"],
        prioritize_source_diversity=True,
    )
    site_context_chunks = _filter_selected_chunks(question, site_context_chunks)
    pdf_chunks = _filter_selected_chunks(question, pdf_chunks)

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
                page = meta.get("page", "?")
                source_index[key] = {
                    "type": "pdf",
                    "filename": filename,
                    "url": _pdf_source_url(filename, [page]),
                    "source_id": f"pdf::{filename}",
                    "distance": row["distance"],
                    "relevance": _relevance(row["distance"]),
                    "snippet": _snippet(row["text"]),
                    "chunk_count": 1,
                    "pages": [page],
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
            src["pages"] = sorted(src["pages"], key=_page_sort_key)
            src["url"] = _pdf_source_url(src["filename"], src["pages"])
        sources.append(src)

    return context, sources


def answer_question(question):
    context, sources = _build_context_and_sources(question)

    if context is None:
        return {
            "answer": FALLBACK_ANSWER,
            "sources": []
        }

    messages = _build_messages(question, context)

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "messages": messages, "stream": False, "options": OLLAMA_OPTIONS},
            timeout=OLLAMA_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        answer = response.json().get("message", {}).get("content", "")
        answer = _finalize_answer(answer)
        if answer == FALLBACK_ANSWER and context and sources:
            extractive_answer = _extractive_answer_from_context(question, context)
            if extractive_answer:
                answer = extractive_answer
        return {"answer": answer, "sources": sources}
    except Exception as e:
        log.error("Error calling Ollama: %s", e)
        return {
            "answer": "I encountered an error while generating an answer. Please make sure Ollama is running.",
            "sources": []
        }


def answer_question_stream(question):
    """Generator that yields SSE events: token chunks, then a final sources event."""
    if _looks_multi_source(question):
        result = answer_question(question)
        yield f"data: {json.dumps({'type': 'token', 'content': result['answer']})}\n\n"
        yield f"data: {json.dumps({'type': 'sources', 'sources': result['sources']})}\n\n"
        yield "data: [DONE]\n\n"
        return

    context, sources = _build_context_and_sources(question)

    if context is None:
        msg = json.dumps({"type": "token", "content": FALLBACK_ANSWER})
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
            timeout=OLLAMA_STREAM_TIMEOUT_SECONDS,
            stream=True,
        )

        response.raise_for_status()

        in_think = False
        emitted_text = False
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
                    emitted_text = True
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                if chunk.get("done"):
                    break

        if not emitted_text:
            yield f"data: {json.dumps({'type': 'token', 'content': FALLBACK_ANSWER})}\n\n"
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as e:
        log.error("Error streaming from Ollama: %s", e)
        yield f"data: {json.dumps({'type': 'error', 'content': 'I encountered an error while generating an answer. Please make sure Ollama is running.'})}\n\n"
        yield "data: [DONE]\n\n"
