'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api, ConversationMessage, Citation, RAGResponse } from '@/lib/api';
import { 
  Send, 
  Loader2, 
  Bot, 
  User, 
  FileText, 
  Sparkles, 
  MessageSquare,
  Trash2,
  BookOpen,
  Brain,
  RefreshCw,
  Settings,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Quote
} from 'lucide-react';

interface Message extends ConversationMessage {
  id: string;
  isLoading?: boolean;
}

const QUERY_MODES = [
  { value: 'qa', label: 'Q&A', icon: MessageSquare, description: 'Ask questions about your documents' },
  { value: 'conversational', label: 'Chat', icon: Brain, description: 'Natural conversation with context' },
  { value: 'summary', label: 'Summary', icon: BookOpen, description: 'Summarize document sections' },
  { value: 'comparative', label: 'Compare', icon: Sparkles, description: 'Compare across documents' }
];

export default function AIChat() {
  const { session } = useAuth();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState('conversational');
  const [showSettings, setShowSettings] = useState(false);
  const [temperature, setTemperature] = useState(0.3);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || !session?.access_token || isLoading) {
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputText.trim(),
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    // Add loading message
    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: 'assistant',
      content: '',
      isLoading: true
    };
    setMessages(prev => [...prev, loadingMessage]);

    try {
      // Prepare conversation history (exclude loading message)
      const conversationHistory = messages.map(msg => ({
        role: msg.role,
        content: msg.content
      }));

      console.log('[CHAT] Sending question:', userMessage.content);

      const response: RAGResponse = await api.askQuestion(
        userMessage.content,
        session.access_token,
        mode,
        conversationHistory,
        { temperature }
      );

      console.log('[CHAT] Received response:', response);

      // Replace loading message with actual response
      const assistantMessage: Message = {
        id: loadingMessage.id,
        role: 'assistant',
        content: response.answer,
        timestamp: response.timestamp,
        citations: response.citations,
        isLoading: false
      };

      setMessages(prev => prev.map(msg => 
        msg.id === loadingMessage.id ? assistantMessage : msg
      ));

      // Add follow-up questions if any
      if (response.followup_questions && response.followup_questions.length > 0) {
        // Store followup questions for display
        const updatedMessage = {
          ...assistantMessage,
          followupQuestions: response.followup_questions
        };
        setMessages(prev => prev.map(msg => 
          msg.id === loadingMessage.id ? updatedMessage as Message : msg
        ));
      }

    } catch (error: any) {
      console.error('[CHAT] Error:', error);
      
      // Replace loading message with error
      setMessages(prev => prev.map(msg => 
        msg.id === loadingMessage.id 
          ? {
              ...msg,
              content: `Sorry, I encountered an error: ${error.message}. Please try again.`,
              isLoading: false
            }
          : msg
      ));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearConversation = () => {
    if (confirm('Clear all messages?')) {
      setMessages([]);
    }
  };

  const handleFollowUpClick = (question: string) => {
    setInputText(question);
    inputRef.current?.focus();
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg flex flex-col h-[600px]">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-700">
        <div className="flex items-center gap-3">
          <div className="bg-blue-500/20 p-2 rounded-lg">
            <Brain className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">AI Research Assistant</h2>
            <p className="text-xs text-gray-400">Chat with your documents using GPT-4</p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Mode Selector */}
          <select
            value={mode}
            onChange={(e) => setMode(e.target.value)}
            className="bg-slate-700 border border-slate-600 rounded px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500"
          >
            {QUERY_MODES.map(m => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>

          {/* Settings Toggle */}
          <button
            onClick={() => setShowSettings(!showSettings)}
            className="p-2 text-gray-400 hover:text-white hover:bg-slate-700 rounded transition"
          >
            <Settings className="w-4 h-4" />
          </button>

          {/* Clear Button */}
          <button
            onClick={clearConversation}
            disabled={messages.length === 0}
            className="p-2 text-gray-400 hover:text-red-400 hover:bg-slate-700 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <div className="p-4 bg-slate-700/50 border-b border-slate-700">
          <div className="flex items-center gap-4">
            <label className="text-sm text-gray-300">
              Temperature: {temperature}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={temperature}
              onChange={(e) => setTemperature(parseFloat(e.target.value))}
              className="flex-1"
            />
            <span className="text-xs text-gray-400">
              {temperature < 0.3 ? 'Precise' : temperature < 0.7 ? 'Balanced' : 'Creative'}
            </span>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="bg-blue-500/10 p-4 rounded-full mb-4">
              <Bot className="w-12 h-12 text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Start a Conversation</h3>
            <p className="text-gray-400 text-sm max-w-md">
              Ask questions about your documents, request summaries, or have a natural conversation. 
              I'll provide answers with citations to your sources.
            </p>
            <div className="mt-6 grid grid-cols-2 gap-3 max-w-lg">
              {QUERY_MODES.map(m => {
                const Icon = m.icon;
                return (
                  <div key={m.value} className="bg-slate-700/50 p-3 rounded-lg border border-slate-600">
                    <div className="flex items-center gap-2 mb-1">
                      <Icon className="w-4 h-4 text-blue-400" />
                      <span className="text-sm font-medium text-white">{m.label}</span>
                    </div>
                    <p className="text-xs text-gray-400">{m.description}</p>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <ChatMessage 
              key={message.id} 
              message={message}
              onFollowUpClick={handleFollowUpClick}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-slate-700">
        <div className="flex gap-2">
          <textarea
            ref={inputRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask anything about your documents..."
            className="flex-1 bg-slate-700 border border-slate-600 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 resize-none"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={isLoading || !inputText.trim()}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white px-6 rounded-lg font-medium transition duration-200 flex items-center justify-center"
          >
            {isLoading ? (
              <Loader2 className="animate-spin h-5 w-5" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-400">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>
    </div>
  );
}

interface ChatMessageProps {
  message: Message & { followupQuestions?: string[] };
  onFollowUpClick: (question: string) => void;
}

function ChatMessage({ message, onFollowUpClick }: ChatMessageProps) {
  const [showCitations, setShowCitations] = useState(false);

  if (message.isLoading) {
    return (
      <div className="flex items-start gap-3">
        <div className="bg-blue-500/20 p-2 rounded-lg flex-shrink-0">
          <Bot className="w-5 h-5 text-blue-400" />
        </div>
        <div className="flex-1 bg-slate-700/50 rounded-lg p-4">
          <div className="flex items-center gap-2 text-gray-400">
            <Loader2 className="animate-spin h-4 w-4" />
            <span className="text-sm">Thinking...</span>
          </div>
        </div>
      </div>
    );
  }

  const isUser = message.role === 'user';

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`p-2 rounded-lg flex-shrink-0 ${isUser ? 'bg-green-500/20' : 'bg-blue-500/20'}`}>
        {isUser ? (
          <User className="w-5 h-5 text-green-400" />
        ) : (
          <Bot className="w-5 h-5 text-blue-400" />
        )}
      </div>
      
      <div className={`flex-1 ${isUser ? 'text-right' : ''}`}>
        <div className={`inline-block max-w-[85%] ${isUser ? 'bg-green-600/20 border-green-500/30' : 'bg-slate-700/50 border-slate-600'} border rounded-lg p-4`}>
          <div className="text-white text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>

          {/* Citations */}
          {!isUser && message.citations && message.citations.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-600">
              <button
                onClick={() => setShowCitations(!showCitations)}
                className="flex items-center gap-2 text-xs text-blue-400 hover:text-blue-300 transition"
              >
                <Quote className="w-3 h-3" />
                <span>{message.citations.length} Source{message.citations.length > 1 ? 's' : ''}</span>
                {showCitations ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
              </button>

              {showCitations && (
                <div className="mt-2 space-y-2">
                  {message.citations.map((citation, idx) => (
                    <div key={idx} className="bg-slate-800/50 rounded p-2 text-xs">
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <div className="flex items-center gap-2">
                          <span className="bg-blue-500/20 text-blue-400 px-1.5 py-0.5 rounded font-mono">
                            {citation.source_number}
                          </span>
                          <span className="text-gray-300 font-medium">{citation.filename}</span>
                        </div>
                        <span className="text-gray-500">
                          {(citation.relevance_score * 100).toFixed(0)}% match
                        </span>
                      </div>
                      <p className="text-gray-400 line-clamp-2">{citation.text_preview}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Follow-up Questions */}
          {!isUser && message.followupQuestions && message.followupQuestions.length > 0 && (
            <div className="mt-3 pt-3 border-t border-slate-600">
              <p className="text-xs text-gray-400 mb-2">Suggested follow-ups:</p>
              <div className="space-y-1">
                {message.followupQuestions.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => onFollowUpClick(question)}
                    className="block w-full text-left text-xs text-blue-400 hover:text-blue-300 hover:bg-slate-600/50 rounded p-2 transition"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
        
        {message.timestamp && (
          <div className="text-xs text-gray-500 mt-1 px-2">
            {new Date(message.timestamp).toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}

