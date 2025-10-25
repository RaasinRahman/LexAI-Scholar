'use client';

import React, { useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import { FileUp, Upload, CheckCircle, XCircle, FileText, BarChart3, FileType, X } from 'lucide-react';

interface UploadResult {
  success: boolean;
  document_id: string;
  filename: string;
  chunk_count: number;
  character_count: number;
  metadata: any;
}

interface PDFUploadProps {
  onUploadSuccess?: (result: UploadResult) => void;
}

export default function PDFUpload({ onUploadSuccess }: PDFUploadProps) {
  const { session } = useAuth();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileSelection(files[0]);
    }
  }, []);

  const handleFileSelection = (file: File) => {
    setError(null);
    setUploadResult(null);
    
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported');
      return;
    }
    
    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      setError('File size must be less than 50MB');
      return;
    }
    
    setSelectedFile(file);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelection(e.target.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('No file selected');
      return;
    }

    if (!session) {
      setError('Not authenticated. Please log in first.');
      return;
    }

    if (!session.access_token) {
      setError('Authentication token missing. Please try logging in again.');
      console.error('Session object:', session);
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadProgress(0);

    try {
      console.log('Starting upload:', selectedFile.name);
      console.log('File size:', selectedFile.size, 'bytes');
      console.log('Using token:', session.access_token.substring(0, 20) + '...');
      
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const result = await api.uploadPDF(selectedFile, session.access_token);
      
      console.log('Upload successful:', result);
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      setUploadResult(result);
      setSelectedFile(null);
      
      if (onUploadSuccess) {
        onUploadSuccess(result);
      }
      
      setTimeout(() => {
        setUploadProgress(0);
      }, 2000);
      
    } catch (err: any) {
      console.error('Upload error:', err);
      const errorMessage = err.message || 'Failed to upload document';
      setError(errorMessage);
      setUploadProgress(0);
    } finally {
      setIsUploading(false);
    }
  };

  const clearSelection = () => {
    setSelectedFile(null);
    setError(null);
    setUploadResult(null);
    setUploadProgress(0);
  };

  return (
    <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-lg p-6">
      <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
        <FileUp className="w-6 h-6" />
        Upload PDF Document
      </h2>

      {/* Success Message */}
      {uploadResult && (
        <div className="mb-4 p-4 bg-green-500/10 border border-green-500 rounded-lg">
          <div className="flex items-start">
            <CheckCircle className="w-5 h-5 text-green-400 mr-2 mt-0.5" />
            <div className="flex-1">
              <p className="text-green-400 font-semibold">Upload Successful!</p>
              <p className="text-green-300 text-sm mt-1">
                <strong>{uploadResult.filename}</strong> has been processed
              </p>
              <div className="grid grid-cols-2 gap-2 mt-2 text-sm text-green-200">
                <div className="flex items-center gap-1">
                  <BarChart3 className="w-3 h-3" />
                  Chunks: {uploadResult.chunk_count}
                </div>
                <div className="flex items-center gap-1">
                  <FileType className="w-3 h-3" />
                  Characters: {uploadResult.character_count.toLocaleString()}
                </div>
                {uploadResult.metadata?.page_count && (
                  <div className="flex items-center gap-1">
                    <FileText className="w-3 h-3" />
                    Pages: {uploadResult.metadata.page_count}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500 rounded-lg">
          <div className="flex items-start">
            <XCircle className="w-5 h-5 text-red-400 mr-2 mt-0.5" />
            <div>
              <p className="text-red-400 font-semibold">Upload Failed</p>
              <p className="text-red-300 text-sm mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Drag & Drop Area */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-all duration-200 ${
          isDragging
            ? 'border-blue-500 bg-blue-500/10'
            : 'border-slate-600 hover:border-blue-500'
        }`}
      >
        <input
          type="file"
          onChange={handleFileSelect}
          accept=".pdf"
          className="hidden"
          id="pdf-upload"
          disabled={isUploading}
        />
        <label
          htmlFor="pdf-upload"
          className="cursor-pointer flex flex-col items-center"
        >
          <svg
            className="w-16 h-16 text-gray-400 mb-4"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
          </svg>
          <span className="text-gray-300 font-medium text-lg mb-2">
            Click to upload or drag and drop
          </span>
          <span className="text-gray-500 text-sm">
            PDF files only (max 50MB)
          </span>
        </label>
      </div>

      {/* Selected File Display */}
      {selectedFile && (
        <div className="mt-4 p-4 bg-slate-700/50 border border-slate-600 rounded-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 flex-1">
              <div className="flex-shrink-0">
                <svg className="w-10 h-10 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-white font-medium truncate">{selectedFile.name}</p>
                <p className="text-gray-400 text-sm">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2 ml-4">
              <button
                onClick={clearSelection}
                disabled={isUploading}
                className="text-gray-400 hover:text-white p-2 rounded transition"
                title="Remove file"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Progress Bar */}
          {isUploading && (
            <div className="mt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-300">Processing...</span>
                <span className="text-sm text-gray-300">{uploadProgress}%</span>
              </div>
              <div className="w-full bg-slate-600 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-blue-500 h-full transition-all duration-300 ease-out"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="text-xs text-gray-400 mt-2">
                Extracting text, generating embeddings, and storing in vector database...
              </p>
            </div>
          )}

          {/* Upload Button */}
          {!isUploading && (
            <button
              onClick={handleUpload}
              className="mt-4 w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition duration-200 flex items-center justify-center space-x-2"
            >
              <Upload className="w-5 h-5" />
              <span>Upload & Process Document</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}

