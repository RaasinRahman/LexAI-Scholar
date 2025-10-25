#!/bin/bash

echo "🎨 Starting LexAI Scholar Frontend..."
echo ""
echo "📦 Checking Node dependencies..."

cd LexAIScholar

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "⚠️  Installing Node dependencies..."
    npm install
fi

echo ""
echo "✅ Dependencies OK"
echo ""
echo "🔧 Starting Next.js development server..."
echo "   Frontend will be available at: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev

