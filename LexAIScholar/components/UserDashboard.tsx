'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import PDFUpload from './PDFUpload';
import SemanticSearch from './SemanticSearch';
import DocumentLibrary from './DocumentLibrary';
import { Upload, Search, Library, Target, Zap, Lock, Lightbulb, Hand } from 'lucide-react';

export default function UserDashboard() {
  const { user } = useAuth();
  const [refreshDocuments, setRefreshDocuments] = useState(false);
  const [activeTab, setActiveTab] = useState<'upload' | 'search' | 'library'>('upload');

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
          <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
            Hello, {fullName}!
            <Hand className="w-10 h-10 text-yellow-400" />
          </h1>
          <p className="text-gray-300 text-lg">
            Welcome to your LexAI Scholar dashboard. Upload PDFs and search with AI-powered semantic search.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="mb-6 flex space-x-2 border-b border-slate-700">
          <button
            onClick={() => setActiveTab('upload')}
            className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'upload'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Upload className="w-4 h-4" />
            Upload
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 ${
              activeTab === 'search'
                ? 'text-blue-400 border-b-2 border-blue-400'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            <Search className="w-4 h-4" />
            Search
          </button>
          <button
            onClick={() => setActiveTab('library')}
            className={`px-4 py-3 font-medium transition-colors flex items-center gap-2 ${
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

