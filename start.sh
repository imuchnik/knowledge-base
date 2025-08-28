#!/bin/bash

# Start script for Knowledge Base Search & Enrichment API

echo "🚀 Starting Knowledge Base Search & Enrichment API..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo "Creating .env file from .env.example..."
    cp .env.example .env
fi

# Create necessary directories
mkdir -p uploaded_documents
mkdir -p chroma_db

# Start the API server
echo ""
echo "Starting API server on http://localhost:8000"
echo "API documentation available at:"
echo "  - Swagger UI: http://localhost:8000/docs"
echo "  - ReDoc: http://localhost:8000/redoc"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

# Start uvicorn with the main app
python -m uvicorn app.main:app --reload --port 8000