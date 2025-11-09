'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import PDFUpload from './PDFUpload';
import SemanticSearch from './SemanticSearch';
import DocumentLibrary from './DocumentLibrary';
import AIChat from './AIChat';
import CaseBrief from './CaseBrief';
import Workspace from './Workspace';
import WorkspaceSelector from './WorkspaceSelector';
import { Upload, Search, Library, Target, Zap, Lock, Lightbulb, Hand, MessageSquare, Scale, Users } from 'lucide-react';

export default function UserDashboard() {
  const { user } = useAuth();
  const { currentWorkspace } = useWorkspace();
  const [refreshDocuments, setRefreshDocuments] = useState(false);
  const [activeTab, setActiveTab] = useState<'upload' | 'search' | 'chat' | 'library' | 'casebrief' | 'workspace'>('chat');

  const fullName = user?.user_metadata?.full_name || 'User';

  const handleUploadSuccess = () => {
    setRefreshDocuments(!refreshDocuments);
    setTimeout(() => {
      setActiveTab('library');
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Welcome Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between mb-4">
            <div className="flex-1">
              <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
                Hello, {fullName}!
                <Hand className="w-10 h-10 text-yellow-400" />
              </h1>
              <p className="text-gray-300 text-lg">
                Welcome to your LexAI Scholar dashboard. Upload PDFs, chat with AI, and collaborate with your team.
              </p>
              {/* User ID Display */}
              <div className="mt-3 flex items-center gap-2">
                <span className="text-sm text-gray-400">Your User ID:</span>
                <code className="px-2 py-1 bg-slate-800 text-blue-400 rounded text-xs font-mono">
                  {user?.id}
                </code>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(user?.id || '');
                    alert('User ID copied to clipboard!');
                  }}
                  className="text-xs px-2 py-1 bg-slate-700 hover:bg-slate-600 text-white rounded transition-colors"
                  title="Copy User ID"
                >
                  Copy
                </button>
                <span className="text-xs text-gray-500">(Share this to be invited to workspaces)</span>
              </div>
            </div>
            <div className="w-72 ml-4">
              <WorkspaceSelector />
            </div>
          </div>
          {currentWorkspace && (
            <div className="bg-blue-900/30 border border-blue-700/50 rounded-lg p-3 mt-4">
              <p className="text-blue-200 text-sm flex items-center gap-2">
                <Users className="w-4 h-4" />
                You're now in the <strong>{currentWorkspace.name}</strong> workspace
              </p>
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="mb-6 flex space-x-2 border-b border-slate-700 overflow-x-auto">
          <button
            onClick={() => setActiveTab('chat')}
            className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'chat'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <MessageSquare className="w-4 h-4" />
            AI Chat
          </button>
          <button
            onClick={() => setActiveTab('casebrief')}
            className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'casebrief'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Scale className="w-4 h-4" />
            Case Briefs
          </button>
          {currentWorkspace && (
            <button
              onClick={() => setActiveTab('workspace')}
              className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 whitespace-nowrap ${
                activeTab === 'workspace'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              <Users className="w-4 h-4" />
              Workspace
            </button>
          )}
          <button
            onClick={() => setActiveTab('search')}
            className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'search'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Search className="w-4 h-4" />
            Search
          </button>
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'upload'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Upload className="w-4 h-4" />
            Upload
          </button>
          <button
            onClick={() => setActiveTab('library')}
            className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 whitespace-nowrap ${
              activeTab === 'library'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Library className="w-4 h-4" />
            Library
          </button>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'chat' && (
            <>
              <AIChat />
              
              {/* Chat Info */}
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
                <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                  <MessageSquare className="w-5 h-5 text-blue-400" />
                  AI Chat Features
                </h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-white font-medium mb-1">Q&A Mode</p>
                    <p className="text-gray-400">Get direct answers to questions with citations</p>
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Conversational</p>
                    <p className="text-gray-400">Natural multi-turn conversations with context</p>
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Summary Mode</p>
                    <p className="text-gray-400">Summarize relevant sections from your docs</p>
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Comparative</p>
                    <p className="text-gray-400">Compare information across documents</p>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'upload' && (
            <>
              <PDFUpload onUploadSuccess={handleUploadSuccess} />
              
              {/* Quick Info */}
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
                <h3 className="text-lg font-bold text-white mb-3">How it works</h3>
                <div className="space-y-3">
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">1</div>
                    <div>
                      <p className="text-white font-medium">Upload PDF</p>
                      <p className="text-gray-400 text-sm">Select a PDF document from your computer</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">2</div>
                    <div>
                      <p className="text-white font-medium">AI Processing</p>
                      <p className="text-gray-400 text-sm">Text extraction, chunking, and embedding generation</p>
                    </div>
                  </div>
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-bold">3</div>
                    <div>
                      <p className="text-white font-medium">Vector Storage</p>
                      <p className="text-gray-400 text-sm">Embeddings stored in Pinecone for semantic search</p>
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'search' && (
            <>
              <SemanticSearch />
              
              {/* Search Tips */}
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
                <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                  <Lightbulb className="w-5 h-5 text-yellow-400" />
                  Search Tips
                </h3>
                <ul className="space-y-2 text-gray-300 text-sm">
                  <li className="flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    <span>Ask questions naturally: "What are the main arguments in this case?"</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    <span>Search by concept: "legal precedents on contract law"</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    <span>Results are ranked by semantic similarity, not exact keyword matches</span>
                  </li>
                  <li className="flex items-start">
                    <span className="text-blue-400 mr-2">•</span>
                    <span>Higher percentage scores indicate more relevant matches</span>
                  </li>
                </ul>
              </div>
            </>
          )}

          {activeTab === 'library' && (
            <DocumentLibrary onRefresh={refreshDocuments} />
          )}

          {activeTab === 'casebrief' && (
            <>
              <CaseBrief />
              
              {/* Case Brief Info */}
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
                <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                  <Scale className="w-5 h-5 text-purple-400" />
                  Case Brief Features
                </h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-white font-medium mb-1">Full Brief Generation</p>
                    <p className="text-gray-400">Comprehensive briefs with facts, issues, holdings, reasoning, and more</p>
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Quick Summaries</p>
                    <p className="text-gray-400">Get concise 2-3 paragraph case summaries instantly</p>
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Case Comparison</p>
                    <p className="text-gray-400">Compare multiple cases to identify similarities and differences</p>
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Export & Share</p>
                    <p className="text-gray-400">Download briefs as text files or copy to clipboard</p>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'workspace' && currentWorkspace && (
            <>
              <Workspace />
              
              {/* Workspace Info */}
              <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
                <h3 className="text-lg font-bold text-white mb-3 flex items-center gap-2">
                  <Users className="w-5 h-5 text-green-400" />
                  Collaborative Features
                </h3>
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-white font-medium mb-1">Team Document Sharing</p>
                    <p className="text-gray-400">Share documents with workspace members and collaborate in real-time</p>
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Comments & Annotations</p>
                    <p className="text-gray-400">Add comments to documents and discuss with your team</p>
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Role-Based Access</p>
                    <p className="text-gray-400">Control permissions with owner, admin, editor, and viewer roles</p>
                  </div>
                  <div>
                    <p className="text-white font-medium mb-1">Activity Feed</p>
                    <p className="text-gray-400">Stay updated with workspace activity and team member actions</p>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Quick Stats */}
        <div className="mt-8 grid md:grid-cols-3 gap-6">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
            <Target className="w-12 h-12 text-blue-400 mb-3" />
            <h3 className="text-lg font-bold text-white mb-2">Semantic Search</h3>
            <p className="text-gray-400 text-sm">
              AI-powered search understands meaning, not just keywords
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
            <Zap className="w-12 h-12 text-yellow-400 mb-3" />
            <h3 className="text-lg font-bold text-white mb-2">Fast Processing</h3>
            <p className="text-gray-400 text-sm">
              Efficient chunking and embedding generation with sentence-transformers
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
            <Lock className="w-12 h-12 text-green-400 mb-3" />
            <h3 className="text-lg font-bold text-white mb-2">Secure Storage</h3>
            <p className="text-gray-400 text-sm">
              Your documents are isolated by user ID in Pinecone vector database
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}

