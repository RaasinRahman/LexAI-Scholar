from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from typing import List, Dict, Any, Optional
import time
import hashlib


class VectorService:
    def __init__(self, pinecone_api_key: str, index_name: str = "lexai-qa-index"):
        print("Loading embedding model (multi-qa-mpnet-base-dot-v1)...")
        self.embedding_model = SentenceTransformer('multi-qa-mpnet-base-dot-v1')
        self.embedding_dimension = 768
        
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
        try:
            processed_text = self._preprocess_text(text)
            embedding = self.embedding_model.encode(processed_text, convert_to_tensor=False, normalize_embeddings=True)
            return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise
    
    def _preprocess_text(self, text: str) -> str:
        max_length = 512
        if len(text) > 2000:
            text = text[:2000]
        
        text = ' '.join(text.split())
        
        return text
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        try:
            processed_texts = [self._preprocess_text(text) for text in texts]
            embeddings = self.embedding_model.encode(
                processed_texts, 
                convert_to_tensor=False, 
                show_progress_bar=True,
                normalize_embeddings=True
            )
            return embeddings.tolist()
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
            
            print(f"Generating embeddings for {len(texts)} chunks...")
            embeddings = self.generate_embeddings_batch(texts)
            
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = self._generate_chunk_id(
                    user_id, 
                    chunk.get("filename", "unknown"), 
                    i
                )
                
                metadata = {
                    "user_id": user_id,
                    "document_id": document_id or "unknown",
                    "chunk_id": chunk.get("chunk_id", i),
                    "text": chunk["text"][:1000],
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
    
    def _expand_query(self, query: str) -> str:
        expanded = query
        
        words = query.split()
        if len(words) <= 2:
            expanded = f"Information about {query}. Details regarding {query}."
        
        return expanded
    
    def _rerank_results(self, results: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
        import re
        
        query_lower = query.lower()
        query_words = set(re.findall(r'\w+', query_lower))
        
        for result in results:
            text_lower = result['text'].lower()
            text_words = set(re.findall(r'\w+', text_lower))
            
            overlap = len(query_words.intersection(text_words))
            overlap_ratio = overlap / max(len(query_words), 1)
            
            keyword_bonus = overlap_ratio * 0.1
            result['original_score'] = result['score']
            result['score'] = min(1.0, result['score'] + keyword_bonus)
            result['keyword_overlap'] = overlap
        
        results.sort(key=lambda x: x['score'], reverse=True)
        
        return results
    
    def search_similar(
        self, 
        query: str, 
        user_id: str,
        top_k: int = 5,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        try:
            print(f"🔍 Original query: '{query}'")
            
            expanded_query = self._expand_query(query)
            if expanded_query != query:
                print(f"🔍 Expanded query: '{expanded_query}'")
            
            print(f"🔍 Generating embedding...")
            query_embedding = self.generate_embedding(expanded_query)
            print(f"✓ Embedding generated (dimension: {len(query_embedding)})")
            
            print(f"🔍 Querying Pinecone for user: {user_id}")
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k * 4,
                include_metadata=True,
                filter={"user_id": {"$eq": user_id}}
            )
            
            print(f"✓ Pinecone returned {len(results.matches)} matches")
            
            matches = []
            for match in results.matches:
                if match.score >= 0.20:
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
            
            print(f"✓ Initial matches: {len(matches)} (score >= 0.20)")
            
            if matches:
                matches = self._rerank_results(matches, query)
                print(f"✓ Reranked results")
            
            matches = [m for m in matches if m['score'] >= min_score]
            matches = matches[:top_k]
            
            print(f"✓ Returning {len(matches)} matches (final threshold: {min_score})")
            for i, match in enumerate(matches[:3]):
                print(f"   #{i+1}: score={match['score']:.3f}, keyword_overlap={match.get('keyword_overlap', 0)}")
            
            return matches
            
        except Exception as e:
            print(f"✗ Error searching vectors: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def delete_document(self, document_id: str, user_id: str) -> Dict[str, Any]:
        try:
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

