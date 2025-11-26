# 🚀 Quick Start - Deploy in 30 Minutes

## 📋 Checklist (Do these first!)

- [ ] GitHub account created
- [ ] Code pushed to GitHub
- [ ] Supabase keys ready
- [ ] Pinecone API key ready  
- [ ] OpenAI API key ready

---

## ⚡ Super Fast Deployment

### Step 1: Push to GitHub (5 min)
```bash
cd /Users/raasin/Desktop/LEXAI
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/lexai-scholar.git
git push -u origin main
```

### Step 2: Deploy Backend (10 min)
1. Go to https://render.com → Sign up with GitHub
2. New + → Web Service → Connect repo
3. Settings:
   - Root Directory: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add env vars: SUPABASE_URL, SUPABASE_KEY, PINECONE_API_KEY, OPENAI_API_KEY
5. Create Web Service
6. **Copy your backend URL**: `https://lexai-backend.onrender.com`

### Step 3: Deploy Frontend (10 min)
```bash
npm install -g vercel
cd LexAIScholar
vercel login
vercel
```

Then in Vercel dashboard → Settings → Environment Variables:
- `NEXT_PUBLIC_API_URL` = your backend URL
- `NEXT_PUBLIC_SUPABASE_URL` = your Supabase URL
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` = your Supabase anon key

Redeploy:
```bash
vercel --prod
```

### Step 4: Update CORS (5 min)
In `backend/main.py`, add your Vercel URL:
```python
allow_origins=[
    "http://localhost:3000",
    "https://lexai-scholar.vercel.app",  # Add this
]
```

Push to GitHub:
```bash
git add backend/main.py
git commit -m "Update CORS"
git push origin main
```

### Step 5: Test! 🎉
Visit `https://lexai-scholar.vercel.app`

---

## 🆘 Quick Fixes

**Backend not responding?**  
→ Wait 30 seconds (Render free tier wakes up)

**CORS errors?**  
→ Check Vercel URL is in backend/main.py CORS list

**Upload fails?**  
→ Check Render logs for specific error

---

## 📚 Full Guide
See `DEPLOY_STEPS.md` for detailed instructions.

