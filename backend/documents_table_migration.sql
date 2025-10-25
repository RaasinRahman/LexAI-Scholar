-- Migration: Create documents table for PDF uploads
-- This table stores metadata about uploaded PDFs and their processing status

-- Create the updated_at function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Drop existing table if it has wrong schema (backup data first if needed)
DROP TABLE IF EXISTS public.documents CASCADE;

-- Create new documents table with correct schema for PDF uploads
CREATE TABLE public.documents (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    title TEXT,
    author TEXT,
    page_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    character_count INTEGER DEFAULT 0,
    file_size_bytes INTEGER DEFAULT 0,
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- RLS Policies: Users can only access their own documents
-- Backend uses service role which should bypass RLS, but we add permissive policies just in case

CREATE POLICY "Users can view own documents" 
    ON public.documents FOR SELECT 
    USING (auth.uid() = user_id);

-- Allow inserts from users OR from service role (backend)
CREATE POLICY "Allow document inserts" 
    ON public.documents FOR INSERT 
    WITH CHECK (auth.uid() = user_id OR auth.role() = 'service_role');

CREATE POLICY "Users can update own documents" 
    ON public.documents FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own documents" 
    ON public.documents FOR DELETE 
    USING (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX idx_documents_user_id ON public.documents(user_id);
CREATE INDEX idx_documents_uploaded_at ON public.documents(uploaded_at DESC);
CREATE INDEX idx_documents_filename ON public.documents(filename);

-- Add trigger for updated_at
CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON public.documents
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Grant necessary permissions
GRANT ALL ON public.documents TO authenticated;
GRANT ALL ON public.documents TO service_role;

