"""
RAG (Retrieval Augmented Generation) Service
Combines vector search with LLM generation for intelligent Q&A
"""

from typing import List, Dict, Any, Optional
import openai
import os
from datetime import datetime


class PromptTemplates:
    """Collection of prompt engineering templates for different query types"""
    
    @staticmethod
    def get_qa_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate a prompt for question-answering with citations"""
        
        # Format context with sources
        formatted_context = ""
        for i, chunk in enumerate(context_chunks, 1):
            source_info = f"[Source {i}: {chunk.get('filename', 'Unknown')} - {chunk.get('title', 'Untitled')}]"
            formatted_context += f"\n{source_info}\n{chunk['text']}\n"
        
        prompt = f"""You are an intelligent research assistant helping users understand their documents. 
Use ONLY the provided context to answer the question. Be precise, informative, and academic in tone.

IMPORTANT CITATION RULES:
1. When you reference information, cite the source number in brackets like [Source 1] or [Source 2]
2. Use multiple citations when combining information: [Source 1, 2]
3. If the context doesn't contain the answer, say "I cannot find this information in your documents"
4. Never make up information not present in the context

CONTEXT FROM USER'S DOCUMENTS:
{formatted_context}

QUESTION: {query}

ANSWER (with citations):"""
        
        return prompt
    
    @staticmethod
    def get_summarization_prompt(context_chunks: List[Dict[str, Any]], focus: Optional[str] = None) -> str:
        """Generate a prompt for document summarization"""
        
        formatted_context = "\n\n".join([chunk['text'] for chunk in context_chunks])
        
        focus_instruction = f" Focus specifically on: {focus}" if focus else ""
        
        prompt = f"""Summarize the following content from the user's documents in a clear, structured way.
{focus_instruction}

Provide:
1. Main Points (3-5 key takeaways)
2. Supporting Details
3. Conclusions or Implications

CONTENT:
{formatted_context}

SUMMARY:"""
        
        return prompt
    
    @staticmethod
    def get_comparative_analysis_prompt(query: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Generate a prompt for comparing information across documents"""
        
        grouped_by_doc = {}
        for chunk in context_chunks:
            doc_id = chunk.get('document_id', 'unknown')
            if doc_id not in grouped_by_doc:
                grouped_by_doc[doc_id] = {
                    'filename': chunk.get('filename', 'Unknown'),
                    'chunks': []
                }
            grouped_by_doc[doc_id]['chunks'].append(chunk['text'])
        
        formatted_context = ""
        for i, (doc_id, data) in enumerate(grouped_by_doc.items(), 1):
            formatted_context += f"\n[Document {i}: {data['filename']}]\n"
            formatted_context += "\n".join(data['chunks'])
            formatted_context += "\n"
        
        prompt = f"""Compare and analyze information across the user's documents regarding: {query}

Provide a structured comparison:
1. Similarities - What themes or ideas appear across documents?
2. Differences - How do the documents differ in their approach or conclusions?
3. Unique Insights - What unique perspectives does each document offer?
4. Synthesis - What overall understanding emerges from considering all sources together?

Cite sources as [Document 1], [Document 2], etc.

DOCUMENTS:
{formatted_context}

COMPARATIVE ANALYSIS:"""
        
        return prompt
    
    @staticmethod
    def get_conversational_prompt(query: str, context_chunks: List[Dict[str, Any]], 
                                  conversation_history: List[Dict[str, str]]) -> str:
        """Generate a prompt for conversational AI with context awareness"""
        
        # Format previous conversation
        history_text = ""
        if conversation_history:
            history_text = "PREVIOUS CONVERSATION:\n"
            for msg in conversation_history[-3:]:  # Last 3 exchanges
                role = msg.get('role', 'user').upper()
                content = msg.get('content', '')
                history_text += f"{role}: {content}\n"
            history_text += "\n"
        
        # Format context
        formatted_context = ""
        for i, chunk in enumerate(context_chunks, 1):
            source_info = f"[Source {i}: {chunk.get('filename', 'Unknown')}]"
            formatted_context += f"\n{source_info}\n{chunk['text'][:800]}...\n"
        
        prompt = f"""You are a knowledgeable research assistant engaged in a conversation with a user about their documents.

CONTEXT FROM DOCUMENTS:
{formatted_context}

{history_text}

NEW QUESTION: {query}

Provide a conversational, helpful response that:
1. Directly addresses the user's question
2. References specific information with citations [Source 1], [Source 2], etc.
3. Acknowledges the conversation history when relevant
4. Is clear, concise, and friendly

RESPONSE:"""
        
        return prompt


class RAGService:
    """
    Retrieval Augmented Generation Service
    Combines vector search with LLM to provide intelligent answers with citations
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize RAG service with OpenAI
        
        Args:
            openai_api_key: OpenAI API key (defaults to env variable)
            model: OpenAI model to use (gpt-4o-mini is cost-effective and capable)
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        openai.api_key = self.api_key
        self.model = model
        self.templates = PromptTemplates()
        
        print(f"[RAG] Initialized with model: {model}")
    
    def generate_answer(
        self,
        query: str,
        context_chunks: List[Dict[str, Any]],
        mode: str = "qa",
        conversation_history: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate an answer using RAG
        
        Args:
            query: User's question
            context_chunks: Retrieved document chunks from vector search
            mode: Type of response - "qa", "summary", "comparative", "conversational"
            conversation_history: Previous conversation for context
            temperature: LLM temperature (0.0-1.0, lower = more focused)
            max_tokens: Maximum response length
            
        Returns:
            Dictionary containing answer, citations, and metadata
        """
        
        try:
            if not context_chunks:
                return {
                    "success": False,
                    "answer": "I don't have any relevant information in your documents to answer this question. Please upload documents related to your query.",
                    "citations": [],
                    "model": self.model,
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Select appropriate prompt template
            if mode == "summary":
                prompt = self.templates.get_summarization_prompt(context_chunks)
            elif mode == "comparative":
                prompt = self.templates.get_comparative_analysis_prompt(query, context_chunks)
            elif mode == "conversational" and conversation_history:
                prompt = self.templates.get_conversational_prompt(query, context_chunks, conversation_history)
            else:  # Default to QA
                prompt = self.templates.get_qa_prompt(query, context_chunks)
            
            print(f"[RAG] Generating response with {len(context_chunks)} context chunks")
            print(f"[RAG] Mode: {mode}, Temperature: {temperature}")
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful research assistant that provides accurate answers based on provided documents."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95,
                frequency_penalty=0.0,
                presence_penalty=0.0
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Extract citation information
            citations = self._extract_citations(answer, context_chunks)
            
            # Calculate token usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            print(f"[RAG] Generated answer ({usage['total_tokens']} tokens)")
            print(f"[RAG] Found {len(citations)} citations")
            
            return {
                "success": True,
                "answer": answer,
                "citations": citations,
                "context_chunks_used": len(context_chunks),
                "model": self.model,
                "mode": mode,
                "usage": usage,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"[RAG] Error generating answer: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "answer": "I encountered an error while generating the response. Please try again.",
                "citations": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _extract_citations(self, answer: str, context_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract citation information from the answer
        
        Returns a list of cited sources with their metadata
        """
        import re
        
        citations = []
        
        # Find all [Source N] patterns in the answer
        citation_pattern = r'\[Source (\d+)(?:,\s*(\d+))?\]'
        matches = re.findall(citation_pattern, answer)
        
        cited_indices = set()
        for match in matches:
            for num in match:
                if num:
                    cited_indices.add(int(num))
        
        # Build citation list
        for idx in sorted(cited_indices):
            if idx <= len(context_chunks):
                chunk = context_chunks[idx - 1]  # 0-indexed
                citations.append({
                    "source_number": idx,
                    "document_id": chunk.get("document_id"),
                    "filename": chunk.get("filename"),
                    "title": chunk.get("title"),
                    "author": chunk.get("author"),
                    "chunk_id": chunk.get("chunk_id"),
                    "text_preview": chunk.get("text", "")[:200] + "...",
                    "relevance_score": chunk.get("score", 0)
                })
        
        return citations
    
    def generate_followup_questions(
        self,
        original_query: str,
        answer: str,
        context_chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Generate relevant follow-up questions based on the conversation
        """
        
        try:
            prompt = f"""Based on this Q&A exchange, suggest 3 relevant follow-up questions the user might want to ask.
Questions should be specific, insightful, and help deepen understanding.

ORIGINAL QUESTION: {original_query}

ANSWER: {answer}

Generate 3 follow-up questions (one per line, no numbering):"""
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates insightful follow-up questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            questions_text = response.choices[0].message.content.strip()
            questions = [q.strip() for q in questions_text.split('\n') if q.strip() and not q.strip().startswith('#')]
            
            return questions[:3]
            
        except Exception as e:
            print(f"[RAG] Error generating follow-up questions: {e}")
            return []
    
    def summarize_conversation(
        self,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """
        Summarize a conversation thread
        """
        
        try:
            history_text = ""
            for msg in conversation_history:
                role = msg.get('role', 'user').upper()
                content = msg.get('content', '')
                history_text += f"{role}: {content}\n\n"
            
            prompt = f"""Summarize this conversation in 2-3 sentences, highlighting the main topics discussed and key insights.

CONVERSATION:
{history_text}

SUMMARY:"""
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"[RAG] Error summarizing conversation: {e}")
            return "Unable to generate summary"

