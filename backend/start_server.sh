#!/bin/bash
cd /Users/raasin/Desktop/LEXAI/backend

# Check if virtual environment exists
if [ -d ".venv" ]; then
    echo "🐍 Using virtual environment"
    PYTHON_CMD=".venv/bin/python"
    PIP_CMD=".venv/bin/pip"
elif command -v python3 &> /dev/null; then
    echo "🐍 Using system Python 3"
    PYTHON_CMD=python3
    PIP_CMD="python3 -m pip"
else
    echo "❌ Error: Python 3 is not installed"
    exit 1
fi

echo "📦 Checking dependencies..."

# Check if required packages are installed
if ! $PYTHON_CMD -c "import uvicorn" &> /dev/null; then
    echo "⚠️  Dependencies not found. Installing..."
    $PIP_CMD install -r requirements.txt
fi

echo ""
echo "🚀 Starting LexAI Backend Server..."
echo "📍 Server will be available at: http://localhost:8000"
echo "📖 API docs at: http://localhost:8000/docs"
echo ""

$PYTHON_CMD -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

