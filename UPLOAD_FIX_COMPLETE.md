# Document Upload Fix - Complete Guide

## Problem
Documents were being uploaded to the vector database (Pinecone) but not being saved to Supabase, so they weren't showing up in the Document Library section of the app.

## Root Cause
The backend code was silently catching Supabase insertion errors and only printing warnings to the console instead of failing the upload. Additionally, the backend wasn't properly authenticating with Supabase for Row-Level Security (RLS) operations.

## What Was Fixed

### 1. Backend Error Handling (`backend/main.py`)
- ✅ **Removed silent error handling** - Now throws proper HTTP errors if Supabase insertion fails
- ✅ **Added automatic rollback** - If Supabase fails, the document is removed from the vector database
- ✅ **Improved error messages** - Better debugging information for policy/permission issues
- ✅ **Added validation** - Ensures Supabase is configured before attempting upload

### 2. Authentication for RLS (`backend/main.py`)
- ✅ **Created `get_user_supabase_client()` function** - Uses user's JWT token for database operations
- ✅ **Updated upload endpoint** - Now uses user-authenticated Supabase client
- ✅ **Proper token handling** - Extracts and passes user's access token for RLS compliance

### 3. Database Policies (`backend/fix_rls_for_upload.sql`)
- ✅ **Created simplified RLS policies** - Clear, permissive policies for authenticated users
- ✅ **Proper permissions** - Ensures authenticated users can insert their own documents

## Setup Instructions

### Step 1: Update Database Policies (Required)
Run the RLS policy fix script in your Supabase SQL Editor:

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Open `/Users/raasin/Desktop/LEXAI/backend/fix_rls_for_upload.sql`
4. Copy and paste the contents into the SQL Editor
5. Click "Run" to execute

This will:
- Drop old conflicting policies
- Create new, simplified policies that work with user JWT tokens
- Verify permissions are set correctly

### Step 2: Restart the Backend
```bash
cd /Users/raasin/Desktop/LEXAI
./start_backend.sh
```

### Step 3: Test Upload
1. Make sure you're logged in to the frontend
2. Try uploading a PDF document
3. Check that it appears in the Document Library immediately after upload

## Verification

### Success Indicators
✅ Upload shows "Upload Successful!" message
✅ Document appears in the Document Library section
✅ Backend logs show: "✓ Document metadata saved to Supabase: [document-id]"
✅ Can search the document using semantic search

### Error Messages (If Still Failing)

**"Database permission error. Please ensure RLS policies are set up correctly."**
- Solution: Run the `fix_rls_for_upload.sql` script in Supabase

**"Database not configured. Cannot store document metadata."**
- Solution: Check that `SUPABASE_URL` and `SUPABASE_KEY` are set in your backend `.env` file

**"Access token required"**
- Solution: Ensure you're logged in and the session is valid. Try logging out and back in.

## Technical Details

### How It Works Now
1. User uploads PDF through frontend
2. Frontend sends file + JWT access token to backend
3. Backend processes PDF and stores in vector database (Pinecone)
4. Backend creates user-authenticated Supabase client with JWT token
5. Backend inserts document metadata into Supabase `documents` table
6. RLS policy checks that `auth.uid() = user_id` (automatically handled by JWT)
7. If Supabase insert fails, backend automatically rolls back vector database entries
8. Frontend receives success/error and updates Document Library

### Files Modified
- `backend/main.py` - Added user authentication for Supabase, improved error handling
- `backend/fix_rls_for_upload.sql` - New file with simplified RLS policies

### Key Changes
```python
# New helper function for user-authenticated Supabase operations
def get_user_supabase_client(access_token: str) -> Client:
    user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    user_client.postgrest.auth(access_token)
    return user_client

# Upload now uses user-authenticated client
user_supabase = get_user_supabase_client(access_token)
result = user_supabase.table("documents").insert(doc_metadata).execute()
```

## Troubleshooting

### Documents Still Not Showing Up?

1. **Check backend logs:**
```bash
cd /Users/raasin/Desktop/LEXAI/backend
tail -f server.log
```

2. **Verify Supabase connection:**
```bash
curl http://localhost:8000/health
```
Should show `"supabase_configured": true`

3. **Check RLS policies in Supabase:**
- Go to Supabase Dashboard → Database → Policies
- Look for `documents` table
- Should have 4 policies: select, insert, update, delete
- All should be enabled

4. **Verify user is authenticated:**
- Frontend: Check browser console for auth errors
- Backend: Check logs for "Authentication failed" messages

5. **Test with Supabase SQL Editor:**
```sql
-- Should return your documents
SELECT * FROM documents WHERE user_id = auth.uid();
```

## Need More Help?

If uploads are still failing after following these steps:

1. Check the backend terminal output when uploading
2. Look for specific error messages
3. Verify that `SUPABASE_KEY` in your `.env` file is either:
   - The **anon** key (public) - RLS policies will be enforced
   - The **service_role** key - Bypasses RLS (use with caution)

The fix is designed to work with the **anon key** by properly authenticating with the user's JWT token.

## Summary

✅ Backend now properly handles Supabase errors
✅ User authentication integrated for RLS compliance
✅ Automatic rollback prevents orphaned vector database entries
✅ Clear error messages help with troubleshooting
✅ SQL script provided to fix RLS policies

Your document uploads should now save to both the vector database AND Supabase, making them visible in the Document Library! 🎉

