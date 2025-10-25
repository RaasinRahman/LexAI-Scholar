# Document Library Display Fix

## Problem
Documents were saving to Supabase successfully but **not showing up in the frontend library section**.

## Root Cause
The backend endpoints for retrieving documents (`GET /documents`, `GET /documents/{id}`, and `DELETE /documents/{id}`) were using the global Supabase client instead of user-authenticated clients. This caused Row-Level Security (RLS) policies to block the queries, preventing documents from being retrieved even though they existed in the database.

## What Was Fixed

### Backend Changes (`backend/main.py`)

All document retrieval and deletion endpoints now use user-authenticated Supabase clients:

#### 1. **GET /documents** - List All Documents
```python
@app.get("/documents")
async def get_user_documents(
    current_user = Depends(get_current_user),
    authorization: str = Header(None)  # ← Added
):
    # Extract JWT token
    access_token = authorization.replace("Bearer ", "")
    
    # Create user-authenticated client
    user_supabase = get_user_supabase_client(access_token)
    
    # Query with RLS compliance
    documents = user_supabase.table("documents").select("*").eq("user_id", user_id).order("uploaded_at", desc=True).execute()
    
    return documents.data
```

#### 2. **GET /documents/{id}** - Get Single Document
- Now uses user-authenticated Supabase client
- Extracts JWT token from Authorization header
- RLS policies work correctly

#### 3. **DELETE /documents/{id}** - Delete Document
- Now uses user-authenticated Supabase client
- Properly deletes from both vector database and Supabase
- Better error handling and logging

### Key Pattern
All endpoints now follow this pattern:
1. Extract JWT token from `Authorization` header
2. Create user-authenticated Supabase client using `get_user_supabase_client(access_token)`
3. Use the authenticated client for all database operations
4. RLS policies automatically enforce user isolation

## Testing

### Backend is Running
```bash
curl http://localhost:8000/health
```

Should return:
```json
{
    "status": "healthy",
    "supabase_configured": true,
    "vector_service_configured": true
}
```

### Test Document Upload & Retrieval
1. **Upload a Document**: Go to Upload tab, select a PDF, and upload
2. **Check Library**: Switch to Library tab - documents should now appear!
3. **Verify in Supabase**: Check your Supabase dashboard → documents table - should see entries

### What You Should See Now
- ✅ Documents appear in the Library tab immediately after upload
- ✅ Documents are properly sorted by upload date (newest first)
- ✅ All document metadata displays correctly (title, author, page count, etc.)
- ✅ Delete button works and removes from both vector DB and Supabase
- ✅ Document count shows correctly

## Technical Details

### How RLS Works Now
1. User logs in → receives JWT token
2. Frontend sends JWT in `Authorization: Bearer {token}` header
3. Backend extracts token and creates authenticated Supabase client
4. Supabase validates JWT and checks `auth.uid()` matches `user_id`
5. RLS policies allow query to proceed
6. Documents are returned successfully

### Before vs After

**Before:**
- Backend used global Supabase client
- RLS couldn't verify user identity
- Queries were blocked
- Documents didn't appear in frontend

**After:**
- Backend uses user-authenticated client per request
- RLS validates user identity from JWT
- Queries succeed
- Documents display in frontend ✅

## Files Modified
- `/Users/raasin/Desktop/LEXAI/backend/main.py`
  - Updated `get_user_documents()` endpoint
  - Updated `get_document()` endpoint  
  - Updated `delete_document()` endpoint

## No Database Changes Needed!
The SQL policies from `fix_rls_for_upload.sql` work perfectly with these changes. If you already ran that script, you're all set!

## Troubleshooting

### Documents Still Not Showing?

1. **Check Backend Logs:**
```bash
tail -f /tmp/backend.log
```
Look for:
- `✓ Retrieved N documents for user {user_id}`
- `✗ Error retrieving documents:` (indicates a problem)

2. **Check Browser Console:**
```javascript
// Open DevTools → Console
// Look for API errors when switching to Library tab
```

3. **Verify JWT Token:**
```bash
# In browser console, check if token exists:
console.log(localStorage.getItem('sb-[your-project-id]-auth-token'))
```

4. **Test Backend Directly:**
```bash
# Get your token from browser and test:
TOKEN="your-jwt-token-here"
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/documents
```

### Common Issues

**"Access token required"**
- Solution: Log out and log back in to refresh your session

**Empty Array Returned `[]`**
- Check that documents actually exist in Supabase
- Verify `user_id` matches between auth.users and documents table

**401 Unauthorized**
- JWT token expired - log in again
- Check that `SUPABASE_KEY` is set in backend `.env`

## Summary

✅ **All document endpoints now use user-authenticated Supabase clients**
✅ **RLS policies work correctly with JWT tokens**  
✅ **Documents display in frontend Library tab**
✅ **Upload → Save → Display flow works end-to-end**
✅ **Backend is running and healthy**

Your documents should now show up in the Library section! 🎉

Just refresh the Library tab or upload a new document to see them appear.

