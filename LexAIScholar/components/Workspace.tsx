'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import { api } from '@/lib/api';
import DocumentViewer from './DocumentViewer';
import {
  Users,
  FileText,
  Activity,
  Settings,
  Plus,
  X,
  Share2,
  MessageSquare,
  Trash2,
  UserPlus,
  Crown,
  Shield,
  Edit3,
  Eye,
  Clock,
  ChevronDown,
  ExternalLink,
} from 'lucide-react';

export default function Workspace() {
  const { session, user } = useAuth();
  const { currentWorkspace, refreshWorkspaces } = useWorkspace();
  const [activeTab, setActiveTab] = useState<'documents' | 'members' | 'activity' | 'settings'>('documents');
  const [viewingDocumentId, setViewingDocumentId] = useState<string | null>(null);
  
  // Documents state
  const [documents, setDocuments] = useState<any[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  
  // Members state
  const [members, setMembers] = useState<any[]>([]);
  const [loadingMembers, setLoadingMembers] = useState(false);
  const [showAddMember, setShowAddMember] = useState(false);
  const [newMemberEmail, setNewMemberEmail] = useState('');
  const [newMemberRole, setNewMemberRole] = useState('viewer');
  
  // Activity state
  const [activities, setActivities] = useState<any[]>([]);
  const [loadingActivity, setLoadingActivity] = useState(false);
  
  // Comments state
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const [comments, setComments] = useState<any[]>([]);
  const [newComment, setNewComment] = useState('');
  const [showComments, setShowComments] = useState(false);

  useEffect(() => {
    if (currentWorkspace && activeTab === 'documents') {
      loadDocuments();
    } else if (currentWorkspace && activeTab === 'members') {
      loadMembers();
    } else if (currentWorkspace && activeTab === 'activity') {
      loadActivity();
    }
  }, [currentWorkspace, activeTab]);

  const loadDocuments = async () => {
    if (!currentWorkspace || !session?.access_token) return;
    
    setLoadingDocs(true);
    try {
      const result = await api.getWorkspaceDocuments(currentWorkspace.id, session.access_token);
      if (result.success) {
        setDocuments(result.documents || []);
      }
    } catch (error: any) {
      console.error('Error loading documents:', error);
    } finally {
      setLoadingDocs(false);
    }
  };

  const loadMembers = async () => {
    if (!currentWorkspace || !session?.access_token) return;
    
    setLoadingMembers(true);
    try {
      const result = await api.getWorkspaceMembers(currentWorkspace.id, session.access_token);
      if (result.success) {
        setMembers(result.members || []);
      }
    } catch (error: any) {
      console.error('Error loading members:', error);
    } finally {
      setLoadingMembers(false);
    }
  };

  const loadActivity = async () => {
    if (!currentWorkspace || !session?.access_token) return;
    
    setLoadingActivity(true);
    try {
      const result = await api.getWorkspaceActivity(currentWorkspace.id, session.access_token);
      if (result.success) {
        setActivities(result.activities || []);
      }
    } catch (error: any) {
      console.error('Error loading activity:', error);
    } finally {
      setLoadingActivity(false);
    }
  };

  const loadComments = async (documentId: string) => {
    if (!currentWorkspace || !session?.access_token) return;
    
    try {
      const result = await api.getDocumentComments(currentWorkspace.id, documentId, session.access_token);
      if (result.success) {
        setComments(result.comments || []);
      }
    } catch (error: any) {
      console.error('Error loading comments:', error);
    }
  };

  const handleAddComment = async () => {
    if (!currentWorkspace || !session?.access_token || !selectedDocId || !newComment.trim()) return;
    
    try {
      await api.addComment(currentWorkspace.id, selectedDocId, newComment, session.access_token);
      setNewComment('');
      await loadComments(selectedDocId);
      await loadActivity();
    } catch (error: any) {
      console.error('Error adding comment:', error);
      alert('Failed to add comment: ' + error.message);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    if (!currentWorkspace || !session?.access_token) return;
    
    if (!confirm('Are you sure you want to remove this member?')) return;
    
    try {
      await api.removeWorkspaceMember(currentWorkspace.id, memberId, session.access_token);
      await loadMembers();
      await loadActivity();
    } catch (error: any) {
      console.error('Error removing member:', error);
      alert('Failed to remove member: ' + error.message);
    }
  };

  const handleUnshareDocument = async (documentId: string) => {
    if (!currentWorkspace || !session?.access_token) return;
    
    if (!confirm('Are you sure you want to unshare this document?')) return;
    
    try {
      await api.unshareDocument(currentWorkspace.id, documentId, session.access_token);
      await loadDocuments();
      await loadActivity();
    } catch (error: any) {
      console.error('Error unsharing document:', error);
      alert('Failed to unshare document: ' + error.message);
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role) {
      case 'owner':
        return <Crown className="w-4 h-4 text-yellow-400" />;
      case 'admin':
        return <Shield className="w-4 h-4 text-purple-400" />;
      case 'editor':
        return <Edit3 className="w-4 h-4 text-blue-400" />;
      default:
        return <Eye className="w-4 h-4 text-gray-400" />;
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
  };

  // Show document viewer if a document is selected
  if (viewingDocumentId) {
    return (
      <DocumentViewer
        documentId={viewingDocumentId}
        workspaceId={currentWorkspace?.id}
        onClose={() => setViewingDocumentId(null)}
      />
    );
  }

  if (!currentWorkspace) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-12 text-center">
        <Users className="w-16 h-16 text-slate-600 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-white mb-2">No Workspace Selected</h3>
        <p className="text-gray-400">
          Select a workspace from the list or create a new one to start collaborating.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Workspace Header */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">{currentWorkspace.name}</h2>
            {currentWorkspace.description && (
              <p className="text-gray-400">{currentWorkspace.description}</p>
            )}
            <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
              <span className="flex items-center gap-1">
                <Users className="w-4 h-4" />
                {currentWorkspace.member_count || 0} members
              </span>
              <span className="flex items-center gap-1">
                <FileText className="w-4 h-4" />
                {currentWorkspace.document_count || 0} documents
              </span>
              <span className="flex items-center gap-1">
                {getRoleIcon(currentWorkspace.user_role || 'viewer')}
                {currentWorkspace.user_role}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-700 flex space-x-1">
        <button
          onClick={() => setActiveTab('documents')}
          className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'documents'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <FileText className="w-4 h-4" />
          Documents
        </button>
        <button
          onClick={() => setActiveTab('members')}
          className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'members'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Users className="w-4 h-4" />
          Members
        </button>
        <button
          onClick={() => setActiveTab('activity')}
          className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 ${
            activeTab === 'activity'
              ? 'text-blue-400 border-b-2 border-blue-400'
              : 'text-gray-400 hover:text-white'
          }`}
        >
          <Activity className="w-4 h-4" />
          Activity
        </button>
        {currentWorkspace.user_role === 'owner' || currentWorkspace.user_role === 'admin' ? (
          <button
            onClick={() => setActiveTab('settings')}
            className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'settings'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Settings className="w-4 h-4" />
            Settings
          </button>
        ) : null}
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === 'documents' && (
          <div className="space-y-4">
            {loadingDocs ? (
              <div className="text-center py-8 text-gray-400">Loading documents...</div>
            ) : documents.length === 0 ? (
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 text-center">
                <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-gray-400">No documents shared in this workspace yet.</p>
                <p className="text-sm text-gray-500 mt-2">
                  Upload a document and share it with this workspace to get started.
                </p>
              </div>
            ) : (
              <div className="grid gap-4">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 hover:border-slate-600 transition-colors"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-white font-medium mb-1">
                          {doc.documents?.filename || 'Unknown Document'}
                        </h3>
                        <p className="text-sm text-gray-400 mb-2">
                          Shared {formatDate(doc.shared_at)}
                        </p>
                        <div className="flex items-center gap-3 text-sm text-gray-500">
                          <span>{doc.documents?.page_count || 0} pages</span>
                          <span>{doc.documents?.chunk_count || 0} chunks</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => setViewingDocumentId(doc.document_id)}
                          className="px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                          title="Open Document"
                        >
                          <ExternalLink className="w-4 h-4" />
                          Open
                        </button>
                        <button
                          onClick={() => {
                            setSelectedDocId(doc.document_id);
                            setShowComments(true);
                            loadComments(doc.document_id);
                          }}
                          className="p-2 text-blue-400 hover:bg-slate-700 rounded-lg transition-colors"
                          title="View Comments"
                        >
                          <MessageSquare className="w-4 h-4" />
                        </button>
                        {(currentWorkspace.user_role === 'owner' ||
                          currentWorkspace.user_role === 'admin' ||
                          currentWorkspace.user_role === 'editor') && (
                          <button
                            onClick={() => handleUnshareDocument(doc.document_id)}
                            className="p-2 text-red-400 hover:bg-slate-700 rounded-lg transition-colors"
                            title="Unshare"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'members' && (
          <div className="space-y-4">
            {(currentWorkspace.user_role === 'owner' || currentWorkspace.user_role === 'admin') && (
              <button
                onClick={() => setShowAddMember(!showAddMember)}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
              >
                <UserPlus className="w-4 h-4" />
                Add Member
              </button>
            )}

            {showAddMember && (
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
                <h3 className="text-white font-medium mb-3">Invite Team Member</h3>
                <p className="text-sm text-gray-400 mb-3">
                  Enter their User ID to invite them to this workspace. They can find their User ID on their dashboard.
                </p>
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      User ID
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., 550e8400-e29b-41d4-a716-446655440000"
                      value={newMemberEmail}
                      onChange={(e) => setNewMemberEmail(e.target.value)}
                      className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      💡 Ask them to copy their User ID from their dashboard
                    </p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-300 mb-2">
                      Role
                    </label>
                    <select
                      value={newMemberRole}
                      onChange={(e) => setNewMemberRole(e.target.value)}
                      className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="viewer">Viewer - Can view documents and add comments</option>
                      <option value="editor">Editor - Can also share documents</option>
                      <option value="admin">Admin - Can manage members and settings</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={async () => {
                        if (!newMemberEmail.trim()) return;
                        
                        // Basic UUID validation
                        const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
                        if (!uuidRegex.test(newMemberEmail.trim())) {
                          alert('Please enter a valid User ID (UUID format)');
                          return;
                        }
                        
                        try {
                          await api.addWorkspaceMember(
                            currentWorkspace.id,
                            newMemberEmail.trim(),
                            newMemberRole,
                            session!.access_token
                          );
                          alert('Successfully added member to the workspace!');
                          setNewMemberEmail('');
                          setShowAddMember(false);
                          await loadMembers();
                          await loadActivity();
                        } catch (error: any) {
                          alert(error.message || 'Failed to add member');
                        }
                      }}
                      className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors font-medium"
                    >
                      Add Member
                    </button>
                    <button
                      onClick={() => {
                        setShowAddMember(false);
                        setNewMemberEmail('');
                      }}
                      className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              </div>
            )}

            {loadingMembers ? (
              <div className="text-center py-8 text-gray-400">Loading members...</div>
            ) : (
              <div className="grid gap-3">
                {members.map((member) => (
                  <div
                    key={member.id}
                    className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 flex items-center justify-between"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-bold">
                        {member.profiles?.full_name?.charAt(0) ||
                          member.profiles?.email?.charAt(0) ||
                          '?'}
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-white font-medium">
                            {member.profiles?.full_name || member.profiles?.email || 'Unknown'}
                          </span>
                          {getRoleIcon(member.role)}
                          <span className="text-xs text-gray-500 capitalize">{member.role}</span>
                        </div>
                        <div className="text-sm text-gray-400">
                          Joined {formatDate(member.joined_at)}
                        </div>
                      </div>
                    </div>
                    {member.role !== 'owner' &&
                      (currentWorkspace.user_role === 'owner' ||
                        currentWorkspace.user_role === 'admin') && (
                        <button
                          onClick={() => handleRemoveMember(member.user_id)}
                          className="p-2 text-red-400 hover:bg-slate-700 rounded-lg transition-colors"
                          title="Remove Member"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'activity' && (
          <div className="space-y-3">
            {loadingActivity ? (
              <div className="text-center py-8 text-gray-400">Loading activity...</div>
            ) : activities.length === 0 ? (
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-8 text-center">
                <Clock className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-gray-400">No activity yet.</p>
              </div>
            ) : (
              activities.map((activity) => (
                <div
                  key={activity.id}
                  className="bg-slate-800/50 border border-slate-700 rounded-lg p-4"
                >
                  <div className="flex items-start gap-3">
                    <Activity className="w-5 h-5 text-blue-400 mt-0.5" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-white font-medium">
                          {activity.profiles?.full_name || activity.profiles?.email || 'Someone'}
                        </span>
                        <span className="text-gray-400">{activity.action.replace(/_/g, ' ')}</span>
                      </div>
                      <div className="text-sm text-gray-500">{formatDate(activity.created_at)}</div>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6">
            <h3 className="text-lg font-bold text-white mb-4">Workspace Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Workspace Name
                </label>
                <input
                  type="text"
                  defaultValue={currentWorkspace.name}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Description
                </label>
                <textarea
                  defaultValue={currentWorkspace.description || ''}
                  rows={3}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="pt-4 border-t border-slate-700">
                <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors">
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Comments Modal */}
      {showComments && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
            <div className="p-4 border-b border-slate-700 flex items-center justify-between">
              <h3 className="text-lg font-bold text-white">Comments</h3>
              <button
                onClick={() => {
                  setShowComments(false);
                  setSelectedDocId(null);
                  setComments([]);
                }}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-400" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {comments.length === 0 ? (
                <div className="text-center py-8 text-gray-400">No comments yet.</div>
              ) : (
                comments.map((comment) => (
                  <div key={comment.id} className="bg-slate-700/50 rounded-lg p-3">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
                        {comment.profiles?.full_name?.charAt(0) ||
                          comment.profiles?.email?.charAt(0) ||
                          '?'}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-white font-medium text-sm">
                            {comment.profiles?.full_name || comment.profiles?.email || 'Unknown'}
                          </span>
                          <span className="text-xs text-gray-500">
                            {formatDate(comment.created_at)}
                          </span>
                        </div>
                        <p className="text-gray-300 text-sm">{comment.content}</p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="p-4 border-t border-slate-700">
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Add a comment..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddComment()}
                  className="flex-1 px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleAddComment}
                  disabled={!newComment.trim()}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                >
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

