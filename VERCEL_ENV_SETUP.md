# 🎯 Vercel Environment Variables Setup

## Your App URLs
- **Frontend**: https://lexai-h2sfrssw1-raasinr-gmailcoms-projects.vercel.app
- **Backend**: https://lexai-backend-5tqv.onrender.com

---

## ⚙️ Step-by-Step: Set Vercel Environment Variables

### Step 1: Open Vercel Dashboard

1. Go to: https://vercel.com/dashboard
2. Find and click your project (lexai-scholar or similar name)
3. Click **"Settings"** tab (top menu)
4. Click **"Environment Variables"** (left sidebar)

---

### Step 2: Add Variable 1 - Backend API URL

Click **"Add New"** and enter:

**Name:**
```
NEXT_PUBLIC_API_URL
```

**Value:**
```
https://lexai-backend-5tqv.onrender.com
```

**Environments:** ✅ Check ALL THREE boxes:
- [x] Production
- [x] Preview
- [x] Development

Click **"Save"**

---

### Step 3: Add Variable 2 - Supabase URL

Click **"Add New"** and enter:

**Name:**
```
NEXT_PUBLIC_SUPABASE_URL
```

**Value:** Get from Supabase Dashboard
1. Go to: https://supabase.com/dashboard
2. Select your project
3. Click **"Settings"** (gear icon) → **"API"**
4. Copy the **"Project URL"** (looks like: `https://xxxxx.supabase.co`)

**Environments:** ✅ Check ALL THREE boxes

Click **"Save"**

---

### Step 4: Add Variable 3 - Supabase Anon Key

Click **"Add New"** and enter:

**Name:**
```
NEXT_PUBLIC_SUPABASE_ANON_KEY
```

**Value:** Get from Supabase Dashboard
1. Same Supabase Settings → API page
2. Find **"anon"** **"public"** section
3. Copy the key (starts with `eyJhbG...`)
4. ⚠️ **NOT** the "service_role" key!

**Environments:** ✅ Check ALL THREE boxes

Click **"Save"**

---

### Step 5: Redeploy

After adding all 3 variables:

1. Click **"Deployments"** tab (top menu)
2. Find the most recent deployment (top one)
3. Click the **three dots (•••)** on the right
4. Click **"Redeploy"**
5. Confirm the redeploy
6. Wait 2-3 minutes

---

## ✅ Verification

After redeployment completes:

1. Visit: https://lexai-h2sfrssw1-raasinr-gmailcoms-projects.vercel.app
2. Open browser console (F12)
3. Try to sign up / log in
4. Check console for errors

**Expected Result:**
- ✅ No CORS errors
- ✅ No "localhost:8000" requests
- ✅ Can create account
- ✅ Can upload documents

---

## 🔍 How to Check if Variables Are Set

In Vercel Dashboard → Settings → Environment Variables:

You should see:

| Name | Value (first few chars) | Environments |
|------|-------------------------|--------------|
| `NEXT_PUBLIC_API_URL` | `https://lexai-back...` | Production, Preview, Development |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://xxxxx.sup...` | Production, Preview, Development |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGc...` | Production, Preview, Development |

---

## 🆘 Troubleshooting

### Problem: Can't find Supabase keys

**Solution:**
1. Go to: https://supabase.com/dashboard/projects
2. Click your project
3. Click gear icon (Settings) → API
4. Copy from there

### Problem: Vercel still showing localhost:8000 in browser console

**Reason:** Environment variables not applied

**Solution:**
1. Make sure you clicked "Save" on each variable
2. Make sure you checked all 3 environment checkboxes
3. Must redeploy after adding variables
4. Clear browser cache and hard refresh (Ctrl+Shift+R)

### Problem: 401 Unauthorized errors

**Reason:** Wrong Supabase keys

**Solution:**
- Double-check you used **ANON key**, not service_role key
- Copy-paste carefully (no extra spaces)
- Redeploy after fixing

---

## 📋 Quick Checklist

- [ ] Backend CORS updated (main.py) ✅ Done automatically
- [ ] Backend pushed to GitHub and redeployed
- [ ] Vercel has `NEXT_PUBLIC_API_URL` = `https://lexai-backend-5tqv.onrender.com`
- [ ] Vercel has `NEXT_PUBLIC_SUPABASE_URL` = your Supabase URL
- [ ] Vercel has `NEXT_PUBLIC_SUPABASE_ANON_KEY` = your Supabase anon key
- [ ] All variables have all 3 environments checked
- [ ] Vercel redeployed after adding variables
- [ ] Tested app - can sign up
- [ ] Tested app - can upload PDFs
- [ ] Everything works! 🎉

