# Acme Corp Policy Chatbot & Website

A full-stack, locally hosted web application and Retrieval-Augmented Generation (RAG) chatbot designed for "Acme Corp" (or any corporate entity). The project combines a modern frontend website with an intelligent FastAPI backend powered by local LLMs (Ollama) and vector search (ChromaDB) to answer user questions using both website content and uploaded PDF documents.

## 🚀 Features

- **Modern Website Features**: Vanilla HTML, CSS, and JS web pages (Home, About, Services, Contact) featuring a responsive and dynamic design.
- **RAG Chatbot Widget**: A floating chat widget built into the website with real-time token streaming (`/chat/stream`), answering user queries strictly based on indexed context.
- **Admin Panel**: Accessible at `/admin`, allowing administrators to:
  - Upload, approve, and delete PDF documents.
  - See real-time statuses of processing documents.
  - Manually trigger website re-indexing.
- **Dual Knowledge Sources**:
  - **PDFs**: Asynchronously chunked, embedded, and added to ChromaDB upon approval.
  - **Website Pages**: HTML content is automatically extracted, chunked, and synchronized into ChromaDB. Changes to frontend HTML files instantly trigger a background re-indexing via a watchdog observer.
- **100% Local Inference**: Powered by local embedding models (`BAAI/bge-large-en-v1.5`) and a local LLM (`llama3.1`) hosted via Ollama. No data leaves your machine.

## 🛠️ Tech Stack

- **Backend**: FastAPI, Uvicorn, Python 3.9+
- **Frontend**: Vanilla HTML5, CSS3, JavaScript
- **Vector Database**: ChromaDB (persistent local storage)
- **Local LLM**: Ollama (`llama3.1:latest`)
- **Embeddings**: SentenceTransformers (`BAAI/bge-large-en-v1.5` - 1024 dims)
- **PDF Processing**: PyMuPDF (`fitz`), LangChain text splitters

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
1. **Python 3.9+**
2. **Ollama**: Download and install from [ollama.com](https://ollama.com).
3. **Llama 3.1 Model**: Run `ollama run llama3.1` in your terminal to pull the model down prior to starting.

## ⚙️ Setup & Installation

1. Clone this repository (or navigate to the project directory).
2. Use the provided setup script to automatically create a virtual environment, install dependencies, and start the server:

```bash
cd policy-chatbot
bash run.sh
```

**What `run.sh` does:**
- Creates a Python virtual environment (`venv`).
- Activates it and installs packages from `backend/requirements.txt`.
- Checks if Ollama is running and attempts to pull/run `llama3.1`.
- Starts the FastAPI server (`uvicorn`) with hot-reloading.

If you prefer to start it manually (after dependencies are installed):
```bash
source venv/bin/activate
cd backend
python -m uvicorn main:app --reload --port 8000
```

## 💻 Usage

Once the server is running, you can access the application in your browser:

- **Public Website Site & Chatbot**: [http://localhost:8000/](http://localhost:8000/)
- **Admin Panel**: [http://localhost:8000/admin](http://localhost:8000/admin)
- **API Documentation (Swagger)**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### Uploading Documents
1. Navigate to the Admin Panel.
2. Drag and drop (or select) a PDF to upload.
3. The document will appear as `pending`. Click **Approve** to trigger the background ingestion process (extracting text, generating embeddings, and storing in ChromaDB).
4. Wait for the status to turn `approved`. The chatbot can now use information from the document!

### Editing the Website
Any time you edit and save an HTML page inside the `frontend/` directory, the backend's automatic file watcher will instantly update the indexed ChromaDB vectors. You do not need to restart the server.

## 🔒 Security & Admin Access

- The API endpoints (like document approval, deletion, and site re-indexing) are secured using an Admin Key.
- Default Admin Key: `localdev123` (used internally by the frontend logic).
- API rate limits are applied to upload and chat endpoints to prevent abuse.

## 🏛️ Architecture & Key Components

- `backend/main.py`: Central FastAPI application routing, background task handling, and static file serving.
- `backend/retrieval.py`: Handles querying ChromaDB with user input, generating a contextual prompt, and managing the stream from Ollama.
- `backend/ingestion.py`: Logic for chunking and embedding PDF documents.
- `backend/site_indexer.py`: Logic for stripping HTML tags from static pages and generating website vectors, alongside the `watchdog` process.
- `backend/db.py`: Singleton manager for the local persistent ChromaDB collection.
- `backend/doc_registry.py`: JSON-based tracker for document processing states (`pending` -> `processing` -> `approved`).
- `frontend/widget.js`: Self-contained script bounding the chat UI logic, maintaining session history locally in the browser. 

---
*Created by the Google DeepMind Antigravity AI agent.*
