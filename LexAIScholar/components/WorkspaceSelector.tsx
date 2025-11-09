'use client';

import React, { useState } from 'react';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import { Plus, Check, ChevronDown, Users, Loader2 } from 'lucide-react';

export default function WorkspaceSelector() {
  const {
    workspaces,
    currentWorkspace,
    selectWorkspace,
    createWorkspace,
    loading,
  } = useWorkspace();
  
  const [showDropdown, setShowDropdown] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newWorkspaceName, setNewWorkspaceName] = useState('');
  const [newWorkspaceDesc, setNewWorkspaceDesc] = useState('');
  const [creating, setCreating] = useState(false);

  const handleCreateWorkspace = async () => {
    if (!newWorkspaceName.trim()) return;
    
    setCreating(true);
    try {
      await createWorkspace(newWorkspaceName, newWorkspaceDesc || null);
      setNewWorkspaceName('');
      setNewWorkspaceDesc('');
      setShowCreateModal(false);
    } catch (error: any) {
      alert('Failed to create workspace: ' + error.message);
    } finally {
      setCreating(false);
    }
  };

  return (
    <>
      <div className="relative">
        <button
          onClick={() => setShowDropdown(!showDropdown)}
          className="w-full px-4 py-3 bg-slate-800/80 border border-slate-700 rounded-lg text-left flex items-center justify-between hover:border-slate-600 transition-colors"
        >
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <Users className="w-4 h-4 text-white" />
            </div>
            <div>
              <div className="text-sm text-gray-400">Workspace</div>
              <div className="text-white font-medium">
                {currentWorkspace ? currentWorkspace.name : 'Personal'}
              </div>
            </div>
          </div>
          <ChevronDown className={`w-5 h-5 text-gray-400 transition-transform ${showDropdown ? 'rotate-180' : ''}`} />
        </button>

        {showDropdown && (
          <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-50 overflow-hidden">
            {/* Personal workspace option */}
            <button
              onClick={() => {
                selectWorkspace(null);
                setShowDropdown(false);
              }}
              className={`w-full px-4 py-3 text-left hover:bg-slate-700/50 transition-colors flex items-center justify-between ${
                !currentWorkspace ? 'bg-slate-700/30' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center">
                  <Users className="w-4 h-4 text-white" />
                </div>
                <div>
                  <div className="text-white font-medium">Personal</div>
                  <div className="text-xs text-gray-400">Your private documents</div>
                </div>
              </div>
              {!currentWorkspace && <Check className="w-5 h-5 text-blue-400" />}
            </button>

            <div className="border-t border-slate-700 my-1" />

            {loading ? (
              <div className="px-4 py-3 text-gray-400 text-center">
                <Loader2 className="w-5 h-5 animate-spin mx-auto" />
              </div>
            ) : workspaces.length === 0 ? (
              <div className="px-4 py-3 text-gray-400 text-sm text-center">
                No workspaces yet
              </div>
            ) : (
              workspaces.map((workspace) => (
                <button
                  key={workspace.id}
                  onClick={() => {
                    selectWorkspace(workspace.id);
                    setShowDropdown(false);
                  }}
                  className={`w-full px-4 py-3 text-left hover:bg-slate-700/50 transition-colors flex items-center justify-between ${
                    currentWorkspace?.id === workspace.id ? 'bg-slate-700/30' : ''
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-sm font-bold">
                      {workspace.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div className="text-white font-medium">{workspace.name}</div>
                      <div className="text-xs text-gray-400">
                        {workspace.member_count || 0} members
                      </div>
                    </div>
                  </div>
                  {currentWorkspace?.id === workspace.id && (
                    <Check className="w-5 h-5 text-blue-400" />
                  )}
                </button>
              ))
            )}

            <div className="border-t border-slate-700 mt-1" />
            
            <button
              onClick={() => {
                setShowDropdown(false);
                setShowCreateModal(true);
              }}
              className="w-full px-4 py-3 text-left hover:bg-slate-700/50 transition-colors flex items-center gap-3 text-blue-400"
            >
              <Plus className="w-5 h-5" />
              <span className="font-medium">Create Workspace</span>
            </button>
          </div>
        )}
      </div>

      {/* Create Workspace Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 border border-slate-700 rounded-lg max-w-md w-full p-6">
            <h2 className="text-2xl font-bold text-white mb-4">Create Workspace</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Workspace Name *
                </label>
                <input
                  type="text"
                  placeholder="e.g., Legal Research Team"
                  value={newWorkspaceName}
                  onChange={(e) => setNewWorkspaceName(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Description (optional)
                </label>
                <textarea
                  placeholder="What's this workspace for?"
                  value={newWorkspaceDesc}
                  onChange={(e) => setNewWorkspaceDesc(e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleCreateWorkspace}
                  disabled={!newWorkspaceName.trim() || creating}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors font-medium flex items-center justify-center gap-2"
                >
                  {creating ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    'Create Workspace'
                  )}
                </button>
                <button
                  onClick={() => {
                    setShowCreateModal(false);
                    setNewWorkspaceName('');
                    setNewWorkspaceDesc('');
                  }}
                  disabled={creating}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-50 text-white rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

