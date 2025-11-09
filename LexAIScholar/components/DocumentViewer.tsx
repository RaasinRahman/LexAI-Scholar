'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import {
  FileText,
  Highlighter,
  MessageSquare,
  StickyNote,
  X,
  Trash2,
  Edit3,
  Save,
  Loader2,
  ChevronLeft,
  User,
  Palette,
  Eye,
  Edit,
  Users,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';

interface Annotation {
  id: string;
  annotation_type: 'highlight' | 'note' | 'comment';
  start_pos: number;
  end_pos: number;
  text_content: string;
  note_content?: string;
  color: string;
  user_id: string;
  created_at: string;
  updated_at?: string;
  profiles?: {
    full_name?: string;
    email?: string;
  };
}

interface DocumentViewerProps {
  documentId: string;
  workspaceId?: string;
  onClose?: () => void;
}

const HIGHLIGHT_COLORS = [
  { name: 'Yellow', hex: '#ffeb3b', bg: 'bg-yellow-200', text: 'text-yellow-900' },
  { name: 'Green', hex: '#4caf50', bg: 'bg-green-200', text: 'text-green-900' },
  { name: 'Blue', hex: '#2196f3', bg: 'bg-blue-200', text: 'text-blue-900' },
  { name: 'Pink', hex: '#e91e63', bg: 'bg-pink-200', text: 'text-pink-900' },
  { name: 'Purple', hex: '#9c27b0', bg: 'bg-purple-200', text: 'text-purple-900' },
  { name: 'Orange', hex: '#ff9800', bg: 'bg-orange-200', text: 'text-orange-900' },
];

export default function DocumentViewer({ documentId, workspaceId, onClose }: DocumentViewerProps) {
  const { session, user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [documentContent, setDocumentContent] = useState<any>(null);
  const [annotations, setAnnotations] = useState<Annotation[]>([]);
  const [selectedText, setSelectedText] = useState<{
    text: string;
    start: number;
    end: number;
  } | null>(null);
  const [showAnnotationMenu, setShowAnnotationMenu] = useState(false);
  const [menuPosition, setMenuPosition] = useState({ x: 0, y: 0 });
  const [selectedColor, setSelectedColor] = useState('#ffeb3b');
  const [annotationNote, setAnnotationNote] = useState('');
  const [editingAnnotation, setEditingAnnotation] = useState<string | null>(null);
  const [editNoteContent, setEditNoteContent] = useState('');
  const [showSidebar, setShowSidebar] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [editableContent, setEditableContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [viewMode, setViewMode] = useState<'read' | 'edit'>('read');
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  const contentRef = useRef<HTMLDivElement>(null);
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const refreshIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (documentId && session?.access_token) {
      loadDocumentContent();
      loadAnnotations();
    }
  }, [documentId, session]);

  // Auto-refresh annotations for real-time collaboration
  useEffect(() => {
    if (autoRefresh && workspaceId && session?.access_token) {
      refreshIntervalRef.current = setInterval(() => {
        loadAnnotations();
      }, 5000); // Refresh every 5 seconds

      return () => {
        if (refreshIntervalRef.current) {
          clearInterval(refreshIntervalRef.current);
        }
      };
    }
  }, [autoRefresh, workspaceId, session]);

  const loadDocumentContent = async () => {
    if (!session?.access_token) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await api.getDocumentContent(documentId, session.access_token);
      if (result.success) {
        setDocumentContent(result);
        setEditableContent(result.full_text || '');
      } else {
        setError('Failed to load document content');
      }
    } catch (error: any) {
      console.error('Error loading document:', error);
      setError(error.message || 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const loadAnnotations = useCallback(async () => {
    if (!session?.access_token) return;
    
    try {
      const result = await api.getAnnotations(documentId, session.access_token, workspaceId);
      if (result.success) {
        setAnnotations(result.annotations || []);
      }
    } catch (error: any) {
      console.error('Error loading annotations:', error);
    }
  }, [documentId, session?.access_token, workspaceId]);

  const handleTextSelection = () => {
    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !contentRef.current) {
      setShowAnnotationMenu(false);
      return;
    }

    const selectedTextContent = selection.toString();
    if (!selectedTextContent.trim()) {
      setShowAnnotationMenu(false);
      return;
    }

    // Get the range and calculate position
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    
    // Calculate position relative to content
    const fullText = contentRef.current.innerText;
    const beforeRange = range.cloneRange();
    beforeRange.selectNodeContents(contentRef.current);
    beforeRange.setEnd(range.startContainer, range.startOffset);
    const startPos = beforeRange.toString().length;
    const endPos = startPos + selectedTextContent.length;

    setSelectedText({
      text: selectedTextContent,
      start: startPos,
      end: endPos,
    });
    
    setMenuPosition({
      x: rect.left + window.scrollX,
      y: rect.bottom + window.scrollY + 5,
    });
    
    setShowAnnotationMenu(true);
  };

  const createHighlight = async (withNote: boolean = false) => {
    if (!selectedText || !session?.access_token) return;

    try {
      await api.createAnnotation(
        documentId,
        withNote ? 'note' : 'highlight',
        selectedText.start,
        selectedText.end,
        selectedText.text,
        session.access_token,
        {
          workspaceId,
          noteContent: withNote ? annotationNote : undefined,
          color: selectedColor,
        }
      );

      setAnnotationNote('');
      setShowAnnotationMenu(false);
      setSelectedText(null);
      await loadAnnotations();
      
      // Clear selection
      window.getSelection()?.removeAllRanges();
    } catch (error: any) {
      alert('Failed to create annotation: ' + error.message);
    }
  };

  const deleteAnnotation = async (annotationId: string) => {
    if (!session?.access_token) return;
    
    if (!confirm('Delete this annotation?')) return;

    try {
      await api.deleteAnnotation(annotationId, session.access_token);
      await loadAnnotations();
    } catch (error: any) {
      alert('Failed to delete annotation: ' + error.message);
    }
  };

  const updateAnnotation = async (annotationId: string) => {
    if (!session?.access_token) return;

    try {
      await api.updateAnnotation(annotationId, session.access_token, {
        noteContent: editNoteContent,
      });
      
      setEditingAnnotation(null);
      setEditNoteContent('');
      await loadAnnotations();
    } catch (error: any) {
      alert('Failed to update annotation: ' + error.message);
    }
  };

  const renderContentWithHighlights = () => {
    if (!documentContent?.full_text) return null;

    const text = documentContent.full_text;
    const sortedAnnotations = [...annotations].sort((a, b) => a.start_pos - b.start_pos);
    
    const parts: JSX.Element[] = [];
    let lastIndex = 0;

    sortedAnnotations.forEach((annotation, idx) => {
      // Add text before highlight
      if (annotation.start_pos > lastIndex) {
        parts.push(
          <span key={`text-${idx}`}>
            {text.substring(lastIndex, annotation.start_pos)}
          </span>
        );
      }

      // Add highlighted text
      const highlightedText = text.substring(annotation.start_pos, annotation.end_pos);
      parts.push(
        <span
          key={`highlight-${annotation.id}`}
          className="relative cursor-pointer transition-opacity hover:opacity-75"
          style={{ backgroundColor: annotation.color + '66' }} // Add transparency
          title={annotation.note_content || 'Highlight'}
        >
          {highlightedText}
        </span>
      );

      lastIndex = annotation.end_pos;
    });

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(
        <span key="text-end">
          {text.substring(lastIndex)}
        </span>
      );
    }

    return parts;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-gray-400 text-lg mb-2">Loading document...</p>
          <p className="text-gray-500 text-sm">Please wait while we fetch the content</p>
        </div>
      </div>
    );
  }

  if (error || !documentContent) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-900">
        <div className="text-center max-w-md">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-white mb-2">
            {error ? 'Error Loading Document' : 'Document Not Found'}
          </h2>
          <p className="text-gray-400 mb-6">
            {error || 'The document you\'re looking for could not be found or you don\'t have access to it.'}
          </p>
          <div className="flex gap-3 justify-center">
            {onClose && (
              <button
                onClick={onClose}
                className="px-6 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Go Back
              </button>
            )}
            <button
              onClick={() => {
                setError(null);
                loadDocumentContent();
              }}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-slate-800 border-b border-slate-700 px-6 py-4 shadow-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            {onClose && (
              <button
                onClick={onClose}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                title="Go back"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
            )}
            <div>
              <h1 className="text-xl font-bold text-white flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-400" />
                {documentContent.title || documentContent.document_name}
              </h1>
              <div className="flex items-center gap-3 mt-1">
                {documentContent.author && (
                  <p className="text-sm text-gray-400">by {documentContent.author}</p>
                )}
                {workspaceId && (
                  <span className="flex items-center gap-1 text-xs text-blue-400 bg-blue-500/10 px-2 py-1 rounded">
                    <Users className="w-3 h-3" />
                    Shared Workspace
                  </span>
                )}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {/* View mode info */}
            <div className="flex items-center gap-2 text-sm text-gray-400 bg-slate-700/50 px-3 py-2 rounded-lg">
              <Eye className="w-4 h-4" />
              <span>{annotations.length} annotation{annotations.length !== 1 ? 's' : ''}</span>
            </div>
            
            {/* Auto-refresh toggle for workspace */}
            {workspaceId && (
              <button
                onClick={() => setAutoRefresh(!autoRefresh)}
                className={`px-3 py-2 rounded-lg transition-colors flex items-center gap-2 text-sm ${
                  autoRefresh 
                    ? 'bg-green-600/20 text-green-400 hover:bg-green-600/30' 
                    : 'bg-slate-700 text-gray-400 hover:bg-slate-600'
                }`}
                title={autoRefresh ? 'Live updates enabled' : 'Live updates disabled'}
              >
                <RefreshCw className={`w-4 h-4 ${autoRefresh ? 'animate-spin' : ''}`} />
                {autoRefresh ? 'Live' : 'Static'}
              </button>
            )}
            
            <button
              onClick={() => setShowSidebar(!showSidebar)}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg transition-colors flex items-center gap-2"
            >
              <StickyNote className="w-4 h-4" />
              {showSidebar ? 'Hide' : 'Show'} Annotations
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex">
        {/* Document Content */}
        <div className={`flex-1 ${showSidebar ? 'mr-96' : ''} transition-all duration-300`}>
          <div className="max-w-4xl mx-auto px-8 py-12">
            {/* Document Info Banner */}
            {documentContent.total_chunks && (
              <div className="mb-6 p-4 bg-slate-800/50 border border-slate-700 rounded-lg">
                <div className="flex items-center justify-between text-sm text-gray-400">
                  <div className="flex items-center gap-4">
                    <span>📄 {documentContent.total_chunks} chunks</span>
                    <span>📝 {documentContent.character_count?.toLocaleString()} characters</span>
                  </div>
                  {documentContent.full_text && (
                    <span className="text-green-400 flex items-center gap-1">
                      ✓ Content loaded successfully
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Empty State */}
            {!documentContent.full_text || documentContent.full_text.trim() === '' ? (
              <div className="text-center py-16">
                <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-white mb-2">No Content Available</h3>
                <p className="text-gray-400 mb-6">
                  This document appears to be empty or the content could not be extracted.
                </p>
                <button
                  onClick={loadDocumentContent}
                  className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 mx-auto"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reload Document
                </button>
              </div>
            ) : (
              <div
                ref={contentRef}
                className="prose prose-invert prose-lg max-w-none bg-slate-800/30 border border-slate-700/50 rounded-lg p-8 shadow-inner"
                onMouseUp={handleTextSelection}
                style={{
                  lineHeight: '1.8',
                  fontSize: '16px',
                  fontFamily: 'Georgia, serif',
                  whiteSpace: 'pre-wrap',
                  minHeight: '500px',
                }}
              >
                {renderContentWithHighlights()}
              </div>
            )}
          </div>
        </div>

        {/* Annotations Sidebar */}
        {showSidebar && (
          <div className="fixed right-0 top-[73px] w-96 h-[calc(100vh-73px)] bg-slate-800 border-l border-slate-700 overflow-y-auto shadow-2xl">
            <div className="p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  <StickyNote className="w-5 h-5 text-purple-400" />
                  Annotations
                  <span className="text-sm font-normal text-gray-400">({annotations.length})</span>
                </h2>
                <button
                  onClick={loadAnnotations}
                  className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                  title="Refresh annotations"
                >
                  <RefreshCw className="w-4 h-4 text-gray-400" />
                </button>
              </div>
              
              {/* Quick Guide */}
              <div className="mb-4 p-3 bg-blue-500/10 border border-blue-500/30 rounded-lg">
                <p className="text-xs text-blue-300 flex items-center gap-2">
                  <Highlighter className="w-3 h-3" />
                  Select text in the document to create highlights and notes
                </p>
              </div>
              
              {annotations.length === 0 ? (
                <div className="text-center py-16 text-gray-400">
                  <div className="w-20 h-20 mx-auto mb-4 bg-slate-700/50 rounded-full flex items-center justify-center">
                    <Highlighter className="w-10 h-10 text-gray-600" />
                  </div>
                  <p className="font-medium text-white mb-2">No annotations yet</p>
                  <p className="text-sm">Start by selecting text in the document</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {annotations.map((annotation) => (
                    <div
                      key={annotation.id}
                      className="bg-slate-700/50 rounded-lg p-4 border border-slate-600 hover:border-slate-500 transition-all hover:shadow-lg"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-5 h-5 rounded shadow-sm"
                            style={{ backgroundColor: annotation.color }}
                          />
                          <span className="text-xs uppercase font-semibold tracking-wide text-gray-400">
                            {annotation.annotation_type}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => {
                              setEditingAnnotation(annotation.id);
                              setEditNoteContent(annotation.note_content || '');
                            }}
                            className="p-1.5 hover:bg-slate-600 rounded transition-colors"
                            title="Edit note"
                          >
                            <Edit3 className="w-3.5 h-3.5 text-blue-400" />
                          </button>
                          <button
                            onClick={() => deleteAnnotation(annotation.id)}
                            className="p-1.5 hover:bg-slate-600 rounded transition-colors"
                            title="Delete annotation"
                          >
                            <Trash2 className="w-3.5 h-3.5 text-red-400" />
                          </button>
                        </div>
                      </div>
                      
                      <div
                        className="text-sm text-gray-200 mb-3 p-3 rounded-lg border-l-4"
                        style={{ 
                          backgroundColor: annotation.color + '15',
                          borderColor: annotation.color
                        }}
                      >
                        <p className="italic">
                          "{annotation.text_content.substring(0, 120)}
                          {annotation.text_content.length > 120 ? '...' : ''}"
                        </p>
                      </div>
                      
                      {editingAnnotation === annotation.id ? (
                        <div className="space-y-2">
                          <label className="text-xs font-medium text-gray-400">Your Note:</label>
                          <textarea
                            value={editNoteContent}
                            onChange={(e) => setEditNoteContent(e.target.value)}
                            className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                            rows={4}
                            placeholder="Add your thoughts, insights, or comments..."
                          />
                          <div className="flex gap-2">
                            <button
                              onClick={() => updateAnnotation(annotation.id)}
                              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                            >
                              <Save className="w-4 h-4" />
                              Save Note
                            </button>
                            <button
                              onClick={() => {
                                setEditingAnnotation(null);
                                setEditNoteContent('');
                              }}
                              className="px-4 py-2 bg-slate-600 hover:bg-slate-500 rounded-lg text-sm transition-colors"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <>
                          {annotation.note_content && (
                            <div className="mb-3 p-3 bg-slate-900/70 rounded-lg text-sm text-gray-200 border border-slate-600">
                              <div className="flex items-start gap-2">
                                <StickyNote className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
                                <p className="flex-1">{annotation.note_content}</p>
                              </div>
                            </div>
                          )}
                          <div className="flex items-center justify-between text-xs text-gray-500">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold">
                                {annotation.profiles?.full_name?.charAt(0)?.toUpperCase() || 
                                 annotation.profiles?.email?.charAt(0)?.toUpperCase() || 
                                 'U'}
                              </div>
                              <span className="font-medium">
                                {annotation.profiles?.full_name || annotation.profiles?.email || 'Unknown User'}
                              </span>
                            </div>
                            <span className="text-gray-600">{formatDate(annotation.created_at)}</span>
                          </div>
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Annotation Menu */}
      {showAnnotationMenu && selectedText && (
        <div
          className="fixed z-50 bg-slate-800 border-2 border-slate-600 rounded-xl shadow-2xl p-5 min-w-96 backdrop-blur-sm"
          style={{
            left: `${Math.min(menuPosition.x, window.innerWidth - 400)}px`,
            top: `${menuPosition.y}px`,
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <Highlighter className="w-5 h-5 text-yellow-400" />
              Create Annotation
            </h3>
            <button
              onClick={() => {
                setShowAnnotationMenu(false);
                setSelectedText(null);
                setAnnotationNote('');
                window.getSelection()?.removeAllRanges();
              }}
              className="p-1.5 hover:bg-slate-700 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-gray-400" />
            </button>
          </div>

          {/* Selected Text Preview */}
          <div className="mb-4 p-3 bg-slate-900/70 border border-slate-600 rounded-lg">
            <p className="text-xs text-gray-400 mb-1">Selected text:</p>
            <p className="text-sm text-gray-200 italic line-clamp-2">
              "{selectedText.text.substring(0, 100)}
              {selectedText.text.length > 100 ? '...' : ''}"
            </p>
          </div>

          <div className="space-y-4">
            {/* Color Picker */}
            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block uppercase tracking-wide">
                Highlight Color
              </label>
              <div className="flex gap-2 flex-wrap">
                {HIGHLIGHT_COLORS.map((color) => (
                  <button
                    key={color.hex}
                    onClick={() => setSelectedColor(color.hex)}
                    className={`w-10 h-10 rounded-lg ${color.bg} border-3 transition-all transform hover:scale-110 ${
                      selectedColor === color.hex 
                        ? 'border-white shadow-lg ring-2 ring-white' 
                        : 'border-slate-600 hover:border-slate-400'
                    }`}
                    title={color.name}
                    style={{ 
                      borderWidth: selectedColor === color.hex ? '3px' : '2px',
                      borderColor: selectedColor === color.hex ? '#ffffff' : '#475569'
                    }}
                  />
                ))}
              </div>
            </div>

            {/* Note Input */}
            <div>
              <label className="text-xs font-semibold text-gray-300 mb-2 block uppercase tracking-wide flex items-center gap-2">
                <StickyNote className="w-3.5 h-3.5" />
                Add Note (Optional)
              </label>
              <textarea
                value={annotationNote}
                onChange={(e) => setAnnotationNote(e.target.value)}
                placeholder="Add your thoughts, insights, or questions..."
                className="w-full px-4 py-3 bg-slate-900 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
                rows={3}
                autoFocus
              />
              <p className="text-xs text-gray-500 mt-1">
                {annotationNote.length}/500 characters
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 pt-2">
              <button
                onClick={() => createHighlight(!!annotationNote.trim())}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-xl"
              >
                <Highlighter className="w-4 h-4" />
                {annotationNote.trim() ? 'Highlight + Note' : 'Highlight Only'}
              </button>
              <button
                onClick={() => {
                  setShowAnnotationMenu(false);
                  setSelectedText(null);
                  setAnnotationNote('');
                  window.getSelection()?.removeAllRanges();
                }}
                className="px-4 py-3 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm font-medium transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

