'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import { api, Document } from '@/lib/api';
import DocumentViewer from './DocumentViewer';
import { Library, RefreshCw, FileText, User, FileStack, FileType, Calendar, Trash2, Loader2, Share2, X, ExternalLink } from 'lucide-react';

interface DocumentLibraryProps {
  onRefresh?: boolean;
}

export default function DocumentLibrary({ onRefresh }: DocumentLibraryProps) {
  const { session } = useAuth();
  const { workspaces } = useWorkspace();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [sharingDocId, setSharingDocId] = useState<string | null>(null);
  const [showShareModal, setShowShareModal] = useState(false);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string>('');
  const [viewingDocumentId, setViewingDocumentId] = useState<string | null>(null);

  const loadDocuments = async () => {
    if (!session?.access_token) return;

    setIsLoading(true);
    setError(null);

    try {
      const docs = await api.getDocuments(session.access_token);
      setDocuments(docs);
    } catch (err: any) {
      setError(err.message || 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [session, onRefresh]);

  const handleDelete = async (documentId: string) => {
    if (!session?.access_token) return;
    
    if (!confirm('Are you sure you want to delete this document? This will remove it from the vector database.')) {
      return;
    }

    setDeletingId(documentId);

    try {
      await api.deleteDocument(documentId, session.access_token);
      setDocuments(documents.filter(doc => doc.id !== documentId));
    } catch (err: any) {
      alert(`Failed to delete document: ${err.message}`);
    } finally {
      setDeletingId(null);
    }
  };

  const handleShareDocument = async () => {
    if (!session?.access_token || !sharingDocId || !selectedWorkspace) return;

    try {
      await api.shareDocumentWithWorkspace(
        selectedWorkspace,
        sharingDocId,
        session.access_token
      );
      
      alert('Document shared successfully!');
      setShowShareModal(false);
      setSharingDocId(null);
      setSelectedWorkspace('');
    } catch (err: any) {
      alert(`Failed to share document: ${err.message}`);
    }
  };

  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatFileSize = (bytes: number): string => {
    const mb = bytes / (1024 * 1024);
    return `${mb.toFixed(2)} MB`;
  };

  // Show document viewer if a document is selected
  if (viewingDocumentId) {
    return (
      <DocumentViewer
        documentId={viewingDocumentId}
        onClose={() => setViewingDocumentId(null)}
      />
    );
  }

  if (isLoading) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
        <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
          <Library className="w-6 h-6" />
          Document Library
        </h2>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="animate-spin h-8 w-8 text-blue-500" />
          <span className="ml-3 text-gray-300">Loading documents...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Library className="w-6 h-6" />
          Document Library
        </h2>
        <button
          onClick={loadDocuments}
          className="text-gray-400 hover:text-white p-2 rounded-lg hover:bg-slate-700 transition"
          title="Refresh"
        >
          <RefreshCw className="w-5 h-5" />
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500 rounded-lg">
          <p className="text-red-400 text-sm">{error}</p>
        </div>
      )}

      {documents.length === 0 ? (
        <div className="text-center py-12">
          <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-gray-400 font-medium mb-2">No documents yet</h3>
          <p className="text-gray-500 text-sm">
            Upload your first PDF document to get started
          </p>
        </div>
      ) : (
        <>
          <div className="mb-4 text-sm text-gray-400">
            {documents.length} document{documents.length !== 1 ? 's' : ''} in your library
          </div>

          <div className="space-y-3">
            {documents.map((doc) => (
              <div
                key={doc.id}
                className="bg-slate-700/50 border border-slate-600 rounded-lg p-4 hover:border-blue-500 transition duration-200"
              >
                <div className="flex items-start justify-between">
                  {/* Document Info */}
                  <div className="flex items-start space-x-3 flex-1 min-w-0">
                    <div className="flex-shrink-0 mt-1">
                      <svg className="w-8 h-8 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="text-white font-semibold mb-1 truncate">
                        {doc.title || doc.filename}
                      </h3>
                      {doc.title && doc.title !== doc.filename && (
                        <p className="text-gray-400 text-sm mb-1 truncate flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          {doc.filename}
                        </p>
                      )}
                      {doc.author && (
                        <p className="text-gray-400 text-sm mb-1 flex items-center gap-1">
                          <User className="w-3 h-3" />
                          {doc.author}
                        </p>
                      )}
                      <div className="flex flex-wrap gap-3 text-xs text-gray-400 mt-2">
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          {doc.page_count} page{doc.page_count !== 1 ? 's' : ''}
                        </span>
                        <span className="flex items-center gap-1">
                          <FileStack className="w-3 h-3" />
                          {doc.chunk_count} chunk{doc.chunk_count !== 1 ? 's' : ''}
                        </span>
                        <span className="flex items-center gap-1">
                          <FileType className="w-3 h-3" />
                          {doc.character_count.toLocaleString()} chars
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(doc.uploaded_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 ml-4">
                    <button
                      onClick={() => setViewingDocumentId(doc.id)}
                      className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                      title="Open document"
                    >
                      <ExternalLink className="w-4 h-4" />
                      Open
                    </button>
                    {workspaces.length > 0 && (
                      <button
                        onClick={() => {
                          setSharingDocId(doc.id);
                          setShowShareModal(true);
                        }}
                        className="text-blue-400 hover:text-blue-300 p-2 rounded-lg hover:bg-blue-500/10 transition"
                        title="Share with workspace"
                      >
                        <Share2 className="w-5 h-5" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(doc.id)}
                      disabled={deletingId === doc.id}
                      className="text-red-400 hover:text-red-300 p-2 rounded-lg hover:bg-red-500/10 transition disabled:opacity-50"
                      title="Delete document"
                    >
                      {deletingId === doc.id ? (
                        <Loader2 className="animate-spin h-5 w-5" />
                      ) : (
                        <Trash2 className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </>
      )}

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-bold text-white">Share Document</h3>
              <button
                onClick={() => {
                  setShowShareModal(false);
                  setSharingDocId(null);
                  setSelectedWorkspace('');
                }}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Select Workspace
                </label>
                <select
                  value={selectedWorkspace}
                  onChange={(e) => setSelectedWorkspace(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Choose a workspace...</option>
                  {workspaces.map((workspace) => (
                    <option key={workspace.id} value={workspace.id}>
                      {workspace.name}
                    </option>
                  ))}
                </select>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleShareDocument}
                  disabled={!selectedWorkspace}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium"
                >
                  Share
                </button>
                <button
                  onClick={() => {
                    setShowShareModal(false);
                    setSharingDocId(null);
                    setSelectedWorkspace('');
                  }}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

