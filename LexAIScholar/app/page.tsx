'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import AuthModal from '@/components/auth/AuthModal';
import UserDashboard from '@/components/UserDashboard';
import { Scale, FileText, Bot, Library, Search, Lightbulb, Target } from 'lucide-react';

export default function Home() {
  const { user, signOut, loading } = useAuth();
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'signup'>('login');

  const openAuthModal = (mode: 'login' | 'signup') => {
    setAuthMode(mode);
    setAuthModalOpen(true);
  };

  const fullName = user?.user_metadata?.full_name || 'User';

  // Show dashboard if user is logged in
  if (user) {
    return (
      <>
        {/* Navigation for logged in users */}
        <nav className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center gap-2">
                <Scale className="w-6 h-6 text-blue-400" />
                <h1 className="text-2xl font-bold text-white">LexAI Scholar</h1>
              </div>
              <div className="flex items-center space-x-4">
                <span className="text-gray-300 text-sm font-medium">
                  {fullName}
                </span>
                <button
                  onClick={() => signOut()}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition duration-200"
                >
                  Sign Out
                </button>
              </div>
            </div>
          </div>
        </nav>
        <UserDashboard />
      </>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
      {/* Navigation */}
      <nav className="bg-slate-800/50 backdrop-blur-sm border-b border-slate-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <Scale className="w-6 h-6 text-blue-400" />
              <h1 className="text-2xl font-bold text-white">LexAI Scholar</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Home
              </button>
              <button className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                Features
              </button>
              <button className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium">
                About
              </button>
              
              {!loading && (
                <>
                  {user ? (
                    <div className="flex items-center space-x-4">
                      <span className="text-gray-300 text-sm font-medium">
                        {fullName}
                      </span>
                      <button
                        onClick={() => signOut()}
                        className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-md text-sm font-medium transition duration-200"
                      >
                        Sign Out
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => openAuthModal('login')}
                        className="text-gray-300 hover:text-white px-4 py-2 rounded-md text-sm font-medium"
                      >
                        Login
                      </button>
                      <button
                        onClick={() => openAuthModal('signup')}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition duration-200"
                      >
                        Sign Up
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      </nav>
      
      {/* Auth Modal */}
      <AuthModal 
        isOpen={authModalOpen} 
        onClose={() => setAuthModalOpen(false)} 
        initialMode={authMode}
      />

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center mb-16">
          <h2 className="text-5xl md:text-6xl font-bold text-white mb-6">
            AI-Powered Legal Document Analysis
          </h2>
          <p className="text-xl text-gray-300 mb-8 max-w-3xl mx-auto">
            Empower your legal studies with advanced AI technology. Analyze documents, 
            extract key insights, and accelerate your learning journey.
          </p>
          <button 
            onClick={() => user ? null : openAuthModal('signup')}
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-8 rounded-lg text-lg transition duration-200 shadow-lg"
          >
            {user ? 'Get Started' : 'Sign Up to Get Started'}
          </button>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-8 mt-20">
          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6 hover:border-blue-500 transition duration-200">
            <FileText className="w-12 h-12 text-blue-400 mb-4" />
            <h3 className="text-xl font-bold text-white mb-3">Document Upload</h3>
            <p className="text-gray-300">
              Upload and manage your legal documents securely. Support for PDF, DOCX, and more.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6 hover:border-blue-500 transition duration-200">
            <Bot className="w-12 h-12 text-purple-400 mb-4" />
            <h3 className="text-xl font-bold text-white mb-3">AI Analysis</h3>
            <p className="text-gray-300">
              Leverage cutting-edge AI to extract key legal concepts, precedents, and insights.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6 hover:border-blue-500 transition duration-200">
            <Library className="w-12 h-12 text-green-400 mb-4" />
            <h3 className="text-xl font-bold text-white mb-3">Study Tools</h3>
            <p className="text-gray-300">
              Create summaries, flashcards, and study guides automatically from your documents.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6 hover:border-blue-500 transition duration-200">
            <Search className="w-12 h-12 text-cyan-400 mb-4" />
            <h3 className="text-xl font-bold text-white mb-3">Smart Search</h3>
            <p className="text-gray-300">
              Find relevant cases, statutes, and legal principles with intelligent search.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6 hover:border-blue-500 transition duration-200">
            <Lightbulb className="w-12 h-12 text-yellow-400 mb-4" />
            <h3 className="text-xl font-bold text-white mb-3">Case Briefs</h3>
            <p className="text-gray-300">
              Generate comprehensive case briefs with AI-powered analysis of facts and holdings.
            </p>
          </div>

          <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6 hover:border-blue-500 transition duration-200">
            <Target className="w-12 h-12 text-red-400 mb-4" />
            <h3 className="text-xl font-bold text-white mb-3">Practice Questions</h3>
            <p className="text-gray-300">
              Test your knowledge with AI-generated practice questions based on your materials.
            </p>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-20 bg-gradient-to-r from-blue-600 to-blue-800 rounded-lg p-12 text-center">
          <h3 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Legal Studies?
          </h3>
          <p className="text-xl text-blue-100 mb-8">
            Join thousands of law students using AI to excel in their studies.
          </p>
          <button 
            onClick={() => user ? null : openAuthModal('signup')}
            className="bg-white text-blue-600 hover:bg-gray-100 font-bold py-3 px-8 rounded-lg text-lg transition duration-200 shadow-lg"
          >
            {user ? 'Continue Learning' : 'Start Free Trial'}
          </button>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-800/50 backdrop-blur-sm border-t border-slate-700 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-gray-400">
            <p>&copy; 2025 LexAI Scholar. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
