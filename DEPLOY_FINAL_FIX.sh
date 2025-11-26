#!/bin/bash

echo "🚀 Deploying Final Connection Fix..."
echo ""

cd /Users/raasin/Desktop/LEXAI

echo "✅ Updated CORS with your Vercel URLs"
echo ""
echo "Your URLs:"
echo "  Frontend: https://lexai-h2sfrssw1-raasinr-gmailcoms-projects.vercel.app"
echo "  Backend:  https://lexai-backend-5tqv.onrender.com"
echo ""

echo "📤 Pushing to GitHub (triggers Render deploy)..."
git add .
git commit -m "Fix: Add Vercel URLs to CORS configuration"
git push origin main

echo ""
echo "✅ Backend will redeploy in 3-5 minutes!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 CRITICAL: Now Set Vercel Environment Variables"
echo ""
echo "1. Go to: https://vercel.com/dashboard"
echo "2. Click your project"
echo "3. Settings → Environment Variables"
echo "4. Add/Update these 3 variables:"
echo ""
echo "   Variable 1:"
echo "   Name:  NEXT_PUBLIC_API_URL"
echo "   Value: https://lexai-backend-5tqv.onrender.com"
echo ""
echo "   Variable 2:"
echo "   Name:  NEXT_PUBLIC_SUPABASE_URL"
echo "   Value: [Your Supabase URL from dashboard]"
echo ""
echo "   Variable 3:"
echo "   Name:  NEXT_PUBLIC_SUPABASE_ANON_KEY"
echo "   Value: [Your Supabase ANON key]"
echo ""
echo "5. After saving, go to Deployments tab"
echo "6. Click ••• on latest deployment"
echo "7. Click 'Redeploy'"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Once both redeploy (5-10 min total):"
echo "   Visit: https://lexai-h2sfrssw1-raasinr-gmailcoms-projects.vercel.app"
echo "   Try to upload a document!"
echo ""

