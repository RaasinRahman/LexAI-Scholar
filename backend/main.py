from fastapi import FastAPI, HTTPException, Depends, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from pdf_service import PDFProcessor
from vector_service import VectorService
from rag_service import RAGService
from case_brief_service import CaseBriefService
from workspace_service import WorkspaceService, WorkspaceRole

load_dotenv()

app = FastAPI(title="LexAI Scholar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "pcsk_6uGvNp_3XAvNGrsf3LKYPzKq42ovqnHatj3J4RJzdx6xhmawsj9jza7K1nskPxsEQrDkfo")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if SUPABASE_URL and SUPABASE_KEY:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    supabase = None
    print("Warning: Supabase credentials not found. Authentication will not work.")

pdf_processor = PDFProcessor()

try:
    vector_service = VectorService(pinecone_api_key=PINECONE_API_KEY)
    print("[SUCCESS] Vector service initialized successfully")
except Exception as e:
    vector_service = None
    print(f"[ERROR] Failed to initialize vector service: {e}")

try:
    if OPENAI_API_KEY:
        rag_service = RAGService(openai_api_key=OPENAI_API_KEY)
        print("[SUCCESS] RAG service initialized successfully")
    else:
        rag_service = None
        print("[WARNING] OpenAI API key not found. RAG features will be disabled.")
except Exception as e:
    rag_service = None
    print(f"[ERROR] Failed to initialize RAG service: {e}")

try:
    if OPENAI_API_KEY:
        case_brief_service = CaseBriefService(openai_api_key=OPENAI_API_KEY)
        print("[SUCCESS] Case Brief service initialized successfully")
    else:
        case_brief_service = None
        print("[WARNING] OpenAI API key not found. Case Brief features will be disabled.")
except Exception as e:
    case_brief_service = None
    print(f"[ERROR] Failed to initialize Case Brief service: {e}")

try:
    if supabase:
        workspace_service = WorkspaceService(supabase_client=supabase)
        print("[SUCCESS] Workspace service initialized successfully")
    else:
        workspace_service = None
        print("[WARNING] Supabase not configured. Workspace features will be disabled.")
except Exception as e:
    workspace_service = None
    print(f"[ERROR] Failed to initialize Workspace service: {e}")

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
    top_k: Optional[int] = 10
    min_score: Optional[float] = 0.25

class RAGQueryRequest(BaseModel):
    query: str
    mode: Optional[str] = "qa"  # qa, summary, comparative, conversational
    top_k: Optional[int] = 5
    min_score: Optional[float] = 0.3
    conversation_history: Optional[List[Dict[str, str]]] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 1000

class CaseBriefRequest(BaseModel):
    document_id: str
    brief_type: Optional[str] = "full"  # full or summary
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 2500

class CaseBriefCompareRequest(BaseModel):
    document_ids: List[str]
    comparison_focus: Optional[str] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 1500

class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None
    citations: Optional[List[Dict[str, Any]]] = None

class CreateWorkspaceRequest(BaseModel):
    name: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class UpdateWorkspaceRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None

class AddMemberRequest(BaseModel):
    user_id: str
    role: str  # owner, admin, editor, viewer

class InviteMemberByEmailRequest(BaseModel):
    email: EmailStr
    role: str  # owner, admin, editor, viewer

class UpdateMemberRoleRequest(BaseModel):
    user_id: str
    role: str

class ShareDocumentRequest(BaseModel):
    workspace_id: str
    document_id: str
    permissions: Optional[Dict[str, bool]] = None

class AddCommentRequest(BaseModel):
    workspace_id: str
    document_id: str
    content: str
    context: Optional[Dict[str, Any]] = None

class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    title: Optional[str] = None
    author: Optional[str] = None
    page_count: int
    chunk_count: int
    character_count: int
    uploaded_at: str

class CreateAnnotationRequest(BaseModel):
    workspace_id: Optional[str] = None
    document_id: str
    annotation_type: str  # highlight, note, comment
    start_pos: int
    end_pos: int
    text_content: str
    note_content: Optional[str] = None
    color: Optional[str] = "#ffeb3b"  # Default yellow

class UpdateAnnotationRequest(BaseModel):
    note_content: Optional[str] = None
    color: Optional[str] = None

def get_user_supabase_client(access_token: str) -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    user_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    user_client.postgrest.auth(access_token)
    return user_client

async def get_current_user(authorization: Optional[str] = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")

@app.get("/")
def root():
    return {
        "message": "LexAI Scholar API - Cloud Service Configured Successfully!",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "supabase_configured": supabase is not None,
        "vector_service_configured": vector_service is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/auth/signup")
async def sign_up(request: SignUpRequest):
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
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
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        supabase.auth.sign_out()
        return {"message": "Signed out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/auth/me")
async def get_current_user_profile(current_user = Depends(get_current_user)):
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        user_id = current_user.user.id
        profile = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        if profile.data and len(profile.data) > 0:
            return profile.data[0]
        else:
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

@app.get("/documents")
async def get_user_documents(
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        
        # Create user-authenticated Supabase client for RLS operations
        user_supabase = get_user_supabase_client(access_token)
        
        documents = user_supabase.table("documents").select("*").eq("user_id", user_id).order("uploaded_at", desc=True).execute()
        
        print(f"[INFO] Retrieved {len(documents.data) if documents.data else 0} documents for user {user_id}")
        
        return documents.data
    except Exception as e:
        print(f"[ERROR] Error retrieving documents: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/study-materials")
async def get_user_study_materials(current_user = Depends(get_current_user)):
    if supabase is None:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        user_id = current_user.user.id
        materials = supabase.table("study_materials").select("*").eq("user_id", user_id).execute()
        return materials.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/users")
def get_users():
    if supabase is None:
        return {"error": "Supabase credentials not configured"}
    data = supabase.table("profiles").select("*").execute()
    return data.data

@app.post("/documents/upload")
async def upload_pdf(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured. Cannot store document metadata.")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        
        user_supabase = get_user_supabase_client(access_token)
        
        pdf_content = await file.read()
        
        print(f"Processing PDF: {file.filename}")
        processing_result = pdf_processor.process_pdf(pdf_content, file.filename)
        
        document_id = str(uuid.uuid4())
        
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
            
            result = user_supabase.table("documents").insert(doc_metadata).execute()
            
            if result.data and len(result.data) > 0:
                print(f"[SUCCESS] Document metadata saved to Supabase: {document_id}")
            else:
                raise Exception("Insert returned no data - possible RLS policy issue")
                
        except Exception as e:
            error_message = str(e)
            print(f"[ERROR] Failed to store metadata in Supabase: {error_message}")
            
            if "policy" in error_message.lower() or "permission" in error_message.lower():
                error_message = (
                    "Database permission error. Please ensure RLS policies are set up correctly. "
                    "Run the fix_rls_for_upload.sql script in your Supabase SQL editor."
                )
            
            
            try:
                vector_service.delete_document(document_id, user_id)
                print(f"[INFO] Rolled back vector database entries for document {document_id}")
            except Exception as cleanup_error:
                print(f"[ERROR] Failed to cleanup vector database: {cleanup_error}")
            
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
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        user_id = current_user.user.id
        
        print(f"[SEARCH] Search Request:")
        print(f"   User ID: {user_id}")
        print(f"   Query: '{request.query}'")
        print(f"   Top K: {request.top_k or 5}")
        print(f"   Min Score: {request.min_score or 0.3}")
        
        results = vector_service.search_similar(
            query=request.query,
            user_id=user_id,
            top_k=request.top_k or 10,
            min_score=request.min_score or 0.25
        )
        
        print(f"[INFO] Found {len(results)} results")
        if results:
            print(f"   Top match score: {results[0]['score']:.3f}")
        
        return {
            "query": request.query,
            "results": results,
            "count": len(results)
        }
        
    except Exception as e:
        print(f"[ERROR] Error searching documents: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/chat/ask")
async def ask_question_rag(
    request: RAGQueryRequest,
    current_user = Depends(get_current_user)
):
    """
    RAG endpoint: Retrieve relevant context and generate AI answer with citations
    Supports multiple modes: qa, summary, comparative, conversational
    """
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    if not rag_service:
        raise HTTPException(status_code=503, detail="RAG service not available. OpenAI API key not configured.")
    
    try:
        user_id = current_user.user.id
        
        print(f"[RAG] Processing query: '{request.query}'")
        print(f"[RAG] Mode: {request.mode}, User: {user_id}")
        
        # Step 1: Retrieve relevant context using vector search
        search_results = vector_service.search_similar(
            query=request.query,
            user_id=user_id,
            top_k=request.top_k or 5,
            min_score=request.min_score or 0.3
        )
        
        if not search_results:
            return {
                "success": True,
                "answer": "I couldn't find relevant information in your documents to answer this question. Please try uploading more documents or rephrasing your query.",
                "citations": [],
                "sources_found": 0,
                "query": request.query
            }
        
        print(f"[RAG] Found {len(search_results)} relevant chunks")
        
        # Step 2: Generate answer with LLM using retrieved context
        rag_result = rag_service.generate_answer(
            query=request.query,
            context_chunks=search_results,
            mode=request.mode or "qa",
            conversation_history=request.conversation_history,
            temperature=request.temperature or 0.3,
            max_tokens=request.max_tokens or 1000
        )
        
        # Step 3: Generate follow-up questions
        followup_questions = []
        if rag_result.get("success"):
            try:
                followup_questions = rag_service.generate_followup_questions(
                    request.query,
                    rag_result.get("answer", ""),
                    search_results
                )
            except Exception as e:
                print(f"[RAG] Could not generate follow-ups: {e}")
        
        print(f"[RAG] Response generated successfully")
        
        return {
            "success": rag_result.get("success", False),
            "answer": rag_result.get("answer", ""),
            "citations": rag_result.get("citations", []),
            "sources_found": len(search_results),
            "context_chunks_used": rag_result.get("context_chunks_used", 0),
            "followup_questions": followup_questions,
            "model": rag_result.get("model"),
            "mode": request.mode,
            "usage": rag_result.get("usage", {}),
            "timestamp": rag_result.get("timestamp"),
            "query": request.query
        }
        
    except Exception as e:
        print(f"[RAG] Error in RAG endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"RAG processing failed: {str(e)}")

@app.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        
        result = vector_service.delete_document(document_id, user_id)
        
        if supabase:
            try:
                user_supabase = get_user_supabase_client(access_token)
                user_supabase.table("documents").delete().eq("id", document_id).eq("user_id", user_id).execute()
                print(f"[SUCCESS] Document deleted from Supabase: {document_id}")
            except Exception as e:
                print(f"[WARNING] Failed to delete from Supabase: {e}")
        
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
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
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

@app.get("/documents/{document_id}/content")
async def get_document_content(
    document_id: str,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Retrieve the full text content of a document, reconstructed from chunks in order.
    """
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        user_supabase = get_user_supabase_client(access_token)
        
        # Try to get document - RLS will handle access control
        # The RLS policy allows access if user owns it OR if it's shared via workspace
        doc_result = user_supabase.table("documents").select("*").eq("id", document_id).execute()
        
        if not doc_result.data or len(doc_result.data) == 0:
            # Document not found or user doesn't have access (blocked by RLS)
            raise HTTPException(status_code=404, detail="Document not found or access denied")
        
        document = doc_result.data[0]
        
        # Query vector store for all chunks of this document
        query_results = vector_service.search_by_filter(
            filter_dict={"document_id": document_id},
            top_k=10000  # Get all chunks
        )
        
        # Sort chunks by chunk_id to maintain order
        sorted_chunks = sorted(query_results.get("matches", []), key=lambda x: x.get("metadata", {}).get("chunk_id", 0))
        
        # Reconstruct full text
        full_text_parts = []
        chunks_data = []
        
        for match in sorted_chunks:
            metadata = match.get("metadata", {})
            chunk_text = metadata.get("text", "")
            
            chunks_data.append({
                "chunk_id": metadata.get("chunk_id", 0),
                "text": chunk_text,
                "start_char": metadata.get("start_char", 0),
                "end_char": metadata.get("end_char", 0),
            })
            
            full_text_parts.append(chunk_text)
        
        full_text = "\n\n".join(full_text_parts)
        
        return {
            "success": True,
            "document_id": document_id,
            "document_name": document.get("filename", ""),
            "title": document.get("title"),
            "author": document.get("author"),
            "full_text": full_text,
            "chunks": chunks_data,
            "total_chunks": len(chunks_data),
            "character_count": len(full_text)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error getting document content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get document content: {str(e)}")

@app.post("/documents/{document_id}/annotations")
async def create_annotation(
    document_id: str,
    request: CreateAnnotationRequest,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Create an annotation (highlight, note, or comment) on a document.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        user_supabase = get_user_supabase_client(access_token)
        
        annotation_id = str(uuid.uuid4())
        
        annotation_data = {
            "id": annotation_id,
            "document_id": document_id,
            "workspace_id": request.workspace_id,
            "user_id": user_id,
            "annotation_type": request.annotation_type,
            "start_pos": request.start_pos,
            "end_pos": request.end_pos,
            "text_content": request.text_content,
            "note_content": request.note_content,
            "color": request.color,
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = user_supabase.table("document_annotations").insert(annotation_data).execute()
        
        return {
            "success": True,
            "annotation": result.data[0] if result.data else annotation_data
        }
        
    except Exception as e:
        print(f"Error creating annotation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create annotation: {str(e)}")

@app.get("/documents/{document_id}/annotations")
async def get_annotations(
    document_id: str,
    workspace_id: Optional[str] = None,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Get all annotations for a document.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_supabase = get_user_supabase_client(access_token)
        
        query = user_supabase.table("document_annotations").select("""
            *,
            profiles(full_name, email)
        """).eq("document_id", document_id)
        
        if workspace_id:
            query = query.eq("workspace_id", workspace_id)
        
        result = query.order("created_at").execute()
        
        return {
            "success": True,
            "annotations": result.data or []
        }
        
    except Exception as e:
        print(f"Error getting annotations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get annotations: {str(e)}")

@app.put("/annotations/{annotation_id}")
async def update_annotation(
    annotation_id: str,
    request: UpdateAnnotationRequest,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Update an annotation's content or color.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_supabase = get_user_supabase_client(access_token)
        
        update_data = {}
        if request.note_content is not None:
            update_data["note_content"] = request.note_content
        if request.color is not None:
            update_data["color"] = request.color
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        update_data["updated_at"] = datetime.utcnow().isoformat()
        
        result = user_supabase.table("document_annotations").update(update_data).eq("id", annotation_id).execute()
        
        return {
            "success": True,
            "annotation": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error updating annotation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update annotation: {str(e)}")

@app.delete("/annotations/{annotation_id}")
async def delete_annotation(
    annotation_id: str,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Delete an annotation.
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_supabase = get_user_supabase_client(access_token)
        
        result = user_supabase.table("document_annotations").delete().eq("id", annotation_id).execute()
        
        return {
            "success": True,
            "message": "Annotation deleted"
        }
        
    except Exception as e:
        print(f"Error deleting annotation: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete annotation: {str(e)}")

@app.get("/vector-stats")
async def get_vector_stats(current_user = Depends(get_current_user)):
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        stats = vector_service.get_index_stats()
        return stats
    except Exception as e:
        print(f"Error getting vector stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/case-brief/generate")
async def generate_case_brief(
    request: CaseBriefRequest,
    current_user = Depends(get_current_user)
):
    """
    Generate a structured case brief from a legal document
    Supports full briefs or quick summaries
    """
    if not case_brief_service:
        raise HTTPException(status_code=503, detail="Case Brief service not available. OpenAI API key not configured.")
    
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        user_id = current_user.user.id
        
        print(f"[CASE BRIEF] Generating {request.brief_type} brief for document {request.document_id}")
        
        # Retrieve all chunks for this document from vector database
        # We use a broad query to get all chunks from the document
        all_chunks = vector_service.search_similar(
            query="case law facts issues holding reasoning disposition court decision",
            user_id=user_id,
            top_k=100,  # Get many chunks
            min_score=0.0  # Accept all chunks from the document
        )
        
        # Filter to only chunks from the requested document
        document_chunks = [
            chunk for chunk in all_chunks 
            if chunk.get('document_id') == request.document_id
        ]
        
        if not document_chunks:
            raise HTTPException(
                status_code=404, 
                detail=f"No content found for document {request.document_id}. Document may not exist or may not belong to you."
            )
        
        print(f"[CASE BRIEF] Found {len(document_chunks)} chunks for document")
        
        # Generate the case brief
        brief_result = case_brief_service.generate_case_brief(
            document_chunks=document_chunks,
            document_id=request.document_id,
            brief_type=request.brief_type,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        if not brief_result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate case brief: {brief_result.get('error', 'Unknown error')}"
            )
        
        print(f"[CASE BRIEF] Successfully generated brief")
        
        return brief_result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CASE BRIEF] Error in case brief endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Case brief generation failed: {str(e)}")

@app.post("/case-brief/extract-section")
async def extract_case_section(
    document_id: str,
    section: str,
    current_user = Depends(get_current_user)
):
    """
    Extract a specific section from a case (facts, issues, holding, reasoning, etc.)
    """
    if not case_brief_service:
        raise HTTPException(status_code=503, detail="Case Brief service not available")
    
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        user_id = current_user.user.id
        
        # Retrieve document chunks
        all_chunks = vector_service.search_similar(
            query=f"case {section}",
            user_id=user_id,
            top_k=100,
            min_score=0.0
        )
        
        document_chunks = [
            chunk for chunk in all_chunks 
            if chunk.get('document_id') == document_id
        ]
        
        if not document_chunks:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Extract the section
        result = case_brief_service.extract_specific_section(
            document_chunks=document_chunks,
            section=section
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CASE BRIEF] Error extracting section: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/case-brief/compare")
async def compare_cases(
    request: CaseBriefCompareRequest,
    current_user = Depends(get_current_user)
):
    """
    Compare multiple case briefs and provide comparative analysis
    """
    if not case_brief_service:
        raise HTTPException(status_code=503, detail="Case Brief service not available")
    
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        user_id = current_user.user.id
        
        if len(request.document_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 documents required for comparison")
        
        print(f"[CASE BRIEF] Comparing {len(request.document_ids)} cases")
        
        # Generate briefs for each document
        case_briefs = []
        for doc_id in request.document_ids:
            # Get document chunks
            all_chunks = vector_service.search_similar(
                query="case law legal",
                user_id=user_id,
                top_k=100,
                min_score=0.0
            )
            
            document_chunks = [
                chunk for chunk in all_chunks 
                if chunk.get('document_id') == doc_id
            ]
            
            if not document_chunks:
                print(f"[WARNING] No chunks found for document {doc_id}")
                continue
            
            # Generate brief
            brief = case_brief_service.generate_case_brief(
                document_chunks=document_chunks,
                document_id=doc_id,
                brief_type="summary",  # Use summary for comparison to save tokens
                temperature=0.2,
                max_tokens=1500
            )
            
            if brief.get("success"):
                case_briefs.append(brief)
        
        if len(case_briefs) < 2:
            raise HTTPException(
                status_code=400, 
                detail="Could not generate briefs for at least 2 documents"
            )
        
        # Compare the cases
        comparison = case_brief_service.compare_cases(
            case_briefs=case_briefs,
            comparison_focus=request.comparison_focus,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[CASE BRIEF] Error comparing cases: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/user-vectors")
async def debug_user_vectors(current_user = Depends(get_current_user)):
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        user_id = current_user.user.id
        
        index_stats = vector_service.get_index_stats()
        
        test_results = vector_service.search_similar(
            query="test education university course work experience",
            user_id=user_id,
            top_k=100,
            min_score=0.0
        )
        
        return {
            "user_id": user_id,
            "total_vectors_in_index": index_stats.get("total_vectors", 0),
            "user_vectors_found": len(test_results),
            "sample_results": test_results[:3] if test_results else [],
            "message": "If user_vectors_found is 0, your documents weren't properly uploaded/embedded"
        }
    except Exception as e:
        print(f"Error in debug endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Debug failed: {str(e)}")

# ==================== WORKSPACE ENDPOINTS ====================

@app.post("/workspaces")
async def create_workspace(
    request: CreateWorkspaceRequest,
    current_user = Depends(get_current_user)
):
    """Create a new collaborative workspace"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        
        result = workspace_service.create_workspace(
            name=request.name,
            description=request.description,
            owner_id=user_id,
            settings=request.settings
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to create workspace"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in create workspace endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspaces")
async def list_workspaces(current_user = Depends(get_current_user)):
    """Get all workspaces the current user is a member of"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        result = workspace_service.list_user_workspaces(user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to list workspaces"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in list workspaces endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspaces/{workspace_id}")
async def get_workspace(
    workspace_id: str,
    current_user = Depends(get_current_user)
):
    """Get workspace details"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        result = workspace_service.get_workspace(workspace_id, user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("error", "Workspace not found"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in get workspace endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/workspaces/{workspace_id}")
async def update_workspace(
    workspace_id: str,
    request: UpdateWorkspaceRequest,
    current_user = Depends(get_current_user)
):
    """Update workspace settings (admin/owner only)"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        updates = request.dict(exclude_unset=True)
        
        result = workspace_service.update_workspace(workspace_id, user_id, updates)
        
        if not result.get("success"):
            raise HTTPException(status_code=403, detail=result.get("error", "Failed to update workspace"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in update workspace endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/workspaces/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a workspace (owner only)"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        result = workspace_service.delete_workspace(workspace_id, user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=403, detail=result.get("error", "Failed to delete workspace"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in delete workspace endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspaces/{workspace_id}/members/invite-by-email")
async def invite_member_by_email(
    workspace_id: str,
    request: InviteMemberByEmailRequest,
    current_user = Depends(get_current_user)
):
    """Invite a member to a workspace by their email address"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        
        # Validate role
        try:
            role = WorkspaceRole(request.role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")
        
        result = workspace_service.add_member_by_email(
            workspace_id=workspace_id,
            email=request.email,
            role=role,
            added_by=user_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to invite member"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in invite by email endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspaces/{workspace_id}/members")
async def add_workspace_member(
    workspace_id: str,
    request: AddMemberRequest,
    current_user = Depends(get_current_user)
):
    """Add a member to a workspace (by user ID - legacy method)"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        
        # Validate role
        try:
            role = WorkspaceRole(request.role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")
        
        result = workspace_service.add_member(
            workspace_id=workspace_id,
            user_id=request.user_id,
            role=role,
            added_by=user_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to add member"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in add member endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspaces/{workspace_id}/members")
async def get_workspace_members(
    workspace_id: str,
    current_user = Depends(get_current_user)
):
    """Get all members of a workspace"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        
        # Check if user is a member
        if not workspace_service.is_member(workspace_id, user_id):
            raise HTTPException(status_code=403, detail="Access denied")
        
        result = workspace_service.get_members(workspace_id)
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in get members endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/workspaces/{workspace_id}/members/{member_id}")
async def remove_workspace_member(
    workspace_id: str,
    member_id: str,
    current_user = Depends(get_current_user)
):
    """Remove a member from a workspace"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        result = workspace_service.remove_member(workspace_id, member_id, user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=403, detail=result.get("error", "Failed to remove member"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in remove member endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/workspaces/{workspace_id}/members/{member_id}/role")
async def update_member_role(
    workspace_id: str,
    member_id: str,
    request: UpdateMemberRoleRequest,
    current_user = Depends(get_current_user)
):
    """Update a member's role"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        
        # Validate role
        try:
            role = WorkspaceRole(request.role)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")
        
        result = workspace_service.update_member_role(
            workspace_id=workspace_id,
            user_id=member_id,
            new_role=role,
            updated_by=user_id
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=403, detail=result.get("error", "Failed to update role"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in update member role endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspaces/documents/share")
async def share_document_with_workspace(
    request: ShareDocumentRequest,
    current_user = Depends(get_current_user)
):
    """Share a document with a workspace"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        
        result = workspace_service.share_document(
            workspace_id=request.workspace_id,
            document_id=request.document_id,
            user_id=user_id,
            permissions=request.permissions
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to share document"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in share document endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/workspaces/{workspace_id}/documents/{document_id}")
async def unshare_document(
    workspace_id: str,
    document_id: str,
    current_user = Depends(get_current_user)
):
    """Remove a document from workspace sharing"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        result = workspace_service.unshare_document(workspace_id, document_id, user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=403, detail=result.get("error", "Failed to unshare document"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in unshare document endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspaces/{workspace_id}/documents")
async def get_workspace_documents(
    workspace_id: str,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """Get all documents shared in a workspace"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    # Extract access token for user-authenticated client
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        
        # Create user-authenticated Supabase client to respect RLS policies
        user_supabase = get_user_supabase_client(access_token)
        
        # Pass user client to workspace service for proper RLS handling
        result = workspace_service.get_workspace_documents(workspace_id, user_id, user_client=user_supabase)
        
        if not result.get("success"):
            raise HTTPException(status_code=403, detail=result.get("error", "Access denied"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in get workspace documents endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/workspaces/comments")
async def add_document_comment(
    request: AddCommentRequest,
    current_user = Depends(get_current_user)
):
    """Add a comment to a document in a workspace"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        
        result = workspace_service.add_comment(
            workspace_id=request.workspace_id,
            document_id=request.document_id,
            user_id=user_id,
            content=request.content,
            context=request.context
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to add comment"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in add comment endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspaces/{workspace_id}/documents/{document_id}/comments")
async def get_document_comments(
    workspace_id: str,
    document_id: str,
    current_user = Depends(get_current_user)
):
    """Get all comments for a document"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        result = workspace_service.get_document_comments(workspace_id, document_id, user_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=403, detail=result.get("error", "Access denied"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in get comments endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/workspaces/{workspace_id}/activity")
async def get_workspace_activity(
    workspace_id: str,
    current_user = Depends(get_current_user),
    limit: int = 50
):
    """Get activity feed for a workspace"""
    if not workspace_service:
        raise HTTPException(status_code=503, detail="Workspace service not available")
    
    try:
        user_id = current_user.user.id
        result = workspace_service.get_activity_feed(workspace_id, user_id, limit)
        
        if not result.get("success"):
            raise HTTPException(status_code=403, detail=result.get("error", "Access denied"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[WORKSPACE] Error in get activity endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
