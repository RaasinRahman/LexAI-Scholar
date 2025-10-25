# Quick Fix Guide: Upload Failed Issue

## 🔧 What Was Done

I've fixed the upload functionality by:

1. **Enhanced error handling** - Now shows specific error messages instead of generic "upload failed"
2. **Added detailed logging** - Both frontend and backend now log every step
3. **Fixed environment variable handling** - Backend now handles both uppercase/lowercase Pinecone API key
4. **Better validation** - Clear messages for authentication and session issues

## ✅ Quick Test

### 1. Open Your Browser
Go to http://localhost:3000

### 2. Open Developer Console
Press `F12` or right-click → "Inspect" → go to "Console" tab

### 3. Try Uploading
1. Make sure you're **logged in**
2. Select a PDF file (must be under 50MB)
3. Click "Upload & Process Document"
4. **Watch the console** - you'll now see detailed logs

### 4. What You Should See

**✅ If it works:**
```
Starting upload: myfile.pdf
File size: 12345 bytes
Uploading to: http://localhost:8000/documents/upload
Upload response status: 200
Upload successful: {...}
```

**❌ If it fails, you'll see one of these:**

#### "Not authenticated. Please log in first."
→ **Fix**: Log out and log back in

#### "Authentication token missing. Please try logging in again."
→ **Fix**: 
1. Sign out
2. Clear browser cache (Ctrl+Shift+Delete)
3. Sign in again

#### "Vector service not configured"
→ **Fix**: Backend issue - see Backend Check below

#### Network error or CORS error
→ **Fix**: Make sure backend is running on port 8000

## 🔍 Backend Check

Run this command:
```bash
curl http://localhost:8000/health
```

Should show:
```json
{
  "status": "healthy",
  "supabase_configured": true,
  "vector_service_configured": true
}
```

If `vector_service_configured` is `false`:
1. Check your `backend/.env` file has: `PINECONE_API_KEY="..."`
2. Restart the backend server

## 🎯 Still Having Issues?

### Check Backend Logs
Look at the terminal where your backend is running. During upload, you should see:
```
Upload request from user: xxx
✓ File read: yourfile.pdf (12345 bytes)
→ Processing PDF: yourfile.pdf
✓ PDF processed: 15 chunks, 5000 characters
...
```

If you see an error here, copy the **full error message** with stack trace.

### Check Browser Network Tab
1. In DevTools, go to "Network" tab
2. Try uploading again
3. Find the `upload` request
4. Look at:
   - **Status Code** (should be 200)
   - **Response** tab (shows error details if failed)
   - **Headers** tab (check Authorization header is present)

### Test with Small PDF
Try uploading a simple, small PDF first (under 1MB) to rule out file-specific issues.

## 📋 Common Solutions

| Error | Solution |
|-------|----------|
| Session expired | Log out, clear cookies, log back in |
| "Failed to upload document" | Check backend logs for specific error |
| Nothing happens on click | Check console for JavaScript errors |
| "CORS error" | Make sure both servers are running (frontend :3000, backend :8000) |
| 401 Unauthorized | Your session expired - log in again |
| 500 Server Error | Check backend terminal for error details |

## 🚀 Next Steps

Once upload works:
1. Check **Document Library** - your file should appear
2. Try **Semantic Search** - search for content in your uploaded PDF
3. View **Vector Stats** to see your documents in the database

## 💡 Pro Tip

Keep the browser console open while using the app - it now shows helpful debug information for every action!

---

**Still stuck?** Share:
1. The complete error from browser console
2. Backend logs during upload attempt  
3. Result of the health check command above

