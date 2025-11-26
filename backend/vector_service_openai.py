"""
Lightweight Vector Service using OpenAI Embeddings API
Works with Render free tier (no heavy models to load)
"""
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import time
import hashlib
from openai import OpenAI


class VectorService:
    def __init__(self, pinecone_api_key: str, openai_api_key: str, index_name: str = "lexai-qa-index"):
        print("Initializing OpenAI client for embeddings...")
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.embedding_dimension = 1536  # OpenAI text-embedding-3-small dimension
        
        print("Initializing Pinecone...")
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index_name = index_name
        
        self._initialize_index()
        
    def _initialize_index(self):
        try:
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                print(f"Creating new Pinecone index: {self.index_name}")
                
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.embedding_dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region="us-east-1"
                    )
                )
                
                print("Waiting for index to be ready...")
                time.sleep(10)
            else:
                print(f"Connecting to existing index: {self.index_name}")
            
            self.index = self.pc.Index(self.index_name)
            print(f"Successfully connected to index: {self.index_name}")
            
        except Exception as e:
            print(f"Error initializing Pinecone index: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding using OpenAI API (no local model needed)"""
        try:
            processed_text = self._preprocess_text(text)
            response = self.openai_client.embeddings.create(
                input=processed_text,
                model="text-embedding-3-small"  # Smaller, faster, cheaper
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        max_length = 8000  # OpenAI allows up to 8191 tokens
        if len(text) > max_length:
            text = text[:max_length]
        
        text = ' '.join(text.split())
        return text
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batches using OpenAI API"""
        try:
            processed_texts = [self._preprocess_text(text) for text in texts]
            
            # OpenAI allows batching
            response = self.openai_client.embeddings.create(
                input=processed_texts,
                model="text-embedding-3-small"
            )
            
            embeddings = [item.embedding for item in response.data]
            return embeddings
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            raise
    
    def _generate_chunk_id(self, user_id: str, filename: str, chunk_id: int) -> str:
        unique_string = f"{user_id}_{filename}_{chunk_id}_{int(time.time())}"
        return hashlib.md5(unique_string.encode()).hexdigest()
    
    def store_document_chunks(
        self, 
        chunks: List[Dict[str, Any]], 
        user_id: str,
        document_id: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            if not chunks:
                return {"success": False, "error": "No chunks to process"}
            
            texts = [chunk["text"] for chunk in chunks]
            
            print(f"Generating embeddings for {len(texts)} chunks using OpenAI API...")
            embeddings = self.generate_embeddings_batch(texts)
            
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = self._generate_chunk_id(user_id, chunk.get("filename", "unknown"), i)
                
                metadata = {
                    "user_id": user_id,
                    "document_id": document_id or chunk.get("document_id", "unknown"),
                    "filename": chunk.get("filename", "unknown"),
                    "title": chunk.get("title"),
                    "author": chunk.get("author"),
                    "chunk_id": i,
                    "text": chunk["text"][:1000],
                    "page_number": chunk.get("page_number"),
                    "start_char": chunk.get("start_char", 0),
                    "end_char": chunk.get("end_char", 0)
                }
                
                vectors.append({
                    "id": vector_id,
                    "values": embedding,
                    "metadata": metadata
                })
            
            batch_size = 100
            total_upserted = 0
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                total_upserted += len(batch)
                print(f"Upserted {total_upserted}/{len(vectors)} vectors")
            
            print(f"Successfully stored {len(vectors)} vectors in Pinecone")
            
            return {
                "success": True,
                "vectors_stored": len(vectors),
                "document_id": document_id
            }
            
        except Exception as e:
            print(f"Error storing document chunks: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def search_similar(
        self, 
        query: str, 
        user_id: str, 
        top_k: int = 10,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        try:
            query_embedding = self.generate_embedding(query)
            
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                filter={"user_id": {"$eq": user_id}}
            )
            
            formatted_results = []
            for match in results.matches:
                if match.score >= min_score:
                    formatted_results.append({
                        "id": match.id,
                        "score": float(match.score),
                        "text": match.metadata.get("text", ""),
                        "filename": match.metadata.get("filename", ""),
                        "title": match.metadata.get("title"),
                        "author": match.metadata.get("author"),
                        "chunk_id": match.metadata.get("chunk_id"),
                        "document_id": match.metadata.get("document_id"),
                        "page_number": match.metadata.get("page_number")
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"Error searching vectors: {e}")
            return []
    
    def search_by_filter(self, filter_dict: Dict[str, Any], top_k: int = 100) -> Dict[str, Any]:
        try:
            dummy_query = [0.0] * self.embedding_dimension
            
            results = self.index.query(
                vector=dummy_query,
                top_k=top_k,
                include_metadata=True,
                filter=filter_dict
            )
            
            return {
                "success": True,
                "matches": [
                    {
                        "id": match.id,
                        "score": float(match.score),
                        "metadata": match.metadata
                    }
                    for match in results.matches
                ]
            }
        except Exception as e:
            print(f"Error in filter search: {e}")
            return {"success": False, "error": str(e), "matches": []}
    
    def delete_document(self, document_id: str, user_id: str) -> Dict[str, bool]:
        try:
            self.index.delete(
                filter={
                    "document_id": {"$eq": document_id},
                    "user_id": {"$eq": user_id}
                }
            )
            
            return {"success": True}
        except Exception as e:
            print(f"Error deleting document: {e}")
            return {"success": False, "error": str(e)}
    
    def get_index_stats(self) -> Dict[str, Any]:
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

