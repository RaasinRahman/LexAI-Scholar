-- Fix RLS policies for documents table
-- Run this in Supabase SQL Editor

-- Drop the old restrictive insert policy
DROP POLICY IF EXISTS "Users can insert own documents" ON public.documents;
DROP POLICY IF EXISTS "Service role can insert documents" ON public.documents;

-- Create new permissive insert policy that allows both users and service role
CREATE POLICY "Allow document inserts" 
    ON public.documents FOR INSERT 
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

