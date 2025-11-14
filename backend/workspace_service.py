"""
Collaborative Workspace Service
Enables team collaboration, document sharing, and activity tracking
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
import uuid


class WorkspaceRole(str, Enum):
    """User roles within a workspace"""
    OWNER = "owner"
    ADMIN = "admin"
    EDITOR = "editor"
    VIEWER = "viewer"


class WorkspaceService:
    """
    Service for managing collaborative workspaces
    Handles workspace creation, membership, permissions, and activities
    """
    
    def __init__(self, supabase_client):
        """
        Initialize workspace service
        
        Args:
            supabase_client: Supabase client instance
        """
        self.supabase = supabase_client
        print("[WORKSPACE] Workspace service initialized")
    
    # ==================== WORKSPACE MANAGEMENT ====================
    
    def create_workspace(
        self,
        name: str,
        description: Optional[str],
        owner_id: str,
        settings: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new collaborative workspace
        
        Args:
            name: Workspace name
            description: Workspace description
            owner_id: User ID of the workspace creator
            settings: Optional workspace settings (visibility, features, etc.)
            
        Returns:
            Created workspace data
        """
        try:
            workspace_id = str(uuid.uuid4())
            
            # Default settings
            default_settings = {
                "visibility": "private",  # private or public
                "allow_document_upload": True,
                "allow_comments": True,
                "allow_annotations": True,
                "require_approval": False
            }
            
            if settings:
                default_settings.update(settings)
            
            workspace_data = {
                "id": workspace_id,
                "name": name,
                "description": description,
                "owner_id": owner_id,
                "settings": default_settings,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            # Create workspace
            result = self.supabase.table("workspaces").insert(workspace_data).execute()
            
            # Add owner as member
            self.add_member(
                workspace_id=workspace_id,
                user_id=owner_id,
                role=WorkspaceRole.OWNER,
                added_by=owner_id
            )
            
            # Log activity
            self.log_activity(
                workspace_id=workspace_id,
                user_id=owner_id,
                action="workspace_created",
                details={"workspace_name": name}
            )
            
            print(f"[WORKSPACE] Created workspace: {workspace_id} - {name}")
            
            return {
                "success": True,
                "workspace": result.data[0] if result.data else workspace_data
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error creating workspace: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_workspace(self, workspace_id: str, user_id: str) -> Dict[str, Any]:
        """
        Get workspace details (if user has access)
        
        Args:
            workspace_id: Workspace ID
            user_id: User ID requesting access
            
        Returns:
            Workspace data with member information
        """
        try:
            # Check if user is a member
            if not self.is_member(workspace_id, user_id):
                return {
                    "success": False,
                    "error": "Access denied. You are not a member of this workspace."
                }
            
            # Get workspace
            workspace_result = self.supabase.table("workspaces").select("*").eq("id", workspace_id).execute()
            
            if not workspace_result.data:
                return {
                    "success": False,
                    "error": "Workspace not found"
                }
            
            workspace = workspace_result.data[0]
            
            # Get user's role in this workspace
            user_role = self.get_member_role(workspace_id, user_id)
            workspace["user_role"] = user_role.value if user_role else None
            
            # Get members
            members = self.get_members(workspace_id)
            
            # Get document count
            doc_count_result = self.supabase.table("workspace_documents").select("id", count="exact").eq("workspace_id", workspace_id).execute()
            
            workspace["member_count"] = len(members.get("members", []))
            workspace["document_count"] = doc_count_result.count if hasattr(doc_count_result, 'count') else 0
            workspace["members"] = members.get("members", [])
            
            return {
                "success": True,
                "workspace": workspace
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error getting workspace: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_user_workspaces(self, user_id: str) -> Dict[str, Any]:
        """
        List all workspaces a user is a member of
        
        Args:
            user_id: User ID
            
        Returns:
            List of workspaces
        """
        try:
            # Get workspaces where user is a member
            member_result = self.supabase.table("workspace_members").select("workspace_id, role, joined_at").eq("user_id", user_id).execute()
            
            if not member_result.data:
                return {
                    "success": True,
                    "workspaces": []
                }
            
            workspace_ids = [m["workspace_id"] for m in member_result.data]
            
            # Get workspace details
            workspaces_result = self.supabase.table("workspaces").select("*").in_("id", workspace_ids).execute()
            
            # Combine data
            workspaces = []
            for workspace in workspaces_result.data:
                # Find user's role
                member_data = next((m for m in member_result.data if m["workspace_id"] == workspace["id"]), None)
                
                workspace["user_role"] = member_data["role"] if member_data else None
                workspace["joined_at"] = member_data["joined_at"] if member_data else None
                
                # Get member count
                members_count = self.supabase.table("workspace_members").select("id", count="exact").eq("workspace_id", workspace["id"]).execute()
                workspace["member_count"] = members_count.count if hasattr(members_count, 'count') else 0
                
                workspaces.append(workspace)
            
            return {
                "success": True,
                "workspaces": workspaces
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error listing workspaces: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_workspace(
        self,
        workspace_id: str,
        user_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update workspace details (requires admin/owner permissions)
        
        Args:
            workspace_id: Workspace ID
            user_id: User making the update
            updates: Fields to update (name, description, settings)
            
        Returns:
            Updated workspace data
        """
        try:
            # Check permissions
            if not self.has_permission(workspace_id, user_id, [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]):
                return {
                    "success": False,
                    "error": "Permission denied. Only owners and admins can update workspace settings."
                }
            
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.supabase.table("workspaces").update(updates).eq("id", workspace_id).execute()
            
            # Log activity
            self.log_activity(
                workspace_id=workspace_id,
                user_id=user_id,
                action="workspace_updated",
                details={"fields_updated": list(updates.keys())}
            )
            
            return {
                "success": True,
                "workspace": result.data[0] if result.data else None
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error updating workspace: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def delete_workspace(self, workspace_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete a workspace (owner only)
        
        Args:
            workspace_id: Workspace ID
            user_id: User requesting deletion
            
        Returns:
            Success status
        """
        try:
            # Check if user is owner
            if not self.has_permission(workspace_id, user_id, [WorkspaceRole.OWNER]):
                return {
                    "success": False,
                    "error": "Permission denied. Only the workspace owner can delete it."
                }
            
            # Delete related data (members, documents, activities, comments)
            self.supabase.table("workspace_members").delete().eq("workspace_id", workspace_id).execute()
            self.supabase.table("workspace_documents").delete().eq("workspace_id", workspace_id).execute()
            self.supabase.table("workspace_activities").delete().eq("workspace_id", workspace_id).execute()
            self.supabase.table("document_comments").delete().eq("workspace_id", workspace_id).execute()
            
            # Delete workspace
            self.supabase.table("workspaces").delete().eq("id", workspace_id).execute()
            
            print(f"[WORKSPACE] Deleted workspace: {workspace_id}")
            
            return {
                "success": True,
                "message": "Workspace deleted successfully"
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error deleting workspace: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # ==================== MEMBER MANAGEMENT ====================
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Look up a user by their email address from Supabase Auth
        Uses the get_user_id_by_email() SQL function to query auth.users
        
        Args:
            email: User's email address
            
        Returns:
            User data if found, None otherwise
        """
        try:
            email_clean = email.lower().strip()
            
            # Use the SQL function to look up user from auth.users
            # This function is created by SIMPLE_EMAIL_LOOKUP.sql
            result = self.supabase.rpc(
                "get_user_id_by_email",
                {"user_email": email_clean}
            ).execute()
            
            if result.data and len(result.data) > 0:
                user_data = result.data[0]
                print(f"[WORKSPACE] Found user: {user_data.get('email')} (ID: {user_data.get('id')})")
                return user_data
            
            print(f"[WORKSPACE] No user found with email: {email}")
            print(f"[WORKSPACE] Make sure:")
            print(f"  1. User has signed up with Supabase Auth")
            print(f"  2. The get_user_id_by_email() function exists (run SIMPLE_EMAIL_LOOKUP.sql)")
            print(f"  3. Email is correct: '{email_clean}'")
            return None
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "function" in error_msg and "does not exist" in error_msg:
                print(f"[WORKSPACE] ERROR: get_user_id_by_email() function not found!")
                print(f"[WORKSPACE] Run SIMPLE_EMAIL_LOOKUP.sql in Supabase SQL Editor to create it.")
            else:
                print(f"[WORKSPACE] Error looking up user by email: {e}")
                import traceback
                traceback.print_exc()
            
            return None
    
    def add_member_by_email(
        self,
        workspace_id: str,
        email: str,
        role: WorkspaceRole,
        added_by: str
    ) -> Dict[str, Any]:
        """
        Add a member to a workspace by their email address
        
        Args:
            workspace_id: Workspace ID
            email: Email address of user to add
            role: Role to assign
            added_by: User adding the member
            
        Returns:
            Success status with user info
        """
        try:
            # Look up user by email
            user = self.get_user_by_email(email)
            
            if not user:
                return {
                    "success": False,
                    "error": f"No user found with email: {email}. They need to sign up first."
                }
            
            user_id = user.get("id")
            
            # Check if already a member
            if self.is_member(workspace_id, user_id):
                return {
                    "success": False,
                    "error": f"{email} is already a member of this workspace."
                }
            
            # Add the member
            return self.add_member(workspace_id, user_id, role, added_by)
            
        except Exception as e:
            print(f"[WORKSPACE] Error adding member by email: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_member(
        self,
        workspace_id: str,
        user_id: str,
        role: WorkspaceRole,
        added_by: str
    ) -> Dict[str, Any]:
        """
        Add a member to a workspace
        
        Args:
            workspace_id: Workspace ID
            user_id: User to add
            role: Role to assign
            added_by: User adding the member
            
        Returns:
            Success status
        """
        try:
            member_data = {
                "workspace_id": workspace_id,
                "user_id": user_id,
                "role": role.value,
                "added_by": added_by,
                "joined_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("workspace_members").insert(member_data).execute()
            
            # Log activity
            self.log_activity(
                workspace_id=workspace_id,
                user_id=added_by,
                action="member_added",
                details={"new_member_id": user_id, "role": role.value}
            )
            
            return {
                "success": True,
                "member": result.data[0] if result.data else None
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error adding member: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def remove_member(
        self,
        workspace_id: str,
        user_id: str,
        removed_by: str
    ) -> Dict[str, Any]:
        """
        Remove a member from a workspace
        
        Args:
            workspace_id: Workspace ID
            user_id: User to remove
            removed_by: User removing the member
            
        Returns:
            Success status
        """
        try:
            # Check permissions
            if not self.has_permission(workspace_id, removed_by, [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]):
                return {
                    "success": False,
                    "error": "Permission denied. Only owners and admins can remove members."
                }
            
            # Can't remove the owner
            member_role = self.get_member_role(workspace_id, user_id)
            if member_role == WorkspaceRole.OWNER:
                return {
                    "success": False,
                    "error": "Cannot remove the workspace owner."
                }
            
            self.supabase.table("workspace_members").delete().eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
            
            # Log activity
            self.log_activity(
                workspace_id=workspace_id,
                user_id=removed_by,
                action="member_removed",
                details={"removed_user_id": user_id}
            )
            
            return {
                "success": True,
                "message": "Member removed successfully"
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error removing member: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def update_member_role(
        self,
        workspace_id: str,
        user_id: str,
        new_role: WorkspaceRole,
        updated_by: str
    ) -> Dict[str, Any]:
        """
        Update a member's role
        
        Args:
            workspace_id: Workspace ID
            user_id: User whose role to update
            new_role: New role to assign
            updated_by: User making the change
            
        Returns:
            Success status
        """
        try:
            # Check permissions
            if not self.has_permission(workspace_id, updated_by, [WorkspaceRole.OWNER, WorkspaceRole.ADMIN]):
                return {
                    "success": False,
                    "error": "Permission denied."
                }
            
            # Can't change owner role
            current_role = self.get_member_role(workspace_id, user_id)
            if current_role == WorkspaceRole.OWNER:
                return {
                    "success": False,
                    "error": "Cannot change the owner's role."
                }
            
            result = self.supabase.table("workspace_members").update({"role": new_role.value}).eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
            
            # Log activity
            self.log_activity(
                workspace_id=workspace_id,
                user_id=updated_by,
                action="member_role_updated",
                details={"target_user_id": user_id, "new_role": new_role.value}
            )
            
            return {
                "success": True,
                "member": result.data[0] if result.data else None
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error updating member role: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_members(self, workspace_id: str) -> Dict[str, Any]:
        """
        Get all members of a workspace with their info from auth.users
        
        Args:
            workspace_id: Workspace ID
            
        Returns:
            List of members with their roles, emails, and names
        """
        try:
            # Use SQL function to get members with auth.users info
            result = self.supabase.rpc(
                "get_workspace_members_with_info",
                {"workspace_uuid": workspace_id}
            ).execute()
            
            if result.data:
                # Transform data to match expected format (with nested profiles structure for frontend compatibility)
                members = []
                for member in result.data:
                    members.append({
                        "id": member.get("id"),
                        "workspace_id": member.get("workspace_id"),
                        "user_id": member.get("user_id"),
                        "role": member.get("role"),
                        "added_by": member.get("added_by"),
                        "joined_at": member.get("joined_at"),
                        "profiles": {
                            "id": member.get("user_id"),
                            "email": member.get("user_email"),
                            "full_name": member.get("user_full_name"),
                            "avatar_url": None  # Could be added later if needed
                        }
                    })
                
                print(f"[WORKSPACE] Retrieved {len(members)} members for workspace {workspace_id}")
                return {
                    "success": True,
                    "members": members
                }
            
            return {
                "success": True,
                "members": []
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "function" in error_msg and "does not exist" in error_msg:
                print(f"[WORKSPACE] ERROR: get_workspace_members_with_info() function not found!")
                print(f"[WORKSPACE] Run GET_WORKSPACE_MEMBERS_WITH_INFO.sql in Supabase SQL Editor.")
            else:
                print(f"[WORKSPACE] Error getting members: {e}")
                import traceback
                traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "members": []
            }
    
    # ==================== DOCUMENT SHARING ====================
    
    def share_document(
        self,
        workspace_id: str,
        document_id: str,
        user_id: str,
        permissions: Optional[Dict[str, bool]] = None
    ) -> Dict[str, Any]:
        """
        Share a document with a workspace
        
        Args:
            workspace_id: Workspace ID
            document_id: Document ID to share
            user_id: User sharing the document
            permissions: Optional specific permissions (can_edit, can_delete, can_comment)
            
        Returns:
            Success status
        """
        try:
            # Check if user has access to document and workspace
            if not self.is_member(workspace_id, user_id):
                return {
                    "success": False,
                    "error": "You are not a member of this workspace."
                }
            
            default_permissions = {
                "can_view": True,
                "can_edit": False,
                "can_delete": False,
                "can_comment": True
            }
            
            if permissions:
                default_permissions.update(permissions)
            
            share_data = {
                "workspace_id": workspace_id,
                "document_id": document_id,
                "shared_by": user_id,
                "permissions": default_permissions,
                "shared_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("workspace_documents").insert(share_data).execute()
            
            # Log activity
            self.log_activity(
                workspace_id=workspace_id,
                user_id=user_id,
                action="document_shared",
                details={"document_id": document_id}
            )
            
            return {
                "success": True,
                "shared_document": result.data[0] if result.data else None
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error sharing document: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def unshare_document(
        self,
        workspace_id: str,
        document_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Remove a document from workspace sharing
        
        Args:
            workspace_id: Workspace ID
            document_id: Document ID
            user_id: User removing the share
            
        Returns:
            Success status
        """
        try:
            # Check permissions
            if not self.has_permission(workspace_id, user_id, [WorkspaceRole.OWNER, WorkspaceRole.ADMIN, WorkspaceRole.EDITOR]):
                return {
                    "success": False,
                    "error": "Permission denied."
                }
            
            self.supabase.table("workspace_documents").delete().eq("workspace_id", workspace_id).eq("document_id", document_id).execute()
            
            # Log activity
            self.log_activity(
                workspace_id=workspace_id,
                user_id=user_id,
                action="document_unshared",
                details={"document_id": document_id}
            )
            
            return {
                "success": True,
                "message": "Document unshared successfully"
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error unsharing document: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_workspace_documents(self, workspace_id: str, user_id: str, user_client=None) -> Dict[str, Any]:
        """
        Get all documents shared in a workspace
        
        Args:
            workspace_id: Workspace ID
            user_id: User requesting documents
            user_client: Optional user-authenticated Supabase client (for RLS)
            
        Returns:
            List of shared documents
        """
        try:
            if not self.is_member(workspace_id, user_id):
                return {
                    "success": False,
                    "error": "Access denied."
                }
            
            # Use user client if provided, otherwise fall back to service client
            client = user_client if user_client else self.supabase
            
            # Get workspace_documents first
            wd_result = self.supabase.table("workspace_documents").select("*").eq("workspace_id", workspace_id).order("shared_at", desc=True).execute()
            
            if not wd_result.data:
                return {
                    "success": True,
                    "documents": []
                }
            
            print(f"[WORKSPACE] Found {len(wd_result.data)} workspace_documents entries")
            
            # Get all document IDs
            doc_ids = [wd["document_id"] for wd in wd_result.data]
            print(f"[WORKSPACE] Document IDs to fetch: {doc_ids}")
            
            # Fetch actual document details using the appropriate client
            # This will respect RLS policies when using user_client
            # Select specific fields to ensure we get what we need
            docs_result = client.table("documents").select("id, filename, title, author, page_count, chunk_count, character_count, uploaded_at, user_id").in_("id", doc_ids).execute()
            
            print(f"[WORKSPACE] Fetched {len(docs_result.data) if docs_result.data else 0} documents from documents table")
            
            if docs_result.data:
                print(f"[WORKSPACE] Sample document data: {docs_result.data[0] if docs_result.data else 'None'}")
            
            # Create a map of document data by ID
            docs_by_id = {doc["id"]: doc for doc in (docs_result.data or [])}
            
            # Combine workspace_documents data with document details
            combined_data = []
            for wd in wd_result.data:
                doc_data = docs_by_id.get(wd["document_id"])
                
                if not doc_data:
                    # If document not found, log warning but include entry with minimal data
                    print(f"[WORKSPACE WARNING] Document {wd['document_id']} not found in documents table")
                    doc_data = {
                        "id": wd["document_id"],
                        "filename": "Unknown Document (Not Found)",
                        "title": None,
                        "author": None,
                        "page_count": 0,
                        "chunk_count": 0
                    }
                
                combined_data.append({
                    **wd,
                    "documents": doc_data
                })
            
            return {
                "success": True,
                "documents": combined_data
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error getting workspace documents: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": str(e),
                "documents": []
            }
    
    # ==================== COMMENTS & ANNOTATIONS ====================
    
    def add_comment(
        self,
        workspace_id: str,
        document_id: str,
        user_id: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Add a comment to a document
        
        Args:
            workspace_id: Workspace ID
            document_id: Document ID
            user_id: User adding comment
            content: Comment content
            context: Optional context (page, selection, coordinates)
            
        Returns:
            Created comment
        """
        try:
            if not self.is_member(workspace_id, user_id):
                return {
                    "success": False,
                    "error": "Access denied."
                }
            
            comment_data = {
                "id": str(uuid.uuid4()),
                "workspace_id": workspace_id,
                "document_id": document_id,
                "user_id": user_id,
                "content": content,
                "context": context or {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("document_comments").insert(comment_data).execute()
            
            # Log activity
            self.log_activity(
                workspace_id=workspace_id,
                user_id=user_id,
                action="comment_added",
                details={"document_id": document_id, "comment_preview": content[:50]}
            )
            
            return {
                "success": True,
                "comment": result.data[0] if result.data else None
            }
            
        except Exception as e:
            print(f"[WORKSPACE] Error adding comment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_document_comments(
        self,
        workspace_id: str,
        document_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get all comments for a document with user info from auth.users
        
        Args:
            workspace_id: Workspace ID
            document_id: Document ID
            user_id: User requesting comments
            
        Returns:
            List of comments with user emails and names
        """
        try:
            if not self.is_member(workspace_id, user_id):
                return {
                    "success": False,
                    "error": "Access denied.",
                    "comments": []
                }
            
            # Use SQL function to get comments with auth.users info
            result = self.supabase.rpc(
                "get_document_comments_with_info",
                {
                    "p_workspace_id": workspace_id,
                    "p_document_id": document_id
                }
            ).execute()
            
            if result.data:
                # Transform to match expected format with nested profiles
                comments = []
                for comment in result.data:
                    comments.append({
                        "id": comment.get("id"),
                        "workspace_id": comment.get("workspace_id"),
                        "document_id": comment.get("document_id"),
                        "user_id": comment.get("user_id"),
                        "content": comment.get("content"),
                        "context": comment.get("context"),
                        "created_at": comment.get("created_at"),
                        "updated_at": comment.get("updated_at"),
                        "profiles": {
                            "id": comment.get("user_id"),
                            "email": comment.get("user_email"),
                            "full_name": comment.get("user_full_name"),
                            "avatar_url": None
                        }
                    })
                
                return {
                    "success": True,
                    "comments": comments
                }
            
            return {
                "success": True,
                "comments": []
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "function" in error_msg and "does not exist" in error_msg:
                print(f"[WORKSPACE] ERROR: get_document_comments_with_info() function not found!")
                print(f"[WORKSPACE] Run GET_COMMENTS_AND_ACTIVITIES_WITH_INFO.sql in Supabase SQL Editor.")
            else:
                print(f"[WORKSPACE] Error getting comments: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "comments": []
            }
    
    # ==================== ACTIVITY TRACKING ====================
    
    def log_activity(
        self,
        workspace_id: str,
        user_id: str,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an activity in the workspace
        
        Args:
            workspace_id: Workspace ID
            user_id: User performing the action
            action: Action type
            details: Additional details
        """
        try:
            activity_data = {
                "id": str(uuid.uuid4()),
                "workspace_id": workspace_id,
                "user_id": user_id,
                "action": action,
                "details": details or {},
                "created_at": datetime.utcnow().isoformat()
            }
            
            self.supabase.table("workspace_activities").insert(activity_data).execute()
            
        except Exception as e:
            print(f"[WORKSPACE] Error logging activity: {e}")
    
    def get_activity_feed(
        self,
        workspace_id: str,
        user_id: str,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get activity feed for a workspace with user info from auth.users
        
        Args:
            workspace_id: Workspace ID
            user_id: User requesting feed
            limit: Number of activities to return
            
        Returns:
            List of activities with user emails and names
        """
        try:
            if not self.is_member(workspace_id, user_id):
                return {
                    "success": False,
                    "error": "Access denied.",
                    "activities": []
                }
            
            # Use SQL function to get activities with auth.users info
            result = self.supabase.rpc(
                "get_workspace_activities_with_info",
                {
                    "p_workspace_id": workspace_id,
                    "p_limit": limit
                }
            ).execute()
            
            if result.data:
                # Transform to match expected format with nested profiles
                activities = []
                for activity in result.data:
                    activities.append({
                        "id": activity.get("id"),
                        "workspace_id": activity.get("workspace_id"),
                        "user_id": activity.get("user_id"),
                        "action": activity.get("action"),
                        "details": activity.get("details"),
                        "created_at": activity.get("created_at"),
                        "profiles": {
                            "id": activity.get("user_id"),
                            "email": activity.get("user_email"),
                            "full_name": activity.get("user_full_name"),
                            "avatar_url": None
                        }
                    })
                
                return {
                    "success": True,
                    "activities": activities
                }
            
            return {
                "success": True,
                "activities": []
            }
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "function" in error_msg and "does not exist" in error_msg:
                print(f"[WORKSPACE] ERROR: get_workspace_activities_with_info() function not found!")
                print(f"[WORKSPACE] Run GET_COMMENTS_AND_ACTIVITIES_WITH_INFO.sql in Supabase SQL Editor.")
            else:
                print(f"[WORKSPACE] Error getting activity feed: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "activities": []
            }
    
    # ==================== PERMISSIONS & HELPERS ====================
    
    def is_member(self, workspace_id: str, user_id: str) -> bool:
        """Check if user is a member of workspace"""
        try:
            result = self.supabase.table("workspace_members").select("id").eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
            return len(result.data) > 0
        except:
            return False
    
    def get_member_role(self, workspace_id: str, user_id: str) -> Optional[WorkspaceRole]:
        """Get user's role in workspace"""
        try:
            result = self.supabase.table("workspace_members").select("role").eq("workspace_id", workspace_id).eq("user_id", user_id).execute()
            if result.data:
                return WorkspaceRole(result.data[0]["role"])
            return None
        except:
            return None
    
    def has_permission(
        self,
        workspace_id: str,
        user_id: str,
        required_roles: List[WorkspaceRole]
    ) -> bool:
        """Check if user has required role/permission"""
        user_role = self.get_member_role(workspace_id, user_id)
        return user_role in required_roles if user_role else False

