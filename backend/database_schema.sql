-- LexAI Scholar Database Schema
-- This schema is designed for Supabase PostgreSQL

-- Note: Supabase automatically creates an auth.users table for authentication
-- We'll extend it with our custom profiles table

-- ========================================
-- USER PROFILES
-- ========================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    avatar_url TEXT,
    university TEXT,
    graduation_year INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

-- Policies: Users can only read/update their own profile
CREATE POLICY "Users can view own profile" 
    ON public.profiles FOR SELECT 
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" 
    ON public.profiles FOR UPDATE 
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" 
    ON public.profiles FOR INSERT 
    WITH CHECK (auth.uid() = id);

-- ========================================
-- LEGAL DOCUMENTS
-- ========================================
CREATE TABLE IF NOT EXISTS public.documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    file_url TEXT NOT NULL,
    file_type TEXT NOT NULL, -- pdf, docx, txt
    file_size INTEGER, -- in bytes
    status TEXT DEFAULT 'uploaded', -- uploaded, processing, analyzed, error
    document_type TEXT, -- case, statute, contract, brief, etc.
    jurisdiction TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Policies: Users can only access their own documents
CREATE POLICY "Users can view own documents" 
    ON public.documents FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own documents" 
    ON public.documents FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own documents" 
    ON public.documents FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own documents" 
    ON public.documents FOR DELETE 
    USING (auth.uid() = user_id);

-- ========================================
-- DOCUMENT ANALYSIS
-- ========================================
CREATE TABLE IF NOT EXISTS public.document_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    summary TEXT,
    key_points JSONB, -- Array of key legal points
    entities JSONB, -- Named entities (people, organizations, dates)
    citations JSONB, -- Legal citations found
    sentiment_score DECIMAL(3,2),
    complexity_score INTEGER, -- 1-10
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.document_analysis ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own analysis" 
    ON public.document_analysis FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own analysis" 
    ON public.document_analysis FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

-- ========================================
-- STUDY MATERIALS
-- ========================================
CREATE TABLE IF NOT EXISTS public.study_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    material_type TEXT NOT NULL, -- flashcard, summary, quiz, case_brief
    content JSONB NOT NULL, -- Flexible structure for different material types
    tags TEXT[],
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.study_materials ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own study materials" 
    ON public.study_materials FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own study materials" 
    ON public.study_materials FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own study materials" 
    ON public.study_materials FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own study materials" 
    ON public.study_materials FOR DELETE 
    USING (auth.uid() = user_id);

-- ========================================
-- CASE BRIEFS
-- ========================================
CREATE TABLE IF NOT EXISTS public.case_briefs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    document_id UUID REFERENCES public.documents(id) ON DELETE CASCADE,
    case_name TEXT NOT NULL,
    citation TEXT,
    court TEXT,
    year INTEGER,
    facts TEXT,
    issue TEXT,
    holding TEXT,
    reasoning TEXT,
    rule TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE public.case_briefs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own case briefs" 
    ON public.case_briefs FOR SELECT 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own case briefs" 
    ON public.case_briefs FOR INSERT 
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own case briefs" 
    ON public.case_briefs FOR UPDATE 
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own case briefs" 
    ON public.case_briefs FOR DELETE 
    USING (auth.uid() = user_id);

-- ========================================
-- INDEXES for Performance
-- ========================================
CREATE INDEX idx_documents_user_id ON public.documents(user_id);
CREATE INDEX idx_documents_created_at ON public.documents(created_at DESC);
CREATE INDEX idx_document_analysis_document_id ON public.document_analysis(document_id);
CREATE INDEX idx_study_materials_user_id ON public.study_materials(user_id);
CREATE INDEX idx_study_materials_document_id ON public.study_materials(document_id);
CREATE INDEX idx_case_briefs_user_id ON public.case_briefs(user_id);

-- ========================================
-- FUNCTIONS
-- ========================================

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_documents_updated_at BEFORE UPDATE ON public.documents
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_study_materials_updated_at BEFORE UPDATE ON public.study_materials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_case_briefs_updated_at BEFORE UPDATE ON public.case_briefs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (NEW.id, NEW.email, NEW.raw_user_meta_data->>'full_name');
    RETURN NEW;
END;
$$ language 'plpgsql' SECURITY DEFINER;

-- Trigger to create profile automatically when user signs up
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

