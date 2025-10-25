/**
 * API Client for LexAI Scholar Backend
 */

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

  /**
   * Upload a PDF document
   */
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

  /**
   * Search documents semantically
   */
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

  /**
   * Get all documents for the user
   */
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

  /**
   * Get a specific document
   */
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

  /**
   * Delete a document
   */
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

  /**
   * Get vector database stats
   */
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

  /**
   * Health check
   */
  async healthCheck(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/health`);
    
    if (!response.ok) {
      throw new Error('Health check failed');
    }

    return response.json();
  }
}

export const api = new APIClient();

