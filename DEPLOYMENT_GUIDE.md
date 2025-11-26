# LexAI Scholar - Deployment Guide

## 🚀 Deployment Architecture

- **Frontend**: Vercel (Next.js)
- **Backend**: Render.com (FastAPI)
- **Database**: Supabase (already cloud-hosted)
- **Vector DB**: Pinecone (already cloud-hosted)
- **AI**: OpenAI (already cloud-hosted)

## 📝 Environment Variables Needed

### Backend (Render)
```
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-service-key
PINECONE_API_KEY=your-pinecone-key
OPENAI_API_KEY=your-openai-key
```

### Frontend (Vercel)
```
NEXT_PUBLIC_API_URL=https://lexai-backend.onrender.com
NEXT_PUBLIC_SUPABASE_URL=your-supabase-url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key
```

## 🔗 Deployment URLs

After deployment, your app will be available at:
- **Frontend**: https://lexai-scholar.vercel.app (or custom domain)
- **Backend API**: https://lexai-backend.onrender.com

## ⚙️ Post-Deployment Steps

1. Update CORS in backend with your Vercel URL
2. Test all features (upload, search, chat, case briefs)
3. Monitor logs on both Render and Vercel dashboards
4. Set up custom domain (optional)

## 💡 Tips

- **Render Free Tier**: Backend sleeps after 15 min inactivity (first request takes ~30s)
- **Upgrade to Render Starter ($7/mo)**: Always-on, faster response times
- **Vercel Free Tier**: Perfect for personal projects, 100GB bandwidth/month

