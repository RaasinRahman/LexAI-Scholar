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
}

export const api = new APIClient();

