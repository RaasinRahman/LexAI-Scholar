from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

# Import our custom services
from pdf_service import PDFProcessor
from vector_service import VectorService

load_dotenv()

app = FastAPI(title="LexAI Scholar API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_6uGvNp_3XAvNGrsf3LKYPzKq42ovqnHatj3J4RJzdx6xhmawsj9jza7K1nskPxsEQrDkfo")

# Initialize supabase client only if credentials are provided
if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("Warning: Supabase credentials not found. Authentication will not work.")

# Initialize PDF Processor
pdf_processor = PDFProcessor()

# Initialize Vector Service (Pinecone)
try:
    vector_service = VectorService(pinecone_api_key=PINECONE_API_KEY)
    print("✓ Vector service initialized successfully")
except Exception as e:
    vector_service = None
    print(f"✗ Failed to initialize vector service: {e}")

# ========================================
# Pydantic Models
# ========================================

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    avatar_url: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: str

class SearchRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5
    min_score: Optional[float] = 0.5

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    title: Optional[str] = None
    author: Optional[str] = None
    page_count: int
    chunk_count: int
    character_count: int
    uploaded_at: str

# ========================================
# Authentication Helper
# ========================================

def get_user_supabase_client(access_token: str) -> Client:
    """
    Create a Supabase client with user's access token for RLS operations
    This ensures RLS policies work correctly
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    # Create a new client with the user's token
    user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    # Set the auth token for this client
    user_client.postgrest.auth(access_token)
    return user_client

async def get_current_user(authorization: Optional[str] = Header(None)):
    """Verify JWT token and return user"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        # Verify token with Supabase
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

# ========================================
# Routes
# ========================================

@app.get("/")
def root():
    return {
        "message": "LexAI Scholar API - Cloud Service Configured Successfully!",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "supabase_configured": supabase is not None,
        "vector_service_configured": vector_service is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

# ========================================
# Authentication Endpoints
# ========================================

@app.post("/auth/signup")
async def sign_up(request: SignUpRequest):
    """Register a new user"""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Create user in Supabase Auth
        response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "full_name": request.full_name
                }
            }
        })
        
        if response.user:
            return {
                "message": "User created successfully",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": request.full_name
                },
                "session": {
                    "access_token": response.session.access_token if response.session else None,
                    "refresh_token": response.session.refresh_token if response.session else None
                }
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to create user")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/signin")
async def sign_in(request: SignInRequest):
    """Sign in an existing user"""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if response.user and response.session:
            return {
                "message": "Sign in successful",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token
                }
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.post("/auth/signout")
async def sign_out(current_user = Depends(get_current_user)):
    """Sign out the current user"""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        supabase.auth.sign_out()
        return {"message": "Signed out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/me")
async def get_current_user_profile(current_user = Depends(get_current_user)):
    """Get current user's profile"""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        user_id = current_user.user.id
        profile = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        if profile.data and len(profile.data) > 0:
            return profile.data[0]
        else:
            # Return basic user info if profile doesn't exist yet
            return {
                "id": user_id,
                "email": current_user.user.email
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/auth/profile")
async def update_profile(
    request: UpdateProfileRequest,
    current_user = Depends(get_current_user)
):
    """Update user profile"""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        user_id = current_user.user.id
        update_data = request.dict(exclude_unset=True)
        
        response = supabase.table("profiles").update(update_data).eq("id", user_id).execute()
        
        return {
            "message": "Profile updated successfully",
            "profile": response.data[0] if response.data else None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========================================
# Document Endpoints (Protected)
# ========================================

@app.get("/documents")
async def get_user_documents(
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """Get all documents for the current user"""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    # Extract access token for user-authenticated Supabase client
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        
        # Create user-authenticated Supabase client for RLS operations
        user_supabase = get_user_supabase_client(access_token)
        
        documents = user_supabase.table("documents").select("*").eq("user_id", user_id).order("uploaded_at", desc=True).execute()
        
        print(f"✓ Retrieved {len(documents.data) if documents.data else 0} documents for user {user_id}")
        
        return documents.data
    except Exception as e:
        print(f"✗ Error retrieving documents: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/study-materials")
async def get_user_study_materials(current_user = Depends(get_current_user)):
    """Get all study materials for the current user"""
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        user_id = current_user.user.id
        materials = supabase.table("study_materials").select("*").eq("user_id", user_id).execute()
        return materials.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Legacy endpoint (keeping for compatibility)
@app.get("/users")
def get_users():
    if supabase is None:
        return {"error": "Supabase credentials not configured"}
    data = supabase.table("profiles").select("*").execute()
    return data.data

# ========================================
# PDF Processing Endpoints
# ========================================

@app.post("/documents/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Upload and process a PDF document
    - Extracts text
    - Generates chunks
    - Creates embeddings
    - Stores in vector database
    """
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured. Cannot store document metadata.")
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Extract access token for user-authenticated Supabase client
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        
        # Create user-authenticated Supabase client for RLS operations
        user_supabase = get_user_supabase_client(access_token)
        
        # Read PDF file
        pdf_content = await file.read()
        
        # Process PDF
        print(f"Processing PDF: {file.filename}")
        processing_result = pdf_processor.process_pdf(pdf_content, file.filename)
        
        # Generate unique document ID
        document_id = str(uuid.uuid4())
        
        # Store chunks in vector database
        print(f"Storing {len(processing_result['chunks'])} chunks in vector database")
        storage_result = vector_service.store_document_chunks(
            chunks=processing_result['chunks'],
            user_id=user_id,
            document_id=document_id
        )
        
        if not storage_result.get("success"):
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to store document: {storage_result.get('error')}"
            )
        
        # Store document metadata in Supabase using user-authenticated client
        try:
            doc_metadata = {
                "id": document_id,
                "user_id": user_id,
                "filename": file.filename,
                "title": processing_result['metadata'].get('title'),
                "author": processing_result['metadata'].get('author'),
                "page_count": processing_result['metadata'].get('page_count', 0),
                "chunk_count": processing_result['chunk_count'],
                "character_count": processing_result['character_count'],
                "file_size_bytes": processing_result['metadata'].get('file_size_bytes', 0),
                "uploaded_at": datetime.utcnow().isoformat()
            }
            
            print(f"Attempting to save document metadata to Supabase...")
            print(f"Document ID: {document_id}, User ID: {user_id}")
            
            # Use user-authenticated client for RLS
            result = user_supabase.table("documents").insert(doc_metadata).execute()
            
            # Check if insert was successful
            if result.data and len(result.data) > 0:
                print(f"✓ Document metadata saved to Supabase: {document_id}")
            else:
                raise Exception("Insert returned no data - possible RLS policy issue")
                
        except Exception as e:
            error_message = str(e)
            print(f"✗ Failed to store metadata in Supabase: {error_message}")
            
            # Provide more helpful error messages
            if "policy" in error_message.lower() or "permission" in error_message.lower():
                error_message = (
                    "Database permission error. Please ensure RLS policies are set up correctly. "
                    "Run the fix_rls_for_upload.sql script in your Supabase SQL editor."
                )
            
            # Clean up: delete from vector database if Supabase fails
            try:
                vector_service.delete_document(document_id, user_id)
                print(f"✓ Rolled back vector database entries for document {document_id}")
            except Exception as cleanup_error:
                print(f"✗ Failed to cleanup vector database: {cleanup_error}")
            
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save document metadata to database: {error_message}"
            )
        
        return {
            "success": True,
            "document_id": document_id,
            "filename": file.filename,
            "metadata": processing_result['metadata'],
            "chunk_count": processing_result['chunk_count'],
            "character_count": processing_result['character_count'],
            "vectors_stored": storage_result.get("vectors_stored", 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@app.post("/documents/search")
async def search_documents(
    request: SearchRequest,
    current_user = Depends(get_current_user)
):
    """
    Semantic search across user's documents
    """
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        user_id = current_user.user.id
        
        # Perform semantic search
        results = vector_service.search_similar(
            query=request.query,
            user_id=user_id,
            top_k=request.top_k or 5,
            min_score=request.min_score or 0.5
        )
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        print(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Delete a document and all its chunks from vector database
    """
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    # Extract access token for user-authenticated Supabase client
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        
        # Delete from vector database
        result = vector_service.delete_document(document_id, user_id)
        
        # Delete from Supabase using user-authenticated client
        if supabase:
            try:
                user_supabase = get_user_supabase_client(access_token)
                user_supabase.table("documents").delete().eq("id", document_id).eq("user_id", user_id).execute()
                print(f"✓ Document deleted from Supabase: {document_id}")
            except Exception as e:
                print(f"Warning: Failed to delete from Supabase: {e}")
        
        return {
            "success": result.get("success", False),
            "message": "Document deleted successfully",
            "document_id": document_id
        }
        
    except Exception as e:
        print(f"Error deleting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Get document metadata
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    # Extract access token for user-authenticated Supabase client
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        
        # Create user-authenticated Supabase client for RLS operations
        user_supabase = get_user_supabase_client(access_token)
        
        result = user_supabase.table("documents").select("*").eq("id", document_id).eq("user_id", user_id).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting document: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")

@app.get("/vector-stats")
async def get_vector_stats(current_user = Depends(get_current_user)):
    """
    Get statistics about the vector database
    """
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        stats = vector_service.get_index_stats()
        return stats
    except Exception as e:
        print(f"Error getting vector stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
