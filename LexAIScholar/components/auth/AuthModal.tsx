'use client';

import React, { useState } from 'react';
import LoginForm from './LoginForm';
import SignupForm from './SignupForm';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialMode?: 'login' | 'signup';
}

export default function AuthModal({ isOpen, onClose, initialMode = 'login' }: AuthModalProps) {
  const [mode, setMode] = useState<'login' | 'signup'>(initialMode);

  if (!isOpen) return null;

  const handleSuccess = () => {
    onClose();
  };

  const toggleMode = () => {
    setMode(mode === 'login' ? 'signup' : 'login');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/70 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative z-10 w-full max-w-md mx-4">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute -top-4 -right-4 bg-slate-700 hover:bg-slate-600 text-white rounded-full p-2 transition duration-200"
          aria-label="Close"
        >
          <svg
            className="w-6 h-6"
            fill="none"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth="2"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {mode === 'login' ? (
          <LoginForm onSuccess={handleSuccess} onToggleForm={toggleMode} />
        ) : (
          <SignupForm onSuccess={handleSuccess} onToggleForm={toggleMode} />
        )}
      </div>
    </div>
  );
}

