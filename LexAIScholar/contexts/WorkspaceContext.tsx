'use client';

import React, { createContext, useContext, useEffect, useState } from 'react';
import { useAuth } from './AuthContext';
import { api } from '@/lib/api';

interface Workspace {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  settings: Record<string, any>;
  created_at: string;
  updated_at: string;
  user_role?: string;
  member_count?: number;
  document_count?: number;
}

interface WorkspaceMember {
  id: string;
  workspace_id: string;
  user_id: string;
  role: string;
  joined_at: string;
  profiles?: {
    id: string;
    email: string;
    full_name: string | null;
    avatar_url: string | null;
  };
}

interface WorkspaceContextType {
  workspaces: Workspace[];
  currentWorkspace: Workspace | null;
  loading: boolean;
  error: string | null;
  selectWorkspace: (workspaceId: string | null) => void;
  createWorkspace: (name: string, description: string | null) => Promise<void>;
  updateWorkspace: (workspaceId: string, updates: Partial<Workspace>) => Promise<void>;
  deleteWorkspace: (workspaceId: string) => Promise<void>;
  refreshWorkspaces: () => Promise<void>;
  addMember: (workspaceId: string, userId: string, role: string) => Promise<void>;
  removeMember: (workspaceId: string, memberId: string) => Promise<void>;
  updateMemberRole: (workspaceId: string, memberId: string, role: string) => Promise<void>;
  getMembers: (workspaceId: string) => Promise<WorkspaceMember[]>;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: React.ReactNode }) {
  const { session } = useAuth();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [currentWorkspace, setCurrentWorkspace] = useState<Workspace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshWorkspaces = async () => {
    if (!session?.access_token) {
      setWorkspaces([]);
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await api.getWorkspaces(session.access_token);
      
      if (result.success) {
        setWorkspaces(result.workspaces || []);
      } else {
        setError(result.error || 'Failed to load workspaces');
      }
    } catch (err: any) {
      console.error('Error loading workspaces:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshWorkspaces();
  }, [session]);

  const selectWorkspace = async (workspaceId: string | null) => {
    if (!workspaceId) {
      setCurrentWorkspace(null);
      return;
    }

    if (!session?.access_token) return;

    try {
      const result = await api.getWorkspace(workspaceId, session.access_token);
      if (result.success) {
        setCurrentWorkspace(result.workspace);
      }
    } catch (err: any) {
      console.error('Error selecting workspace:', err);
      setError(err.message);
    }
  };

  const createWorkspace = async (name: string, description: string | null) => {
    if (!session?.access_token) throw new Error('Not authenticated');

    try {
      const result = await api.createWorkspace(name, description, session.access_token);
      
      if (result.success) {
        await refreshWorkspaces();
        // Auto-select the newly created workspace
        if (result.workspace) {
          setCurrentWorkspace(result.workspace);
        }
      } else {
        throw new Error(result.error || 'Failed to create workspace');
      }
    } catch (err: any) {
      console.error('Error creating workspace:', err);
      throw err;
    }
  };

  const updateWorkspace = async (workspaceId: string, updates: Partial<Workspace>) => {
    if (!session?.access_token) throw new Error('Not authenticated');

    try {
      const result = await api.updateWorkspace(workspaceId, updates, session.access_token);
      
      if (result.success) {
        await refreshWorkspaces();
        if (currentWorkspace?.id === workspaceId) {
          setCurrentWorkspace(result.workspace);
        }
      } else {
        throw new Error(result.error || 'Failed to update workspace');
      }
    } catch (err: any) {
      console.error('Error updating workspace:', err);
      throw err;
    }
  };

  const deleteWorkspace = async (workspaceId: string) => {
    if (!session?.access_token) throw new Error('Not authenticated');

    try {
      await api.deleteWorkspace(workspaceId, session.access_token);
      
      if (currentWorkspace?.id === workspaceId) {
        setCurrentWorkspace(null);
      }
      
      await refreshWorkspaces();
    } catch (err: any) {
      console.error('Error deleting workspace:', err);
      throw err;
    }
  };

  const addMember = async (workspaceId: string, userId: string, role: string) => {
    if (!session?.access_token) throw new Error('Not authenticated');

    try {
      await api.addWorkspaceMember(workspaceId, userId, role, session.access_token);
      await refreshWorkspaces();
    } catch (err: any) {
      console.error('Error adding member:', err);
      throw err;
    }
  };

  const removeMember = async (workspaceId: string, memberId: string) => {
    if (!session?.access_token) throw new Error('Not authenticated');

    try {
      await api.removeWorkspaceMember(workspaceId, memberId, session.access_token);
      await refreshWorkspaces();
    } catch (err: any) {
      console.error('Error removing member:', err);
      throw err;
    }
  };

  const updateMemberRole = async (workspaceId: string, memberId: string, role: string) => {
    if (!session?.access_token) throw new Error('Not authenticated');

    try {
      await api.updateMemberRole(workspaceId, memberId, role, session.access_token);
      await refreshWorkspaces();
    } catch (err: any) {
      console.error('Error updating member role:', err);
      throw err;
    }
  };

  const getMembers = async (workspaceId: string): Promise<WorkspaceMember[]> => {
    if (!session?.access_token) throw new Error('Not authenticated');

    try {
      const result = await api.getWorkspaceMembers(workspaceId, session.access_token);
      return result.members || [];
    } catch (err: any) {
      console.error('Error getting members:', err);
      throw err;
    }
  };

  const value = {
    workspaces,
    currentWorkspace,
    loading,
    error,
    selectWorkspace,
    createWorkspace,
    updateWorkspace,
    deleteWorkspace,
    refreshWorkspaces,
    addMember,
    removeMember,
    updateMemberRole,
    getMembers,
  };

  return <WorkspaceContext.Provider value={value}>{children}</WorkspaceContext.Provider>;
}

export function useWorkspace() {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error('useWorkspace must be used within a WorkspaceProvider');
  }
  return context;
}

