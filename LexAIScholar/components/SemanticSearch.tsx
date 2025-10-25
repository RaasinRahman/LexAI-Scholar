'use client';

import React, { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api, SearchResult } from '@/lib/api';
import { Search, Loader2, XCircle, FileText, User, Target, Sparkles, ThumbsUp, Pin, Copy, ExternalLink, Lightbulb, Info } from 'lucide-react';

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
      console.log('[SEARCH] Searching for:', query);
      const response = await api.searchDocuments(
        query.trim(),
        session.access_token,
        10,
        0.25
      );
      
      const endTime = Date.now();
      setSearchTime(endTime - startTime);
      
      console.log('[SUCCESS] Search results:', response);
      setResults(response.results);
    } catch (err: any) {
      console.error('[ERROR] Search error:', err);
      setError(err.message || 'Search failed');
      setResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  const highlightText = (text: string, query: string): JSX.Element => {
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
    if (score >= 0.7) return 'text-green-400';
    if (score >= 0.5) return 'text-blue-400';
    if (score >= 0.35) return 'text-yellow-400';
    return 'text-orange-400';
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 0.7) return 'Excellent Match';
    if (score >= 0.5) return 'Very Good';
    if (score >= 0.35) return 'Good Match';
    return 'Relevant';
  };

  const getRelevanceBadge = (score: number): { icon: React.ElementType; label: string; color: string } => {
    if (score >= 0.7) return { icon: Target, label: 'Highly Relevant', color: 'bg-green-500/20 text-green-300 border-green-500' };
    if (score >= 0.5) return { icon: Sparkles, label: 'Very Relevant', color: 'bg-blue-500/20 text-blue-300 border-blue-500' };
    if (score >= 0.35) return { icon: ThumbsUp, label: 'Relevant', color: 'bg-yellow-500/20 text-yellow-300 border-yellow-500' };
    return { icon: Pin, label: 'May be Relevant', color: 'bg-orange-500/20 text-orange-300 border-orange-500' };
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
        <Search className="w-6 h-6" />
        Semantic Search
      </h2>
      
      <p className="text-gray-300 text-sm mb-4 flex items-center gap-2">
        <Info className="w-4 h-4 text-blue-400" />
        <span><span className="font-semibold">Q&A Optimized Search</span> - Ask full questions in natural language. 
        Uses specialized question-answer AI model (multi-qa-mpnet) for best results.</span>
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
            <Search className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
          </div>
          <button
            type="submit"
            disabled={isSearching || !query.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg font-medium transition duration-200 flex items-center space-x-2"
          >
            {isSearching ? (
              <>
                <Loader2 className="animate-spin h-5 w-5" />
                <span>Searching...</span>
              </>
            ) : (
              <>
                <Search className="w-5 h-5" />
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
            <XCircle className="w-5 h-5 text-red-400 mr-2 mt-0.5" />
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
                  <div className="flex items-center space-x-2 mb-2">
                    <span className="text-blue-400 font-medium text-sm">
                      #{index + 1}
                    </span>
                    <h3 className="text-white font-semibold truncate">
                      {result.title || result.filename}
                    </h3>
                    {(() => {
                      const badge = getRelevanceBadge(result.score);
                      const IconComponent = badge.icon;
                      return (
                        <span className={`text-xs px-2 py-0.5 rounded border ${badge.color} flex items-center gap-1`}>
                          <IconComponent className="w-3 h-3" />
                          <span>{badge.label}</span>
                        </span>
                      );
                    })()}
                  </div>
                  <div className="flex items-center space-x-3 text-xs text-gray-400">
                    <span className="flex items-center gap-1">
                      <FileText className="w-3 h-3" />
                      {result.filename}
                    </span>
                    {result.author && (
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {result.author}
                      </span>
                    )}
                    <span>Section #{result.chunk_id + 1}</span>
                  </div>
                </div>
                <div className="flex flex-col items-end ml-4">
                  <div className={`text-2xl font-bold ${getScoreColor(result.score)}`}>
                    {(result.score * 100).toFixed(0)}%
                  </div>
                  <div className={`text-xs ${getScoreColor(result.score)}`}>
                    {getScoreLabel(result.score)}
                  </div>
                </div>
              </div>

              {/* Result Content */}
              <div className="bg-slate-800/50 rounded p-4 mb-3 border border-slate-700/50">
                <div className="flex items-start mb-2">
                  <span className="text-gray-500 text-xs font-semibold uppercase tracking-wide mr-2">Content:</span>
                </div>
                <p className="text-gray-200 text-sm leading-relaxed whitespace-pre-line">
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
                  className="text-xs text-gray-400 hover:text-white px-3 py-1 rounded bg-slate-600/50 hover:bg-slate-600 transition flex items-center gap-1"
                >
                  <Copy className="w-3 h-3" />
                  Copy
                </button>
                <button className="text-xs text-gray-400 hover:text-white px-3 py-1 rounded bg-slate-600/50 hover:bg-slate-600 transition flex items-center gap-1">
                  <ExternalLink className="w-3 h-3" />
                  View Document
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
            <p className="text-gray-500 text-sm mb-4">
              Try adjusting your search query or upload more documents
            </p>
            <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 text-left max-w-2xl mx-auto">
              <p className="text-blue-400 font-semibold text-sm mb-3 flex items-center gap-2">
                <Lightbulb className="w-4 h-4" />
                Search Tips for Better Results:
              </p>
              <ul className="text-gray-400 text-xs space-y-2 list-disc list-inside">
                <li><span className="font-semibold text-gray-300">Be specific but natural:</span> Ask questions like "What are the main findings?" instead of just "findings"</li>
                <li><span className="font-semibold text-gray-300">Use complete questions:</span> "What courses did I take?" works better than "courses"</li>
                <li><span className="font-semibold text-gray-300">Upload more documents:</span> More content = better search results</li>
                <li><span className="font-semibold text-gray-300">Wait for processing:</span> Give documents 10-15 seconds to be indexed after upload</li>
                <li><span className="font-semibold text-gray-300">Check Document Library:</span> Verify your documents are uploaded successfully</li>
              </ul>
            </div>
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

