# 🚀 LexAI Scholar - Complete Deployment Steps

Follow these steps **in order** to deploy your app to production.

---

## ⚠️ BEFORE YOU START

### Collect Your API Keys

You'll need these keys. Gather them now:

1. **Supabase** (https://supabase.com/dashboard)
   - Project URL: `https://xxxxx.supabase.co`
   - Service Role Key (from Settings → API)
   - Anon/Public Key (from Settings → API)

2. **Pinecone** (https://app.pinecone.io)
   - API Key (from API Keys section)

3. **OpenAI** (https://platform.openai.com/api-keys)
   - API Key: `sk-...`

4. **GitHub Account** (free)
   - Make sure you have a GitHub account

---

## 🎯 STEP 1: Prepare Your Code for Deployment

### 1.1 Initialize Git (if not already done)

```bash
cd /Users/raasin/Desktop/LEXAI

# Check if git is initialized
git status

# If not initialized, run:
git init
git add .
git commit -m "Initial commit - Ready for deployment"
```

### 1.2 Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `lexai-scholar`
3. Make it **Private** (recommended) or Public
4. **DO NOT** initialize with README (we already have code)
5. Click **Create repository**

### 1.3 Push Your Code to GitHub

Copy the commands from GitHub (replace with your username):

```bash
git remote add origin https://github.com/YOUR_USERNAME/lexai-scholar.git
git branch -M main
git push -u origin main
```

✅ **Verify**: Refresh GitHub page - you should see your code

---

## 🔧 STEP 2: Deploy Backend to Render

### 2.1 Create Render Account

1. Go to https://render.com
2. Click **Sign Up**
3. Sign up with **GitHub** (easiest way)
4. Authorize Render to access your repositories

### 2.2 Create New Web Service

1. In Render dashboard, click **New +** → **Web Service**
2. Click **Connect a repository**
3. Find `lexai-scholar` and click **Connect**

### 2.3 Configure the Service

**Basic Settings:**
- **Name**: `lexai-backend`
- **Region**: `Oregon (US West)` or closest to you
- **Branch**: `main`
- **Root Directory**: `backend`
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

**Instance Type:**
- Select **Free** (good to start)

### 2.4 Add Environment Variables

Scroll down to **Environment Variables** section and add these:

| Key | Value |
|-----|-------|
| `SUPABASE_URL` | Your Supabase URL |
| `SUPABASE_KEY` | Your Supabase **Service Role** key |
| `PINECONE_API_KEY` | Your Pinecone API key |
| `OPENAI_API_KEY` | Your OpenAI API key (starts with sk-) |
| `PYTHON_VERSION` | `3.11.0` |

### 2.5 Deploy!

1. Click **Create Web Service**
2. Wait 5-10 minutes for initial build
3. Watch the logs - you should see:
   ```
   [SUCCESS] Vector service initialized successfully
   [SUCCESS] RAG service initialized successfully
   ```

### 2.6 Get Your Backend URL

1. Once deployed, you'll see: **Your service is live 🎉**
2. Copy the URL (looks like: `https://lexai-backend.onrender.com`)
3. **Save this URL** - you'll need it for frontend!

✅ **Test Backend**: Visit `https://your-backend-url.onrender.com/health`
   - Should see: `{"status": "healthy"}`

---

## 🎨 STEP 3: Deploy Frontend to Vercel

### 3.1 Install Vercel CLI

```bash
npm install -g vercel
```

### 3.2 Login to Vercel

```bash
vercel login
```

Choose login method (Email or GitHub recommended)

### 3.3 Deploy Frontend

```bash
cd /Users/raasin/Desktop/LEXAI/LexAIScholar
vercel
```

Answer the prompts:
- **Set up and deploy**: `Y`
- **Which scope**: Select your account
- **Link to existing project**: `N`
- **What's your project's name**: `lexai-scholar`
- **In which directory is your code located**: `./`
- **Want to override settings**: `N`

Wait 2-3 minutes for deployment...

### 3.4 Get Your Frontend URL

After deployment completes, you'll see:
```
✅ Production: https://lexai-scholar.vercel.app
```

**Save this URL!**

### 3.5 Add Environment Variables

1. Go to https://vercel.com/dashboard
2. Click on your project `lexai-scholar`
3. Go to **Settings** → **Environment Variables**
4. Add these variables:

| Name | Value |
|------|-------|
| `NEXT_PUBLIC_API_URL` | `https://lexai-backend.onrender.com` (YOUR backend URL) |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase **Anon/Public** key |

5. Click **Save**

### 3.6 Redeploy with Environment Variables

```bash
vercel --prod
```

Wait 2-3 minutes for redeployment...

✅ **Your frontend is now live!**

---

## 🔗 STEP 4: Connect Frontend and Backend (CORS)

### 4.1 Update CORS in Backend

1. Open `backend/main.py` in your editor
2. Find the CORS configuration (around line 24)
3. Update it with your Vercel URL:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://lexai-scholar.vercel.app",  # YOUR Vercel URL
        "https://lexai-scholar-*.vercel.app",  # Preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.2 Push Changes to GitHub

```bash
cd /Users/raasin/Desktop/LEXAI
git add backend/main.py
git commit -m "Update CORS for production"
git push origin main
```

Render will automatically detect the push and redeploy! (takes 3-5 min)

---

## ✅ STEP 5: Test Your Deployed App

### 5.1 Visit Your App

Open your browser and go to:
```
https://lexai-scholar.vercel.app
```

### 5.2 Test Complete Flow

1. **Sign Up** - Create a test account
2. **Upload PDF** - Upload a sample legal document
3. **Search** - Try semantic search
4. **Ask Questions** - Test the AI chat
5. **Generate Case Brief** - Create a case brief

### 5.3 Check for Errors

If something doesn't work:

1. **Check Browser Console** (F12)
   - Look for CORS errors
   - Look for network errors

2. **Check Render Logs**
   - Go to Render dashboard
   - Click your service
   - Click **Logs** tab

3. **Check Vercel Logs**
   - Go to Vercel dashboard
   - Click your project
   - Click **Deployments** → Latest deployment → **View Logs**

---

## 🎉 SUCCESS! Your App is Live!

**Your URLs:**
- 🎨 Frontend: `https://lexai-scholar.vercel.app`
- 🔧 Backend API: `https://lexai-backend.onrender.com`

---

## 🚨 Common Issues & Solutions

### Issue: "Backend not responding" / Long wait times

**Cause**: Render free tier sleeps after 15 min of inactivity

**Solutions**:
1. Wait ~30 seconds for first request (it's waking up)
2. Upgrade to Render Starter ($7/mo) for always-on

### Issue: CORS errors in browser

**Cause**: Backend doesn't allow your frontend domain

**Solution**:
1. Check `backend/main.py` CORS settings
2. Make sure your Vercel URL is in `allow_origins`
3. Push changes to GitHub
4. Wait for Render to redeploy

### Issue: "Failed to upload document"

**Possible causes**:
1. File too large (Render free has 100MB limit)
2. Missing environment variables
3. Pinecone or Supabase not configured

**Solution**:
1. Check Render logs for specific error
2. Verify all environment variables are set
3. Try smaller PDF file first

### Issue: Environment variables not working

**Solution**:
1. After adding env vars, always redeploy:
   - **Vercel**: Run `vercel --prod`
   - **Render**: Click "Manual Deploy" → "Deploy latest commit"

---

## 🔄 Future Deployments

After initial setup, deploying updates is easy:

### Quick Deploy Script

```bash
cd /Users/raasin/Desktop/LEXAI
./deploy.sh
```

Or manually:

```bash
# Backend: Just push to GitHub
git add .
git commit -m "Update features"
git push origin main
# Render auto-deploys!

# Frontend: Run vercel
cd LexAIScholar
vercel --prod
```

---

## 📊 Monitoring Your App

### Render Dashboard
- View backend logs
- See API requests
- Monitor CPU/memory usage
- Check for errors

### Vercel Dashboard
- View build logs
- See deployment history
- Monitor bandwidth usage
- Check analytics

---

## 💰 Cost Summary

**Current Setup (Free Tier):**
- Vercel: Free
- Render: Free (with sleep)
- Total: **$0/month**

**Recommended Production Setup:**
- Vercel Hobby: Free
- Render Starter: $7/month
- Total: **$7/month**

Plus your existing services:
- Supabase: Free tier is generous
- Pinecone: Free tier (100k vectors)
- OpenAI: Pay per use (~$1-5/month light usage)

---

## 🎯 Next Steps

After successful deployment:

1. ✅ Set up custom domain (optional)
2. ✅ Configure monitoring/alerts
3. ✅ Set up automated backups
4. ✅ Add your team members
5. ✅ Share with users!

---

## 📞 Need Help?

If you get stuck:

1. Check this guide carefully
2. Check the logs (Render + Vercel)
3. Google the specific error message
4. Check Render/Vercel documentation

---

**🎉 Congratulations on deploying your app!**

