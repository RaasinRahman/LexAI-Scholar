#!/bin/bash

echo "🚀 Starting LexAI Scholar Backend..."
echo ""
echo "📦 Checking virtual environment..."

cd backend


if [ ! -d ".venv" ]; then
    echo "⚠️  Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt
fi


if ! .venv/bin/python -c "import fastapi" 2>/dev/null; then
    echo "⚠️  Installing Python dependencies..."
    .venv/bin/pip install -r requirements.txt
fi

echo ""
echo "✅ Dependencies OK"
echo ""
echo "🔧 Starting FastAPI server..."
echo "   Backend will be available at: http://localhost:8000"
echo "   API docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

.venv/bin/python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

