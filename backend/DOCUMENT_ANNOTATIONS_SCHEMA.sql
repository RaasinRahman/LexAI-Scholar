-- Document Annotations Table
-- Stores highlights, notes, and annotations on documents

CREATE TABLE IF NOT EXISTS document_annotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Annotation details
    annotation_type TEXT NOT NULL CHECK (annotation_type IN ('highlight', 'note', 'comment')),
    start_pos INTEGER NOT NULL,
    end_pos INTEGER NOT NULL,
    text_content TEXT NOT NULL, -- The actual text that was highlighted/annotated
    note_content TEXT, -- Optional note/comment added by the user
    color TEXT DEFAULT '#ffeb3b', -- Highlight color (hex)
    
    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ,
    
    -- Constraints
    CONSTRAINT valid_position CHECK (end_pos > start_pos)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_document_annotations_document_id ON document_annotations(document_id);
CREATE INDEX IF NOT EXISTS idx_document_annotations_workspace_id ON document_annotations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_document_annotations_user_id ON document_annotations(user_id);
CREATE INDEX IF NOT EXISTS idx_document_annotations_created_at ON document_annotations(created_at DESC);

-- Row Level Security (RLS)
ALTER TABLE document_annotations ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view annotations on documents they own or that are shared in their workspaces
CREATE POLICY "Users can view annotations on accessible documents"
    ON document_annotations
    FOR SELECT
    USING (
        -- User owns the document
        EXISTS (
            SELECT 1 FROM documents
            WHERE documents.id = document_annotations.document_id
            AND documents.user_id = auth.uid()
        )
        OR
        -- Document is in a workspace the user has access to
        EXISTS (
            SELECT 1 FROM workspace_members wm
            JOIN workspace_documents wd ON wd.workspace_id = wm.workspace_id
            WHERE wd.document_id = document_annotations.document_id
            AND wm.user_id = auth.uid()
        )
    );

-- Policy: Users can create annotations on documents they have access to
CREATE POLICY "Users can create annotations on accessible documents"
    ON document_annotations
    FOR INSERT
    WITH CHECK (
        user_id = auth.uid()
        AND
        (
            -- User owns the document
            EXISTS (
                SELECT 1 FROM documents
                WHERE documents.id = document_annotations.document_id
                AND documents.user_id = auth.uid()
            )
            OR
            -- Document is in a workspace where user has at least viewer role
            EXISTS (
                SELECT 1 FROM workspace_members wm
                JOIN workspace_documents wd ON wd.workspace_id = wm.workspace_id
                WHERE wd.document_id = document_annotations.document_id
                AND wm.user_id = auth.uid()
            )
        )
    );

-- Policy: Users can update their own annotations
CREATE POLICY "Users can update their own annotations"
    ON document_annotations
    FOR UPDATE
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Policy: Users can delete their own annotations
CREATE POLICY "Users can delete their own annotations"
    ON document_annotations
    FOR DELETE
    USING (user_id = auth.uid());

-- Comment on table
COMMENT ON TABLE document_annotations IS 'Stores user annotations, highlights, and notes on documents';

