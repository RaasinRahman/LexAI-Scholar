#!/bin/bash

echo "🔧 Deploying Memory Error Fix..."
echo ""

cd /Users/raasin/Desktop/LEXAI

echo "📝 Committing changes..."
git add .
git commit -m "Fix memory error: Switch to OpenAI embeddings API (free tier compatible)"

echo ""
echo "📤 Pushing to GitHub (triggers Render auto-deploy)..."
git push origin main

echo ""
echo "✅ Changes pushed!"
echo ""
echo "📊 Next steps:"
echo "1. Go to https://dashboard.render.com"
echo "2. Click 'lexai-backend'"
echo "3. Watch the 'Logs' tab"
echo "4. Wait for 'Your service is live 🎉' (3-5 minutes)"
echo ""
echo "✅ Look for: [SUCCESS] Vector service initialized successfully (using OpenAI embeddings)"
echo ""

