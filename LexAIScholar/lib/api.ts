const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Document {
  id: string;
  filename: string;
  title?: string;
  author?: string;
  page_count: number;
  chunk_count: number;
  character_count: number;
  uploaded_at: string;
}

export interface SearchResult {
  id: string;
  score: number;
  text: string;
  filename: string;
  title?: string;
  author?: string;
  chunk_id: number;
  document_id: string;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  count: number;
}

export interface Citation {
  source_number: number;
  document_id: string;
  filename: string;
  title?: string;
  author?: string;
  chunk_id: number;
  text_preview: string;
  relevance_score: number;
}

export interface RAGResponse {
  success: boolean;
  answer: string;
  citations: Citation[];
  sources_found: number;
  context_chunks_used: number;
  followup_questions: string[];
  model: string;
  mode: string;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  timestamp: string;
  query: string;
}

export interface ConversationMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  citations?: Citation[];
}

export interface CaseBrief {
  success: boolean;
  document_id: string;
  case_name?: string;
  brief_type: string;
  brief_content: string;
  sections: Record<string, string>;
  metadata: {
    model: string;
    chunks_processed: number;
    character_count: number;
    usage: {
      prompt_tokens: number;
      completion_tokens: number;
      total_tokens: number;
    };
    generated_at: string;
  };
}

export interface CaseComparison {
  success: boolean;
  comparison: string;
  cases_compared: number;
  case_names: string[];
  usage: {
    total_tokens: number;
  };
  generated_at: string;
}

class APIClient {
  private getAuthHeaders(token?: string): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    return headers;
  }

  async uploadPDF(file: File, token: string): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      console.log('Uploading to:', `${API_BASE_URL}/documents/upload`);
      console.log('File name:', file.name);
      console.log('File size:', file.size);

      const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      console.log('Upload response status:', response.status);

      if (!response.ok) {
        let errorMessage = 'Failed to upload document';
        try {
          const error = await response.json();
          errorMessage = error.detail || errorMessage;
          console.error('Upload error details:', error);
        } catch (e) {
          console.error('Could not parse error response:', e);
          errorMessage = `Upload failed with status ${response.status}`;
        }
        throw new Error(errorMessage);
      }

      const result = await response.json();
      console.log('Upload successful:', result);
      return result;
    } catch (error) {
      console.error('Upload exception:', error);
      throw error;
    }
  }

  async searchDocuments(
    query: string,
    token: string,
    top_k: number = 5,
    min_score: number = 0.5
  ): Promise<SearchResponse> {
    const response = await fetch(`${API_BASE_URL}/documents/search`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({ query, top_k, min_score }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to search documents');
    }

    return response.json();
  }

  async getDocuments(token: string): Promise<Document[]> {
    const response = await fetch(`${API_BASE_URL}/documents`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get documents');
    }

    return response.json();
  }

  async getDocument(documentId: string, token: string): Promise<Document> {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get document');
    }

    return response.json();
  }

  async deleteDocument(documentId: string, token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete document');
    }

    return response.json();
  }

  async getVectorStats(token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/vector-stats`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get vector stats');
    }

    return response.json();
  }

  async healthCheck(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return response.json();
  }

  async askQuestion(
    query: string,
    token: string,
    mode: string = 'qa',
    conversationHistory?: ConversationMessage[],
    options?: {
      top_k?: number;
      min_score?: number;
      temperature?: number;
      max_tokens?: number;
    }
  ): Promise<RAGResponse> {
    const response = await fetch(`${API_BASE_URL}/chat/ask`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({
        query,
        mode,
        conversation_history: conversationHistory,
        top_k: options?.top_k || 5,
        min_score: options?.min_score || 0.3,
        temperature: options?.temperature || 0.3,
        max_tokens: options?.max_tokens || 1000,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get answer');
    }

    return response.json();
  }

  async generateCaseBrief(
    documentId: string,
    token: string,
    options?: {
      brief_type?: 'full' | 'summary';
      temperature?: number;
      max_tokens?: number;
    }
  ): Promise<CaseBrief> {
    const response = await fetch(`${API_BASE_URL}/case-brief/generate`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({
        document_id: documentId,
        brief_type: options?.brief_type || 'full',
        temperature: options?.temperature || 0.2,
        max_tokens: options?.max_tokens || 2500,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to generate case brief');
    }

    return response.json();
  }

  async compareCases(
    documentIds: string[],
    token: string,
    options?: {
      comparison_focus?: string;
      temperature?: number;
      max_tokens?: number;
    }
  ): Promise<CaseComparison> {
    const response = await fetch(`${API_BASE_URL}/case-brief/compare`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({
        document_ids: documentIds,
        comparison_focus: options?.comparison_focus,
        temperature: options?.temperature || 0.3,
        max_tokens: options?.max_tokens || 1500,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to compare cases');
    }

    return response.json();
  }

  async extractCaseSection(
    documentId: string,
    section: string,
    token: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/case-brief/extract-section?document_id=${documentId}&section=${section}`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to extract section');
    }

    return response.json();
  }

  // ==================== WORKSPACE METHODS ====================

  async createWorkspace(
    name: string,
    description: string | null,
    token: string,
    settings?: Record<string, any>
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({ name, description, settings }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create workspace');
    }

    return response.json();
  }

  async getWorkspaces(token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get workspaces');
    }

    return response.json();
  }

  async getWorkspace(workspaceId: string, token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get workspace');
    }

    return response.json();
  }

  async updateWorkspace(
    workspaceId: string,
    updates: { name?: string; description?: string; settings?: Record<string, any> },
    token: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update workspace');
    }

    return response.json();
  }

  async deleteWorkspace(workspaceId: string, token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete workspace');
    }

    return response.json();
  }

  async inviteMemberByEmail(
    workspaceId: string,
    email: string,
    role: string,
    token: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/members/invite-by-email`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({ email, role }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to invite member');
    }

    return response.json();
  }

  async addWorkspaceMember(
    workspaceId: string,
    userId: string,
    role: string,
    token: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/members`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({ user_id: userId, role }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to add member');
    }

    return response.json();
  }

  async getWorkspaceMembers(workspaceId: string, token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/members`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get members');
    }

    return response.json();
  }

  async removeWorkspaceMember(
    workspaceId: string,
    memberId: string,
    token: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/members/${memberId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to remove member');
    }

    return response.json();
  }

  async updateMemberRole(
    workspaceId: string,
    memberId: string,
    role: string,
    token: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/members/${memberId}/role`, {
      method: 'PUT',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({ user_id: memberId, role }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update role');
    }

    return response.json();
  }

  async shareDocumentWithWorkspace(
    workspaceId: string,
    documentId: string,
    token: string,
    permissions?: Record<string, boolean>
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/documents/share`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({ workspace_id: workspaceId, document_id: documentId, permissions }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to share document');
    }

    return response.json();
  }

  async unshareDocument(
    workspaceId: string,
    documentId: string,
    token: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/documents/${documentId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to unshare document');
    }

    return response.json();
  }

  async getWorkspaceDocuments(workspaceId: string, token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/documents`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get workspace documents');
    }

    return response.json();
  }

  async addComment(
    workspaceId: string,
    documentId: string,
    content: string,
    token: string,
    context?: Record<string, any>
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/comments`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({ workspace_id: workspaceId, document_id: documentId, content, context }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to add comment');
    }

    return response.json();
  }

  async getDocumentComments(
    workspaceId: string,
    documentId: string,
    token: string
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/documents/${documentId}/comments`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get comments');
    }

    return response.json();
  }

  async getWorkspaceActivity(
    workspaceId: string,
    token: string,
    limit: number = 50
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/workspaces/${workspaceId}/activity?limit=${limit}`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get activity');
    }

    return response.json();
  }

  // ==================== DOCUMENT CONTENT & ANNOTATIONS ====================

  async getDocumentContent(documentId: string, token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/content`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get document content');
    }

    return response.json();
  }

  async createAnnotation(
    documentId: string,
    annotationType: 'highlight' | 'note' | 'comment',
    startPos: number,
    endPos: number,
    textContent: string,
    token: string,
    options?: {
      workspaceId?: string;
      noteContent?: string;
      color?: string;
    }
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/documents/${documentId}/annotations`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({
        workspace_id: options?.workspaceId,
        document_id: documentId,
        annotation_type: annotationType,
        start_pos: startPos,
        end_pos: endPos,
        text_content: textContent,
        note_content: options?.noteContent,
        color: options?.color || '#ffeb3b',
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create annotation');
    }

    return response.json();
  }

  async getAnnotations(
    documentId: string,
    token: string,
    workspaceId?: string
  ): Promise<any> {
    const url = workspaceId
      ? `${API_BASE_URL}/documents/${documentId}/annotations?workspace_id=${workspaceId}`
      : `${API_BASE_URL}/documents/${documentId}/annotations`;

    const response = await fetch(url, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get annotations');
    }

    return response.json();
  }

  async updateAnnotation(
    annotationId: string,
    token: string,
    updates: {
      noteContent?: string;
      color?: string;
    }
  ): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/annotations/${annotationId}`, {
      method: 'PUT',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({
        note_content: updates.noteContent,
        color: updates.color,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to update annotation');
    }

    return response.json();
  }

  async deleteAnnotation(annotationId: string, token: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/annotations/${annotationId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(token),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to delete annotation');
    }

    return response.json();
  }
}

export const api = new APIClient();

