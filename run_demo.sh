#!/bin/bash

echo "🚀 Starting Knowledge Base Search & Enrichment Demo"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt > /dev/null 2>&1

# Start the API server in the background
echo "Starting API server..."
python -m uvicorn app.main:app --port 8000 &
API_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 5

# Run the demo
echo ""
echo "Running demo script..."
python demo_script.py

# Kill the API server
echo ""
echo "Stopping API server..."
kill $API_PID

echo "Demo completed!"