#!/bin/bash

# RAG Policy Chatbot — Startup Script

echo "🚀 Starting Policy Chatbot Setup..."

# 1. Setup Virtual Environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

# 2. Install Dependencies
echo "Installing dependencies..."
pip install -r backend/requirements.txt

# 3. Handle Ollama
echo "Checking Ollama..."
if ! command -v ollama &> /dev/null
then
    echo "⚠️ Ollama not found in PATH. Please install it from https://ollama.ai"
    # Do not exit, maybe it's running but not in path for some reason
fi

# Try to start ollama serve in background if not running
if ! pgrep -x "ollama" > /dev/null
then
    echo "Starting Ollama server..."
    ollama serve &
    sleep 5
fi

echo "Pulling llama3.1 model (this may take a while if first time)..."
ollama pull llama3.1

# 4. Start Backend
echo "Starting FastAPI server..."
cd backend
python3 -m uvicorn main:app --reload --port 8000
