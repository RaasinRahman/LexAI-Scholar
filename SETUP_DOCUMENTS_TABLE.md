# Fix Documents Table in Supabase

## Problem
The `documents` table doesn't exist or has the wrong schema in Supabase, causing uploaded PDFs to not appear in the library.

## Solution
Run the SQL migration to create the correct table structure.

## Steps

### 1. Open Supabase Dashboard
1. Go to https://supabase.com/dashboard
2. Select your project
3. Click on **SQL Editor** in the left sidebar

### 2. Run the Migration
1. Click **New query**
2. Copy the contents of `backend/documents_table_migration.sql`
3. Paste into the SQL editor
4. Click **Run** or press `Ctrl+Enter` (Cmd+Enter on Mac)

### 3. Verify the Table
After running the migration, verify the table was created:

```sql
-- Check if table exists and view its structure
SELECT * FROM information_schema.columns 
WHERE table_name = 'documents';

-- Check RLS policies
SELECT * FROM pg_policies WHERE tablename = 'documents';
```

### 4. Test the Upload
1. Return to your app
2. Upload a PDF document
3. Switch to the **Library** tab
4. Your document should now appear!

## Expected Table Structure

The `documents` table should have these columns:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to auth.users)
- `filename` (TEXT)
- `title` (TEXT, nullable)
- `author` (TEXT, nullable)
- `page_count` (INTEGER)
- `chunk_count` (INTEGER)
- `character_count` (INTEGER)
- `file_size_bytes` (INTEGER)
- `uploaded_at` (TIMESTAMP)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

## Troubleshooting

### Error: "relation already exists"
If you see this error, the table exists but might have the wrong schema. You have two options:

**Option A: Drop and recreate (if you don't care about existing data)**
```sql
DROP TABLE IF EXISTS public.documents CASCADE;
-- Then run the full migration again
```

**Option B: Alter existing table (preserve data)**
Run only the necessary ALTER TABLE commands based on what columns are missing.

### Error: "permission denied"
Make sure you're logged in with the correct Supabase account and have admin access to the project.

### Documents still not showing
1. Check browser console for errors
2. Refresh the page (hard refresh: Ctrl+Shift+R / Cmd+Shift+R)
3. Click the refresh button in the Document Library
4. Check backend logs: `tail -f backend/server.log`

