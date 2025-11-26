#!/bin/bash

echo "🔍 Checking Your Deployment Configuration..."
echo ""

# Check if backend/main.py exists and show CORS config
if [ -f "backend/main.py" ]; then
    echo "📋 CORS Configuration in backend/main.py:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    grep -A 10 "allow_origins=" backend/main.py | head -15
    echo ""
else
    echo "❌ backend/main.py not found"
fi

echo ""
echo "📝 IMPORTANT CHECKLIST:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1️⃣  Get your URLs:"
echo "   Frontend: https://vercel.com/dashboard"
echo "   Backend:  https://dashboard.render.com"
echo ""
echo "2️⃣  Test backend health:"
echo "   Visit: https://YOUR-BACKEND.onrender.com/health"
echo "   Should see: {\"status\": \"healthy\"}"
echo ""
echo "3️⃣  Check Vercel Environment Variables:"
echo "   ✓ NEXT_PUBLIC_API_URL (your Render backend URL)"
echo "   ✓ NEXT_PUBLIC_SUPABASE_URL"
echo "   ✓ NEXT_PUBLIC_SUPABASE_ANON_KEY"
echo ""
echo "4️⃣  Check Render Environment Variables:"
echo "   ✓ SUPABASE_URL"
echo "   ✓ SUPABASE_KEY (Service Role key)"
echo "   ✓ PINECONE_API_KEY"
echo "   ✓ OPENAI_API_KEY"
echo ""
echo "5️⃣  Update CORS (if needed):"
echo "   Add your Vercel URL to backend/main.py allow_origins"
echo ""
echo "6️⃣  Check browser console (F12) for errors"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 See DEBUG_DEPLOYMENT.md for detailed instructions"
echo ""

