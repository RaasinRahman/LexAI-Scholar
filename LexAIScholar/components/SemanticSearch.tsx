'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api, SearchResult } from '@/lib/api';

export default function SemanticSearch() {
  const { session } = useAuth();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchTime, setSearchTime] = useState<number>(0);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!query.trim() || !session?.access_token) {
      return;
    }

    setIsSearching(true);
    setError(null);
    setHasSearched(true);
    
    const startTime = Date.now();

    try {
      const response = await api.searchDocuments(
        query.trim(),
        session.access_token,
        5,
        0.5
      );
      
      const endTime = Date.now();
      setSearchTime(endTime - startTime);
      
      setResults(response.results);
    } catch (err: any) {
      setError(err.message || 'Search failed');
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const highlightText = (text: string, query: string): JSX.Element => {
    // Simple highlighting - in production, use a more sophisticated method
    const lowerText = text.toLowerCase();
    const lowerQuery = query.toLowerCase();
    const words = lowerQuery.split(' ').filter(w => w.length > 2);
    
    let highlighted = text;
    words.forEach(word => {
      const regex = new RegExp(`(${word})`, 'gi');
      highlighted = highlighted.replace(regex, '<mark class="bg-yellow-400/30 text-yellow-200">$1</mark>');
    });
    
    return <span dangerouslySetInnerHTML={{ __html: highlighted }} />;
  };

  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return 'text-green-400';
    if (score >= 0.65) return 'text-blue-400';
    if (score >= 0.5) return 'text-yellow-400';
    return 'text-gray-400';
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 0.8) return 'Excellent Match';
    if (score >= 0.65) return 'Good Match';
    if (score >= 0.5) return 'Fair Match';
    return 'Weak Match';
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-4 flex items-center">
        🔍 Semantic Search
      </h2>
      
      <p className="text-gray-300 text-sm mb-4">
        Search across all your documents using natural language. The AI will find semantically similar content.
      </p>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="mb-6">
        <div className="flex space-x-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything... (e.g., 'What are the key findings about contract law?')"
              className="w-full px-4 py-3 pl-10 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-500/50"
              disabled={isSearching}
            />
            <svg
              className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition duration-200 flex items-center space-x-2"
          >
            {isSearching ? (
              <>
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
                <span>Searching...</span>
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <span>Search</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500 rounded-lg">
          <div className="flex items-start">
            <svg className="w-5 h-5 text-red-400 mr-2 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <p className="text-red-400 font-semibold">Search Failed</p>
              <p className="text-red-300 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Results Summary */}
      {hasSearched && !isSearching && (
        <div className="mb-4 flex items-center justify-between text-sm">
          <div className="text-gray-300">
            Found <span className="font-semibold text-white">{results.length}</span> result{results.length !== 1 ? 's' : ''}
            {results.length > 0 && searchTime > 0 && (
              <span className="text-gray-400"> in {searchTime}ms</span>
            )}
          </div>
          {results.length > 0 && (
            <div className="text-gray-400">
              Sorted by relevance
            </div>
          )}
        </div>
      )}

      {/* Search Results */}
      <div className="space-y-4">
        {results.length > 0 ? (
          results.map((result, index) => (
            <div
              key={result.id}
              className="bg-slate-700/50 border border-slate-600 rounded-lg p-4 hover:border-blue-500 transition duration-200"
            >
              {/* Result Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-blue-400 font-medium text-sm">
                      #{index + 1}
                    </span>
                    <h3 className="text-white font-semibold truncate">
                      {result.title || result.filename}
                    </h3>
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-gray-400">
                    <span>📄 {result.filename}</span>
                    {result.author && <span>✍️ {result.author}</span>}
                    <span>Chunk #{result.chunk_id + 1}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end ml-4">
                  <div className={`text-lg font-bold ${getScoreColor(result.score)}`}>
                    {(result.score * 100).toFixed(0)}%
                  </div>
                  <div className={`text-xs ${getScoreColor(result.score)}`}>
                    {getScoreLabel(result.score)}
                  </div>
                </div>
              </div>

              {/* Result Content */}
              <div className="bg-slate-800/50 rounded p-3 mb-3">
                <p className="text-gray-200 text-sm leading-relaxed">
                  {highlightText(result.text, query)}
                </p>
              </div>

              {/* Result Actions */}
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => {
                    // Copy text to clipboard
                    navigator.clipboard.writeText(result.text);
                  }}
                  className="text-xs text-gray-400 hover:text-white px-3 py-1 rounded bg-slate-600/50 hover:bg-slate-600 transition"
                >
                  📋 Copy
                </button>
                <button className="text-xs text-gray-400 hover:text-white px-3 py-1 rounded bg-slate-600/50 hover:bg-slate-600 transition">
                  🔗 View Document
                </button>
              </div>
            </div>
          ))
        ) : hasSearched && !isSearching ? (
          <div className="text-center py-12">
            <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 className="text-gray-400 font-medium mb-2">No results found</h3>
            <p className="text-gray-500 text-sm">
              Try adjusting your search query or upload more documents
            </p>
          </div>
        ) : !hasSearched ? (
          <div className="text-center py-12">
            <svg className="w-16 h-16 text-gray-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <h3 className="text-gray-400 font-medium mb-2">Start searching</h3>
            <p className="text-gray-500 text-sm">
              Enter a question or topic to search across your documents
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

