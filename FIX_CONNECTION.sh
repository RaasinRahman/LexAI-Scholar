#!/bin/bash

echo "🔧 Fixing Frontend-Backend Connection..."
echo ""

cd /Users/raasin/Desktop/LEXAI

echo "✅ Step 1: Fixed CORS configuration in backend/main.py"
echo "   Now allows all Vercel deployments"
echo ""

echo "📤 Step 2: Pushing CORS fix to GitHub..."
git add backend/main.py
git commit -m "Fix CORS: Allow Vercel deployments"
git push origin main

echo ""
echo "✅ Changes pushed! Render will auto-deploy in 3-5 minutes."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 NEXT: Check Your Vercel Environment Variables"
echo ""
echo "1. Go to: https://vercel.com/dashboard"
echo "2. Click your project"
echo "3. Settings → Environment Variables"
echo "4. VERIFY these 3 variables exist:"
echo ""
echo "   NEXT_PUBLIC_API_URL = https://YOUR-BACKEND.onrender.com"
echo "   NEXT_PUBLIC_SUPABASE_URL = https://xxx.supabase.co"
echo "   NEXT_PUBLIC_SUPABASE_ANON_KEY = eyJhbG..."
echo ""
echo "5. If NEXT_PUBLIC_API_URL is wrong or missing:"
echo "   - Get your backend URL from: https://dashboard.render.com"
echo "   - Set it in Vercel (without /health or trailing slash)"
echo "   - Redeploy from Vercel dashboard"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 After Render redeploys (5 min), test:"
echo "   1. Visit: https://YOUR-BACKEND.onrender.com/health"
echo "   2. Should see: {\"status\": \"healthy\"}"
echo "   3. Then try your Vercel app!"
echo ""

