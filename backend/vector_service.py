"""
Vector Embedding and Pinecone Integration Service
Handles embedding generation and vector database operations
"""
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import time
import hashlib


class VectorService:
    """
    Service for generating embeddings and managing vector database operations
    """
    
    def __init__(self, pinecone_api_key: str, index_name: str = "lexai-documents"):
        """
        Initialize the vector service with Pinecone
        
        Args:
            pinecone_api_key: Pinecone API key
            index_name: Name of the Pinecone index to use
        """
        # Initialize embedding model
        # Using 'all-MiniLM-L6-v2' - fast, efficient, 384 dimensions
        print("Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dimension = 384  # Dimension for all-MiniLM-L6-v2
        
        # Initialize Pinecone
        print("Initializing Pinecone...")
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index_name = index_name
        
        # Create or connect to index
        self._initialize_index()
        
    def _initialize_index(self):
        """
        Create Pinecone index if it doesn't exist, or connect to existing one
        """
        try:
            # List existing indexes
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                print(f"Creating new Pinecone index: {self.index_name}")
                
                # Create index with serverless spec (free tier)
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dimension,
                    metric="cosine",  # cosine similarity for semantic search
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"  # Free tier region
                    )
                )
                
                # Wait for index to be ready
                print("Waiting for index to be ready...")
                time.sleep(10)
            else:
                print(f"Connecting to existing index: {self.index_name}")
            
            # Connect to the index
            self.index = self.pc.Index(self.index_name)
            print(f"Successfully connected to index: {self.index_name}")
            
        except Exception as e:
            print(f"Error initializing Pinecone index: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a given text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            embedding = self.embedding_model.encode(text, convert_to_tensor=False)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch (more efficient)
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
            return embeddings.tolist()
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            raise
    
    def _generate_chunk_id(self, user_id: str, filename: str, chunk_id: int) -> str:
        """
        Generate a unique ID for a chunk
        """
        unique_string = f"{user_id}_{filename}_{chunk_id}_{int(time.time())}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def store_document_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        user_id: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate embeddings for chunks and store in Pinecone
        
        Args:
            chunks: List of text chunks with metadata
            user_id: User ID for filtering
            document_id: Optional document ID for tracking
            
        Returns:
            Dictionary with storage results
        """
        try:
            if not chunks:
                return {"success": False, "error": "No chunks to process"}
            
            # Extract texts for batch embedding
            texts = [chunk["text"] for chunk in chunks]
            
            # Generate embeddings in batch
            print(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.generate_embeddings_batch(texts)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = self._generate_chunk_id(
                    user_id, 
                    chunk.get("filename", "unknown"), 
                    i
                )
                
                # Build metadata, ensuring no None values (Pinecone doesn't accept null)
                metadata = {
                    "user_id": user_id,
                    "document_id": document_id or "unknown",
                    "chunk_id": chunk.get("chunk_id", i),
                    "text": chunk["text"][:1000],  # Store first 1000 chars in metadata
                    "filename": chunk.get("filename") or "unknown",
                    "title": chunk.get("title") or "",
                    "author": chunk.get("author") or "",
                    "chunk_length": chunk.get("chunk_length", 0),
                    "start_char": chunk.get("start_char", 0),
                    "end_char": chunk.get("end_char", 0)
                }
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            # Upsert to Pinecone in batches of 100
            batch_size = 100
            print(f"Uploading {len(vectors)} vectors to Pinecone...")
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
            
            return {
                "success": True,
                "chunks_processed": len(chunks),
                "vectors_stored": len(vectors)
            }
            
        except Exception as e:
            print(f"Error storing document chunks: {e}")
            return {"success": False, "error": str(e)}
    
    def search_similar(
        self, 
        query: str, 
        user_id: str,
        top_k: int = 5,
        min_score: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using semantic search
        
        Args:
            query: Search query text
            user_id: User ID for filtering results
            top_k: Number of results to return
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of matching chunks with metadata and scores
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Search in Pinecone with user filter
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"user_id": {"$eq": user_id}}
            )
            
            # Format results
            matches = []
            for match in results.matches:
                if match.score >= min_score:
                    matches.append({
                        "id": match.id,
                        "score": float(match.score),
                        "text": match.metadata.get("text", ""),
                        "filename": match.metadata.get("filename", "unknown"),
                        "title": match.metadata.get("title", ""),
                        "author": match.metadata.get("author", ""),
                        "chunk_id": match.metadata.get("chunk_id", 0),
                        "document_id": match.metadata.get("document_id", "")
                    })
            
            return matches
            
        except Exception as e:
            print(f"Error searching vectors: {e}")
            raise
    
    def delete_document(self, document_id: str, user_id: str) -> Dict[str, Any]:
        """
        Delete all chunks associated with a document
        
        Args:
            document_id: Document ID to delete
            user_id: User ID for verification
            
        Returns:
            Deletion result
        """
        try:
            # Delete by filter
            self.index.delete(
                filter={
                    "document_id": {"$eq": document_id},
                    "user_id": {"$eq": user_id}
                }
            )
            
            return {"success": True, "message": "Document deleted from vector database"}
            
        except Exception as e:
            print(f"Error deleting document: {e}")
            return {"success": False, "error": str(e)}
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the Pinecone index
        """
        try:
            stats = self.index.describe_index_stats()
            return {
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return {"error": str(e)}

