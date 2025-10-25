# 🚀 LexAI Scholar - Quick Start

## 30-Second Setup

### Terminal 1 - Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

### Terminal 2 - Frontend
```bash
cd LexAIScholar
npm install
npm run dev
```

### Terminal 3 - Quick Scripts (Optional)
```bash
# Make scripts executable
chmod +x start_backend.sh start_frontend.sh

# Then use:
./start_backend.sh  # Terminal 1
./start_frontend.sh # Terminal 2
```

---

## 🔑 Environment Setup

### Backend: `backend/.env`
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
PINECONE_API_KEY=pcsk_6uGvNp_3XAvNGrsf3LKYPzKq42ovqnHatj3J4RJzdx6xhmawsj9jza7K1nskPxsEQrDkfo
```

### Frontend: `LexAIScholar/.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_key
```

---

## 🎯 URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## ✅ First Use

1. Visit http://localhost:3000
2. Click "Sign Up" and create account
3. Go to "📤 Upload" tab
4. Upload a PDF document
5. Go to "🔍 Search" tab
6. Search with natural language

---

## 📦 What's Included

✅ PDF text extraction (PyPDF2 + pdfplumber)  
✅ Intelligent chunking (1000 char chunks, 200 overlap)  
✅ AI embeddings (sentence-transformers)  
✅ Vector database (Pinecone - auto-configured!)  
✅ Semantic search (not keyword-based)  
✅ Beautiful UI (Next.js + Tailwind)  
✅ User authentication (Supabase)  
✅ Drag-and-drop upload  
✅ Real-time progress tracking  
✅ Document library management  

---

## 🎓 Example Searches

Try these semantic queries:
- "What are the main legal arguments?"
- "contract terms and obligations"
- "precedents and case law"
- "key findings and conclusions"
- "plaintiff's claims and defenses"

---

## 📚 Documentation

- **Full Setup Guide:** `PDF_VECTOR_SEARCH_SETUP.md`
- **Testing Guide:** `TESTING_GUIDE.md`
- **This File:** Quick reference

---

## ⚡ Pro Tips

1. **First upload is slow** - Downloads embedding model (~80MB)
2. **No Pinecone setup needed** - Index created automatically
3. **Search is semantic** - "obligations" matches "duties"
4. **Results are scored** - Higher % = better match
5. **User-isolated** - You only see your documents

---

## 🐛 Troubleshooting

**Backend won't start?**
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

**Frontend won't start?**
- Install dependencies: `npm install`
- Check Node version: `node --version` (need 18+)

**Upload fails?**
- Ensure backend is running
- Check file is a PDF
- Max file size: 50MB

**Search returns nothing?**
- Upload at least one document first
- Try a different query
- Check document has text (not scanned image)

---

## 🎉 You're Ready!

Everything is configured and ready to use. Just start both servers and begin uploading PDFs!

**Questions?** Check the full guides:
- `PDF_VECTOR_SEARCH_SETUP.md` - Detailed setup
- `TESTING_GUIDE.md` - Testing checklist

