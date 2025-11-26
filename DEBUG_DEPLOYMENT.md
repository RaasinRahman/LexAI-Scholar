# 🔍 Debug Deployment - Step by Step

## Quick Checks

### 1. Get Your URLs
- **Frontend**: Check at https://vercel.com/dashboard
- **Backend**: Check at https://dashboard.render.com

Write them down:
- Frontend: `https://lexai-eight.vercel.app/`
- Backend: `https://lexai-backend-5tqv.onrender.com`

---

## 🔧 Step-by-Step Debugging

### Step 1: Test Backend is Working

Visit your backend URL + `/health`:
```
https://your-backend.onrender.com/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "supabase_configured": true,
  "vector_service_configured": true,
  "timestamp": "..."
}
```

**If you see an error or it takes 30+ seconds:**
- Backend is sleeping (Render free tier)
- Wait 30 seconds and try again

---

### Step 2: Check Vercel Environment Variables

1. Go to: https://vercel.com/dashboard
2. Click your project
3. Go to **Settings** → **Environment Variables**

**You MUST have these 3 variables:**

| Name | Value Example | Where to Get It |
|------|---------------|-----------------|
| `NEXT_PUBLIC_API_URL` | `https://lexai-backend.onrender.com` | Your Render backend URL |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxx.supabase.co` | Supabase dashboard |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbG...` | Supabase dashboard (ANON key, not service key!) |

**If any are missing or wrong:**
- Add/fix them
- Click "Redeploy" after saving

---

### Step 3: Check Render Environment Variables

1. Go to: https://dashboard.render.com
2. Click your `lexai-backend` service
3. Go to **Environment** tab

**You MUST have these 4 variables:**

| Key | Value Starts With | Where to Get It |
|-----|-------------------|-----------------|
| `SUPABASE_URL` | `https://` | Supabase dashboard |
| `SUPABASE_KEY` | `eyJhbG...` | Supabase **Service Role** key (longer key) |
| `PINECONE_API_KEY` | `pcsk_...` | Pinecone dashboard |
| `OPENAI_API_KEY` | `sk-...` | OpenAI dashboard |

**If any are missing:**
- Add them
- Backend will auto-redeploy

---

### Step 4: Check CORS Configuration

Your backend needs to allow your Vercel URL.

**Check backend/main.py** - Should include YOUR Vercel URL:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://your-actual-vercel-url.vercel.app",  # ← YOUR URL HERE
        "https://*.vercel.app",
    ],
    ...
)
```

**If your URL is NOT in the list:**
1. Update `backend/main.py`
2. Git commit and push
3. Render will auto-redeploy

---

### Step 5: Check Browser Console for Errors

1. Open your Vercel app: `https://your-app.vercel.app`
2. Press **F12** (or right-click → Inspect)
3. Click **Console** tab
4. Try to upload a document or search
5. Look for errors

**Common errors you might see:**

❌ **CORS Error:**
```
Access to fetch at 'https://backend...' blocked by CORS policy
```
→ Fix: Update CORS in backend/main.py (see Step 4)

❌ **404 Not Found:**
```
GET https://localhost:8000/... 404
```
→ Fix: Frontend still pointing to localhost, not your Render URL
→ Check Vercel env vars (Step 2)

❌ **Unauthorized / 401:**
```
Failed to fetch: 401 Unauthorized
```
→ Fix: Supabase keys are wrong
→ Check env vars (Steps 2 & 3)

---

### Step 6: Check Render Logs

1. Go to: https://dashboard.render.com
2. Click `lexai-backend`
3. Click **Logs** tab
4. Try to upload a document in your app
5. Watch for errors in logs

**Look for:**

✅ **Good signs:**
```
[SUCCESS] Vector service initialized
[SUCCESS] RAG service initialized
POST /documents/upload
```

❌ **Bad signs:**
```
[ERROR] Failed to initialize
KeyError: 'OPENAI_API_KEY'
Connection refused
```
→ Missing environment variables (Step 3)

---

## 🎯 Most Common Issues

### Issue #1: Frontend pointing to localhost

**Symptom:** Nothing works, browser console shows `localhost:8000`

**Fix:**
1. Vercel Dashboard → Settings → Environment Variables
2. Set `NEXT_PUBLIC_API_URL` to your Render URL
3. Redeploy

### Issue #2: CORS blocking requests

**Symptom:** Browser console shows CORS errors

**Fix:**
1. Edit `backend/main.py`
2. Add your Vercel URL to `allow_origins`
3. Git push (Render auto-deploys)

### Issue #3: Missing environment variables

**Symptom:** Backend logs show "not configured" or KeyError

**Fix:**
1. Add missing variables in Render Dashboard
2. Backend auto-redeploys

### Issue #4: Backend sleeping (Render free tier)

**Symptom:** First request takes 30+ seconds, then works

**Not really a problem!** Just wait. Or upgrade to $7/mo for always-on.

---

## ✅ Quick Test Checklist

Run through these in order:

- [ ] Backend health endpoint works: `https://your-backend.onrender.com/health`
- [ ] Vercel has `NEXT_PUBLIC_API_URL` pointing to Render URL
- [ ] Vercel has correct Supabase URL and ANON key
- [ ] Render has all 4 environment variables (Supabase, Pinecone, OpenAI)
- [ ] Backend CORS includes your Vercel URL
- [ ] Browser console shows NO CORS errors
- [ ] Can sign up/log in to app
- [ ] Can upload a PDF

---

## 🆘 If Still Not Working

**Send me:**
1. Your Vercel URL
2. Your Render backend URL
3. Screenshot of browser console (F12)
4. Screenshot of Render logs

I'll help you debug!

