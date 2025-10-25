# LexAI Scholar - Testing Guide

## 🧪 End-to-End Testing Checklist

### Pre-Testing Setup

1. ✅ **Backend Requirements Installed**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. ✅ **Frontend Dependencies Installed**
   ```bash
   cd LexAIScholar
   npm install
   ```

3. ✅ **Environment Variables Configured**
   - Backend: `backend/.env` with Supabase and Pinecone credentials
   - Frontend: `LexAIScholar/.env.local` with API URL and Supabase credentials

---

## 🚀 Step-by-Step Testing

### Step 1: Start Backend (Terminal 1)

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
Loading embedding model...
Initializing Pinecone...
Creating new Pinecone index: lexai-documents  (or "Connecting to existing index")
✓ Vector service initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Verify:**
- Visit: http://localhost:8000
- Should see: `{"message": "LexAI Scholar API - Cloud Service Configured Successfully!", ...}`

- Visit: http://localhost:8000/health
- Should see: `{"status": "healthy", "vector_service_configured": true, ...}`

- Visit: http://localhost:8000/docs
- Should see interactive API documentation

### Step 2: Start Frontend (Terminal 2)

```bash
cd LexAIScholar
npm run dev
```

**Expected Output:**
```
✓ Ready in 2s
○ Local:        http://localhost:3000
```

**Verify:**
- Visit: http://localhost:3000
- Should see the LexAI Scholar landing page

---

## 📝 Functional Testing

### Test 1: Authentication ✅

1. Click "Sign Up" button
2. Enter:
   - Email: test@example.com
   - Password: TestPassword123
   - Full Name: Test User
3. Click "Create Account"
4. **Expected:** Redirect to dashboard with welcome message

### Test 2: PDF Upload ✅

1. Go to "📤 Upload" tab
2. Click the upload area or drag a PDF file
3. Click "Upload & Process Document"
4. **Expected:**
   - Progress bar shows 0% → 100%
   - "Processing..." message appears
   - Success message with document stats:
     - Filename
     - Chunk count
     - Character count
     - Page count
   - After 2 seconds, automatically switches to "📚 Library" tab

**Backend Console Output:**
```
Processing PDF: your-document.pdf
Generating embeddings for X chunks...
Uploading Y vectors to Pinecone...
```

### Test 3: Document Library ✅

1. Go to "📚 Library" tab
2. **Expected:**
   - See list of uploaded documents
   - Each document shows:
     - Title/filename
     - Author (if available)
     - Page count
     - Chunk count
     - Character count
     - Upload timestamp
   - Delete button is visible

3. Click refresh button
4. **Expected:** List updates with latest documents

### Test 4: Semantic Search ✅

1. Go to "🔍 Search" tab
2. Enter query: "What are the key findings?"
3. Click "Search" button
4. **Expected:**
   - "Searching..." loading state
   - Results appear ranked by relevance
   - Each result shows:
     - Relevance score (50-100%)
     - Score label (Excellent/Good/Fair Match)
     - Document title/filename
     - Author
     - Chunk number
     - Text excerpt with potential highlighting
   - Search time displayed (e.g., "Found 5 results in 234ms")

### Test 5: Search Variations ✅

Try these queries to test semantic understanding:

1. **Exact phrase:** "contract obligations"
   - Should find exact matches

2. **Semantic query:** "duties under agreement"
   - Should match "obligations" and "contract" content

3. **Question format:** "What are the main arguments?"
   - Should find argumentative sections

4. **Concept search:** "legal precedents"
   - Should find case law references

### Test 6: Copy Functionality ✅

1. In search results, click "📋 Copy" on a result
2. **Expected:** Text copied to clipboard (check by pasting)

### Test 7: Delete Document ✅

1. Go to "📚 Library" tab
2. Click delete button on a document
3. Confirm deletion
4. **Expected:**
   - Confirmation dialog appears
   - Document removed from list
   - Document also deleted from Pinecone

---

## 🔍 Backend API Testing

### Using curl

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Upload Document (requires auth token)
```bash
curl -X POST http://localhost:8000/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@path/to/document.pdf"
```

#### Search Documents
```bash
curl -X POST http://localhost:8000/documents/search \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "top_k": 5}'
```

#### List Documents
```bash
curl http://localhost:8000/documents \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Vector Stats
```bash
curl http://localhost:8000/vector-stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🐛 Common Issues and Solutions

### Issue: "Failed to initialize vector service"

**Cause:** Pinecone API key is invalid or internet connection issue

**Solution:**
- Verify Pinecone API key in `.env`
- Check internet connection
- Wait a moment and restart backend (first run downloads ~80MB embedding model)

### Issue: "Failed to upload document"

**Cause:** Backend not running or CORS issue

**Solution:**
- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify backend CORS settings allow `http://localhost:3000`

### Issue: Search returns no results

**Cause:** No documents uploaded or min_score too high

**Solution:**
- Upload at least one PDF document
- Try a more general query
- Check if document actually has relevant content

### Issue: "Only PDF files are supported"

**Cause:** Trying to upload non-PDF file

**Solution:**
- Only PDF files are currently supported
- Ensure file has `.pdf` extension

### Issue: Slow first upload

**Cause:** Embedding model needs to download on first run

**Solution:**
- First upload may take longer (~1-2 minutes)
- Subsequent uploads will be faster
- Model is cached after first download

---

## ✅ Expected Performance

### Upload Performance
- Small PDF (1-10 pages): ~5-15 seconds
- Medium PDF (10-50 pages): ~15-45 seconds  
- Large PDF (50-100 pages): ~45-90 seconds

*Time includes: text extraction, chunking, embedding generation, and Pinecone upload*

### Search Performance
- Typical search: 200-500ms
- Includes: query embedding generation + Pinecone vector search

### Embedding Model Download (First Run Only)
- Model: all-MiniLM-L6-v2
- Size: ~80MB
- Time: 1-3 minutes depending on internet speed

---

## 📊 Pinecone Verification

### Check Pinecone Dashboard

1. Go to: https://app.pinecone.io/
2. Login with your Pinecone account
3. Navigate to "Indexes"
4. Verify:
   - Index name: `lexai-documents`
   - Status: `Ready`
   - Metric: `cosine`
   - Dimension: `384`
   - Total vectors: Should increase as you upload documents

### Query Pinecone Stats via API

```bash
curl http://localhost:8000/vector-stats \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Expected response:
```json
{
  "total_vectors": 150,
  "dimension": 384,
  "index_fullness": 0.0
}
```

---

## 🎯 Feature Verification Matrix

| Feature | Component | Status | Notes |
|---------|-----------|--------|-------|
| PDF Upload | PDFUpload.tsx | ✅ | Drag-and-drop working |
| Text Extraction | pdf_service.py | ✅ | PyPDF2 + pdfplumber |
| Chunking | pdf_service.py | ✅ | 1000 chars, 200 overlap |
| Embeddings | vector_service.py | ✅ | all-MiniLM-L6-v2 |
| Pinecone Index | vector_service.py | ✅ | Auto-created |
| Vector Storage | vector_service.py | ✅ | User-isolated |
| Semantic Search | SemanticSearch.tsx | ✅ | Natural language |
| Document Library | DocumentLibrary.tsx | ✅ | CRUD operations |
| Metadata Extraction | pdf_service.py | ✅ | Title, author, pages |
| Authentication | AuthContext.tsx | ✅ | Supabase Auth |
| API Client | lib/api.ts | ✅ | Type-safe |

---

## 🚦 System Health Indicators

### Backend Healthy When:
- ✅ `/health` returns 200 status
- ✅ `vector_service_configured: true`
- ✅ `supabase_configured: true`
- ✅ Console shows "Vector service initialized successfully"

### Frontend Healthy When:
- ✅ Page loads without errors
- ✅ No red errors in browser console
- ✅ Can navigate between tabs
- ✅ Upload button is enabled

### Pinecone Healthy When:
- ✅ Index exists in dashboard
- ✅ Uploads succeed
- ✅ Search returns results
- ✅ Vector stats API works

---

## 📋 Test Completion Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Can create account
- [ ] Can login
- [ ] Can upload PDF
- [ ] Upload shows progress
- [ ] Upload shows success message
- [ ] Document appears in library
- [ ] Can search uploaded document
- [ ] Search returns relevant results
- [ ] Results show correct relevance scores
- [ ] Can copy search result text
- [ ] Can delete document
- [ ] Can logout
- [ ] Pinecone index exists
- [ ] No console errors
- [ ] No linter errors

---

## 🎉 Success Criteria

Your system is **fully operational** if:

1. ✅ You can upload a PDF and see it processed
2. ✅ The document appears in your library
3. ✅ You can search and get relevant results
4. ✅ Results have reasonable relevance scores (>50%)
5. ✅ No errors in browser console or backend logs
6. ✅ Pinecone dashboard shows vectors

**Congratulations! Your AI-powered semantic search system is working!** 🎊

