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
# Use OpenAI embeddings instead of sentence-transformers (memory efficient)
from vector_service_openai import VectorService
from rag_service import RAGService
from case_brief_service import CaseBriefService
from workspace_service import WorkspaceService, WorkspaceRole
from practice_questions_service import PracticeQuestionsService
from analytics_service import AnalyticsService
from study_plan_service import StudyPlanService

load_dotenv()

app = FastAPI(title="LexAI Scholar API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "https://lexai-h2sfrssw1-raasinr-gmailcoms-projects.vercel.app",  # Your production URL
        "https://lexai-eight.vercel.app",  # Your custom domain
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel preview deployments
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
    if PINECONE_API_KEY and OPENAI_API_KEY:
        vector_service = VectorService(
            pinecone_api_key=PINECONE_API_KEY,
            openai_api_key=OPENAI_API_KEY
        )
        print("[SUCCESS] Vector service initialized successfully (using OpenAI embeddings)")
    else:
        vector_service = None
        print("[WARNING] Pinecone or OpenAI API key not found. Vector service disabled.")
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

try:
    if OPENAI_API_KEY:
        practice_questions_service = PracticeQuestionsService(openai_api_key=OPENAI_API_KEY)
        print("[SUCCESS] Practice Questions service initialized successfully")
    else:
        practice_questions_service = None
        print("[WARNING] OpenAI API key not found. Practice Questions features will be disabled.")
except Exception as e:
    practice_questions_service = None
    print(f"[ERROR] Failed to initialize Practice Questions service: {e}")

try:
    analytics_service = AnalyticsService()
    print("[SUCCESS] Analytics service initialized successfully")
except Exception as e:
    analytics_service = None
    print(f"[ERROR] Failed to initialize Analytics service: {e}")

try:
    if OPENAI_API_KEY:
        study_plan_service = StudyPlanService(openai_api_key=OPENAI_API_KEY)
        print("[SUCCESS] Study Plan service initialized successfully")
    else:
        study_plan_service = None
        print("[WARNING] OpenAI API key not found. Study Plan features will be disabled.")
except Exception as e:
    study_plan_service = None
    print(f"[ERROR] Failed to initialize Study Plan service: {e}")

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

class GeneratePracticeQuestionsRequest(BaseModel):
    document_id: str
    question_count: Optional[int] = 5
    question_types: Optional[List[str]] = None  # ['multiple_choice', 'short_answer', 'true_false']
    difficulty: Optional[str] = "medium"  # 'easy', 'medium', 'hard'
    focus_area: Optional[str] = None
    temperature: Optional[float] = 0.7

class GenerateQuizRequest(BaseModel):
    document_ids: List[str]
    quiz_name: str
    question_count: Optional[int] = 10
    question_types: Optional[List[str]] = None
    difficulty: Optional[str] = "medium"

class EvaluateAnswerRequest(BaseModel):
    question: Dict[str, Any]
    user_answer: Any
    temperature: Optional[float] = 0.3

class RecordQuizSessionRequest(BaseModel):
    quiz_id: Optional[str] = None
    document_ids: List[str]
    total_questions: int
    correct_answers: int
    difficulty: str
    question_types: List[str]
    start_time: str
    end_time: Optional[str] = None
    performance_by_type: Optional[Dict[str, Any]] = None
    topics_covered: Optional[List[str]] = None

class GenerateStudyPlanRequest(BaseModel):
    time_commitment: Optional[str] = "moderate"  # light, moderate, intensive
    goals: Optional[Dict[str, Any]] = None

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

# ==================== PRACTICE QUESTIONS ENDPOINTS ====================

@app.post("/practice-questions/generate")
async def generate_practice_questions(
    request: GeneratePracticeQuestionsRequest,
    current_user = Depends(get_current_user)
):
    """
    Generate practice questions from a document
    Supports multiple question types and difficulty levels
    """
    if not practice_questions_service:
        raise HTTPException(status_code=503, detail="Practice Questions service not available. OpenAI API key not configured.")
    
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        user_id = current_user.user.id
        
        print(f"[PRACTICE QUESTIONS] Generating questions for document {request.document_id}")
        
        # Retrieve document chunks from vector database
        all_chunks = vector_service.search_similar(
            query="legal case facts issues holding reasoning",
            user_id=user_id,
            top_k=100,
            min_score=0.0
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
        
        print(f"[PRACTICE QUESTIONS] Found {len(document_chunks)} chunks for document")
        
        # Generate practice questions
        result = practice_questions_service.generate_questions(
            document_chunks=document_chunks,
            document_id=request.document_id,
            question_count=request.question_count or 5,
            question_types=request.question_types,
            difficulty=request.difficulty or "medium",
            focus_area=request.focus_area,
            temperature=request.temperature or 0.7
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate questions: {result.get('error', 'Unknown error')}"
            )
        
        print(f"[PRACTICE QUESTIONS] Successfully generated {result.get('question_count')} questions")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PRACTICE QUESTIONS] Error in generate endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@app.post("/practice-questions/generate-quiz")
async def generate_quiz(
    request: GenerateQuizRequest,
    current_user = Depends(get_current_user)
):
    """
    Generate a comprehensive quiz from multiple documents
    """
    if not practice_questions_service:
        raise HTTPException(status_code=503, detail="Practice Questions service not available")
    
    if not vector_service:
        raise HTTPException(status_code=500, detail="Vector service not configured")
    
    try:
        user_id = current_user.user.id
        
        if len(request.document_ids) < 1:
            raise HTTPException(status_code=400, detail="At least 1 document required for quiz")
        
        print(f"[PRACTICE QUESTIONS] Generating quiz from {len(request.document_ids)} documents")
        
        # Retrieve chunks for all documents
        document_chunks_map = {}
        
        for doc_id in request.document_ids:
            all_chunks = vector_service.search_similar(
                query="legal case facts issues holding reasoning",
                user_id=user_id,
                top_k=100,
                min_score=0.0
            )
            
            document_chunks = [
                chunk for chunk in all_chunks 
                if chunk.get('document_id') == doc_id
            ]
            
            if document_chunks:
                document_chunks_map[doc_id] = document_chunks
        
        if not document_chunks_map:
            raise HTTPException(
                status_code=404,
                detail="No content found for the specified documents"
            )
        
        # Generate quiz
        result = practice_questions_service.generate_quiz(
            document_ids=list(document_chunks_map.keys()),
            document_chunks_map=document_chunks_map,
            quiz_name=request.quiz_name,
            question_count=request.question_count or 10,
            difficulty=request.difficulty or "medium",
            question_types=request.question_types
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate quiz: {result.get('error', 'Unknown error')}"
            )
        
        print(f"[PRACTICE QUESTIONS] Successfully generated quiz with {result.get('question_count')} questions")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PRACTICE QUESTIONS] Error in generate quiz endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Quiz generation failed: {str(e)}")

@app.post("/practice-questions/evaluate")
async def evaluate_answer(
    request: EvaluateAnswerRequest,
    current_user = Depends(get_current_user)
):
    """
    Evaluate a user's answer to a practice question
    Provides feedback and scoring
    """
    if not practice_questions_service:
        raise HTTPException(status_code=503, detail="Practice Questions service not available")
    
    try:
        print(f"[PRACTICE QUESTIONS] Evaluating answer for question type: {request.question.get('type')}")
        
        result = practice_questions_service.evaluate_answer(
            question=request.question,
            user_answer=request.user_answer,
            temperature=request.temperature or 0.3
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to evaluate answer: {result.get('error', 'Unknown error')}"
            )
        
        print(f"[PRACTICE QUESTIONS] Answer evaluated - Correct: {result.get('is_correct')}, Score: {result.get('score')}")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[PRACTICE QUESTIONS] Error in evaluate endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Answer evaluation failed: {str(e)}")

# ==================== ANALYTICS ENDPOINTS ====================

@app.post("/analytics/record-session")
async def record_quiz_session(
    request: RecordQuizSessionRequest,
    current_user = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Record a completed quiz session for analytics tracking
    """
    if not analytics_service:
        raise HTTPException(status_code=503, detail="Analytics service not available")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        user_supabase = get_user_supabase_client(access_token)
        
        # Calculate score percentage
        score_percentage = (request.correct_answers / request.total_questions * 100) if request.total_questions > 0 else 0
        
        # Parse timestamps
        start_time_str = request.start_time
        end_time_str = request.end_time or datetime.utcnow().isoformat()
        
        # Calculate time spent
        try:
            start_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
            time_spent_seconds = int((end_dt - start_dt).total_seconds())
        except:
            time_spent_seconds = 0
        
        # Prepare session data for database
        session_data = {
            "user_id": user_id,
            "quiz_id": request.quiz_id,
            "document_ids": request.document_ids,
            "total_questions": request.total_questions,
            "correct_answers": request.correct_answers,
            "score_percentage": round(score_percentage, 2),
            "difficulty": request.difficulty,
            "question_types": request.question_types,
            "time_spent_seconds": time_spent_seconds,
            "performance_by_type": request.performance_by_type or {},
            "topics_covered": request.topics_covered or [],
            "start_time": start_time_str,
            "completed_at": end_time_str
        }
        
        # Store in Supabase
        result = user_supabase.table("quiz_sessions").insert(session_data).execute()
        
        if not result.data or len(result.data) == 0:
            raise Exception("Failed to insert quiz session into database")
        
        print(f"[ANALYTICS] Recorded quiz session: {score_percentage:.1f}% score, {request.total_questions} questions")
        
        return {
            "success": True,
            "session_id": result.data[0].get("id"),
            "score_percentage": score_percentage,
            "message": "Quiz session recorded successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ANALYTICS] Error recording session: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to record session: {str(e)}")

@app.get("/analytics/progress")
async def get_progress_analytics(
    current_user = Depends(get_current_user),
    time_period_days: Optional[int] = None,
    authorization: str = Header(None)
):
    """
    Get comprehensive progress analytics and metrics
    Returns performance trends, weak areas, and learning statistics
    """
    if not analytics_service:
        raise HTTPException(status_code=503, detail="Analytics service not available")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        user_supabase = get_user_supabase_client(access_token)
        
        print(f"[ANALYTICS] Fetching progress for user {user_id}")
        
        # Build query for quiz history
        query = user_supabase.table("quiz_sessions").select("*").eq("user_id", user_id)
        
        # Apply time period filter if specified
        if time_period_days:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
            query = query.gte("completed_at", cutoff_date.isoformat())
        
        # Fetch quiz history from database
        result = query.order("completed_at", desc=False).execute()
        quiz_history = result.data or []
        
        print(f"[ANALYTICS] Found {len(quiz_history)} quiz sessions")
        
        if not quiz_history:
            return {
                "success": True,
                "message": "No quiz data available yet. Complete some quizzes to see your analytics!",
                "overview": {
                    "total_quizzes": 0,
                    "total_questions_answered": 0,
                    "total_correct_answers": 0,
                    "overall_accuracy": 0,
                    "average_score": 0,
                    "median_score": 0,
                    "days_active": 0
                }
            }
        
        # Calculate progress metrics
        metrics = analytics_service.calculate_progress_metrics(quiz_history)
        
        if not metrics.get("success"):
            raise HTTPException(status_code=500, detail=metrics.get("error", "Failed to calculate metrics"))
        
        # Get knowledge gaps
        gaps = analytics_service.identify_knowledge_gaps(quiz_history)
        
        # Add gaps to metrics
        if gaps.get("success"):
            metrics["gaps"] = gaps.get("gaps", {})
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ANALYTICS] Error getting progress: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/summary")
async def get_performance_summary(
    current_user = Depends(get_current_user),
    time_period_days: Optional[int] = 7,
    authorization: str = Header(None)
):
    """
    Get a summary of performance for a specific time period
    """
    if not analytics_service:
        raise HTTPException(status_code=503, detail="Analytics service not available")
    
    if not supabase:
        raise HTTPException(status_code=500, detail="Database not configured")
    
    access_token = authorization.replace("Bearer ", "") if authorization else None
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token required")
    
    try:
        user_id = current_user.user.id
        user_supabase = get_user_supabase_client(access_token)
        
        # Build query for quiz history
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        
        result = user_supabase.table("quiz_sessions").select("*").eq("user_id", user_id).gte("completed_at", cutoff_date.isoformat()).execute()
        quiz_history = result.data or []
        
        summary = analytics_service.get_performance_summary(quiz_history, time_period_days)
        
        if not summary.get("success"):
            raise HTTPException(status_code=500, detail=summary.get("error", "Failed to get summary"))
        
        return summary
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ANALYTICS] Error getting summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== STUDY PLAN ENDPOINTS ====================

@app.post("/study-plan/generate")
async def generate_study_plan(
    request: GenerateStudyPlanRequest,
    current_user = Depends(get_current_user)
):
    """
    Generate a personalized study plan based on user performance and goals
    """
    if not study_plan_service:
        raise HTTPException(status_code=503, detail="Study Plan service not available. OpenAI API key not configured.")
    
    if not analytics_service:
        raise HTTPException(status_code=503, detail="Analytics service not available")
    
    try:
        user_id = current_user.user.id
        
        print(f"[STUDY PLAN] Generating plan for user {user_id}")
        
        # Get user performance analytics
        quiz_history = []  # TODO: Get from database
        performance = analytics_service.calculate_progress_metrics(quiz_history)
        
        # Get knowledge gaps
        gaps = analytics_service.identify_knowledge_gaps(quiz_history)
        if gaps.get("success"):
            performance["gaps"] = gaps.get("gaps", {})
        
        # Get available documents
        documents = []
        if supabase:
            try:
                docs_result = supabase.table("documents").select("*").eq("user_id", user_id).execute()
                documents = docs_result.data or []
            except Exception as e:
                print(f"[STUDY PLAN] Error fetching documents: {e}")
        
        # Generate study plan
        result = study_plan_service.generate_study_plan(
            user_performance=performance,
            available_documents=documents,
            goals=request.goals,
            time_commitment=request.time_commitment or "moderate"
        )
        
        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate study plan: {result.get('error', 'Unknown error')}"
            )
        
        print(f"[STUDY PLAN] Successfully generated study plan")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[STUDY PLAN] Error generating plan: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/study-plan/recommendations")
async def get_quick_recommendations(
    current_user = Depends(get_current_user)
):
    """
    Get quick study recommendations without generating a full plan
    """
    if not study_plan_service:
        raise HTTPException(status_code=503, detail="Study Plan service not available")
    
    if not analytics_service:
        raise HTTPException(status_code=503, detail="Analytics service not available")
    
    try:
        user_id = current_user.user.id
        
        # Get user performance
        quiz_history = []  # TODO: Get from database
        performance = analytics_service.calculate_progress_metrics(quiz_history)
        
        # Get knowledge gaps
        gaps = analytics_service.identify_knowledge_gaps(quiz_history)
        if gaps.get("success"):
            performance["gaps"] = gaps.get("gaps", {})
        
        # Generate recommendations
        result = study_plan_service.generate_quick_recommendations(
            user_performance=performance,
            recent_quiz_results=quiz_history[-5:] if quiz_history else []
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Failed to generate recommendations"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[STUDY PLAN] Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
