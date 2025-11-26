#!/bin/bash

echo "🚀 Deploying LexAI Scholar..."
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "❌ Git repository not initialized. Please initialize git first:"
    echo "   git init"
    echo "   git add ."
    echo "   git commit -m 'Initial commit'"
    exit 1
fi

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
    echo "📝 Uncommitted changes found. Committing..."
    git add .
    git commit -m "Deploy: $(date +%Y-%m-%d_%H:%M:%S)"
else
    echo "✅ No uncommitted changes"
fi

# Push to GitHub (triggers Render auto-deploy)
echo ""
echo "📤 Pushing to GitHub..."
git push origin main

# Deploy frontend to Vercel
echo ""
echo "🎨 Deploying frontend to Vercel..."
cd LexAIScholar

if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

vercel --prod

cd ..

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "📊 Check deployment status:"
echo "   Backend: https://dashboard.render.com"
echo "   Frontend: https://vercel.com/dashboard"

