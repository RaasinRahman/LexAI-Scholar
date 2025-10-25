-- Fix RLS policies for documents table to allow uploads
-- Run this in Supabase SQL Editor if uploads are failing

-- First, let's drop all existing policies
DROP POLICY IF EXISTS "Users can view own documents" ON public.documents;
DROP POLICY IF EXISTS "Users can insert own documents" ON public.documents;
DROP POLICY IF EXISTS "Allow document inserts" ON public.documents;
DROP POLICY IF EXISTS "Service role can insert documents" ON public.documents;
DROP POLICY IF EXISTS "Users can update own documents" ON public.documents;
DROP POLICY IF EXISTS "Users can delete own documents" ON public.documents;

-- Create new permissive policies

-- SELECT: Users can only see their own documents
CREATE POLICY "documents_select_policy" 
    ON public.documents FOR SELECT 
    USING (auth.uid() = user_id);

-- INSERT: Allow authenticated users to insert documents with their user_id
CREATE POLICY "documents_insert_policy" 
    ON public.documents FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

-- UPDATE: Users can only update their own documents
CREATE POLICY "documents_update_policy" 
    ON public.documents FOR UPDATE 
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- DELETE: Users can only delete their own documents
CREATE POLICY "documents_delete_policy" 
    ON public.documents FOR DELETE 
    USING (auth.uid() = user_id);

-- Make sure RLS is enabled
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Grant necessary permissions
GRANT ALL ON public.documents TO authenticated;
GRANT ALL ON public.documents TO service_role;

-- Verify the policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual, with_check
FROM pg_policies
WHERE tablename = 'documents';

