import logging
import fitz  # PyMuPDF
import pdfplumber
from langchain.text_splitter import RecursiveCharacterTextSplitter
from db import get_db
from doc_registry import update_doc_status
from embeddings import get_model

log = logging.getLogger(__name__)

def ingest_document(doc_id, filepath, filename):
    try:
        text_content = []
        
        # 1. Extract text with PyMuPDF
        doc = fitz.open(filepath)
        page_count = len(doc)

        try:
            # 2. Iterate through pages for text and tables
            with pdfplumber.open(filepath) as pdf:
                for i in range(page_count):
                    page_text = doc[i].get_text()

                    # Extract tables with pdfplumber
                    table_text = ""
                    plumber_page = pdf.pages[i]
                    tables = plumber_page.extract_tables()
                    for table in tables:
                        for row in table:
                            # Convert each table to pipe-delimited text rows
                            row_text = " | ".join([str(cell) if cell is not None else "" for cell in row])
                            table_text += row_text + "\n"

                    combined_page_text = f"{page_text}\n{table_text}"
                    text_content.append({"text": combined_page_text, "page": i + 1})
        finally:
            doc.close()

        # 3. Split combined text
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        chunks = []
        for item in text_content:
            page_chunks = text_splitter.split_text(item["text"])
            total_page_chunks = len(page_chunks)
            for page_chunk_idx, chunk in enumerate(page_chunks):
                chunks.append({
                    "text": chunk,
                    "metadata": {
                        "doc_id": doc_id,
                        "filename": filename,
                        "page": item["page"],
                        "source_type": "pdf",
                        "chunk_index": page_chunk_idx,
                        "page_chunk_count": total_page_chunks,
                        "source_label": f"{filename} (Page {item['page']})",
                    }
                })

        # 4. Generate embeddings and upsert into ChromaDB
        db = get_db()
        texts = [c["text"] for c in chunks]
        embeddings = get_model().encode(texts).tolist()
        metadatas = [c["metadata"] for c in chunks]
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        
        db.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )

        # 5. Update registry
        update_doc_status(doc_id, "approved", chunk_count=len(chunks))
        return len(chunks)

    except Exception as e:
        log.error("Ingestion failed for %s: %s", filename, e)
        update_doc_status(doc_id, "error")
        raise e
