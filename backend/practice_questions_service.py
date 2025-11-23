"""
Practice Questions Generator Service
Generates practice questions from legal documents to help users study and test their knowledge
"""

from typing import List, Dict, Any, Optional
import openai
import os
from datetime import datetime
import json


class PracticeQuestionsService:
    """
    Service for generating practice questions from documents
    Supports multiple question types: multiple choice, short answer, true/false
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize Practice Questions Service
        
        Args:
            openai_api_key: OpenAI API key
            model: OpenAI model to use
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        openai.api_key = self.api_key
        self.model = model
        
        print(f"[PRACTICE QUESTIONS] Initialized with model: {model}")
    
    def generate_questions(
        self,
        document_chunks: List[Dict[str, Any]],
        document_id: str,
        question_count: int = 5,
        question_types: Optional[List[str]] = None,
        difficulty: str = "medium",
        focus_area: Optional[str] = None,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate practice questions from document content
        
        Args:
            document_chunks: Document chunks containing the content
            document_id: ID of the document
            question_count: Number of questions to generate
            question_types: List of question types ['multiple_choice', 'short_answer', 'true_false']
            difficulty: Difficulty level ('easy', 'medium', 'hard')
            focus_area: Optional specific topic to focus on
            temperature: LLM temperature for creativity
            
        Returns:
            Dictionary containing generated questions and metadata
        """
        
        try:
            if not document_chunks:
                return {
                    "success": False,
                    "error": "No document content provided"
                }
            
            # Default question types if not specified
            if not question_types:
                question_types = ["multiple_choice", "short_answer", "true_false"]
            
            # Combine document chunks into context
            context = self._prepare_context(document_chunks)
            
            # Get document metadata
            document_name = document_chunks[0].get('filename', 'Unknown Document')
            document_title = document_chunks[0].get('title', '')
            
            print(f"[PRACTICE QUESTIONS] Generating {question_count} questions for document {document_id}")
            print(f"[PRACTICE QUESTIONS] Types: {question_types}, Difficulty: {difficulty}")
            
            # Generate questions using LLM
            prompt = self._create_question_generation_prompt(
                context=context,
                question_count=question_count,
                question_types=question_types,
                difficulty=difficulty,
                focus_area=focus_area,
                document_name=document_name
            )
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert legal educator who creates high-quality practice questions to test comprehension and critical thinking."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=3000
            )
            
            questions_text = response.choices[0].message.content.strip()
            
            # Parse the generated questions
            questions = self._parse_questions(questions_text, question_types)
            
            # Calculate usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            print(f"[PRACTICE QUESTIONS] Generated {len(questions)} questions ({usage['total_tokens']} tokens)")
            
            return {
                "success": True,
                "document_id": document_id,
                "document_name": document_name,
                "document_title": document_title,
                "questions": questions,
                "question_count": len(questions),
                "difficulty": difficulty,
                "focus_area": focus_area,
                "model": self.model,
                "usage": usage,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"[PRACTICE QUESTIONS] Error generating questions: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def _prepare_context(self, document_chunks: List[Dict[str, Any]], max_chars: int = 8000) -> str:
        """
        Prepare document context for question generation
        """
        # Sort chunks by chunk_id to maintain order
        sorted_chunks = sorted(document_chunks, key=lambda x: x.get('chunk_id', 0))
        
        # Combine chunks up to max_chars
        context_parts = []
        total_chars = 0
        
        for chunk in sorted_chunks:
            text = chunk.get('text', '')
            if total_chars + len(text) > max_chars:
                # Add partial text to reach max_chars
                remaining = max_chars - total_chars
                if remaining > 100:  # Only add if there's meaningful space
                    context_parts.append(text[:remaining])
                break
            context_parts.append(text)
            total_chars += len(text)
        
        return "\n\n".join(context_parts)
    
    def _create_question_generation_prompt(
        self,
        context: str,
        question_count: int,
        question_types: List[str],
        difficulty: str,
        focus_area: Optional[str],
        document_name: str
    ) -> str:
        """
        Create the prompt for generating practice questions
        """
        
        types_description = []
        if "multiple_choice" in question_types:
            types_description.append("- Multiple Choice: 4 options (A, B, C, D) with one correct answer")
        if "short_answer" in question_types:
            types_description.append("- Short Answer: Questions requiring 2-3 sentence answers")
        if "true_false" in question_types:
            types_description.append("- True/False: Statement-based questions")
        
        types_text = "\n".join(types_description)
        
        focus_instruction = f"\nFocus specifically on: {focus_area}" if focus_area else ""
        
        prompt = f"""Based on the following legal document content, generate {question_count} high-quality practice questions to test understanding.

DOCUMENT: {document_name}

CONTENT:
{context}

REQUIREMENTS:
1. Generate {question_count} questions distributed across these types:
{types_text}

2. Difficulty Level: {difficulty.upper()}
   - Easy: Test basic comprehension and recall
   - Medium: Test understanding and application
   - Hard: Test analysis, synthesis, and critical thinking

3. Question Quality:
   - Questions must be directly answerable from the provided content
   - Be specific and clear
   - Avoid ambiguous wording
   - For multiple choice, make distractors plausible but clearly incorrect
   - Test important concepts, not trivial details
{focus_instruction}

OUTPUT FORMAT (JSON):
[
  {{
    "id": 1,
    "type": "multiple_choice",
    "question": "What is the main holding in this case?",
    "options": {{
      "A": "Option A text",
      "B": "Option B text",
      "C": "Option C text",
      "D": "Option D text"
    }},
    "correct_answer": "B",
    "explanation": "Explanation of why B is correct and others are wrong",
    "difficulty": "medium",
    "topic": "Topic area"
  }},
  {{
    "id": 2,
    "type": "short_answer",
    "question": "Explain the legal reasoning used by the court.",
    "correct_answer": "The court reasoned that...",
    "explanation": "Key points to include in the answer",
    "difficulty": "hard",
    "topic": "Legal Reasoning"
  }},
  {{
    "id": 3,
    "type": "true_false",
    "question": "The court ruled in favor of the defendant.",
    "correct_answer": true,
    "explanation": "This is true because...",
    "difficulty": "easy",
    "topic": "Case Outcome"
  }}
]

Generate the questions now as valid JSON:"""
        
        return prompt
    
    def _parse_questions(self, questions_text: str, question_types: List[str]) -> List[Dict[str, Any]]:
        """
        Parse the generated questions from LLM response
        """
        try:
            # Try to extract JSON from the response
            # Sometimes the LLM wraps it in markdown code blocks
            if "```json" in questions_text:
                start = questions_text.find("```json") + 7
                end = questions_text.find("```", start)
                questions_text = questions_text[start:end].strip()
            elif "```" in questions_text:
                start = questions_text.find("```") + 3
                end = questions_text.find("```", start)
                questions_text = questions_text[start:end].strip()
            
            # Parse JSON
            questions = json.loads(questions_text)
            
            # Validate and clean questions
            validated_questions = []
            for q in questions:
                if self._validate_question(q):
                    validated_questions.append(q)
            
            return validated_questions
            
        except json.JSONDecodeError as e:
            print(f"[PRACTICE QUESTIONS] JSON parse error: {e}")
            print(f"[PRACTICE QUESTIONS] Raw response: {questions_text[:500]}")
            
            # Fallback: try to extract questions manually
            return self._fallback_parse(questions_text, question_types)
    
    def _validate_question(self, question: Dict[str, Any]) -> bool:
        """
        Validate that a question has all required fields
        """
        required_fields = ['id', 'type', 'question', 'correct_answer', 'explanation']
        
        for field in required_fields:
            if field not in question:
                print(f"[PRACTICE QUESTIONS] Missing field '{field}' in question")
                return False
        
        # Type-specific validation
        if question['type'] == 'multiple_choice':
            if 'options' not in question or len(question['options']) != 4:
                return False
        
        return True
    
    def _fallback_parse(self, text: str, question_types: List[str]) -> List[Dict[str, Any]]:
        """
        Fallback parser if JSON parsing fails
        Returns a basic structure
        """
        print("[PRACTICE QUESTIONS] Using fallback parser")
        return []
    
    def evaluate_answer(
        self,
        question: Dict[str, Any],
        user_answer: Any,
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """
        Evaluate a user's answer to a practice question
        
        Args:
            question: The question dictionary
            user_answer: User's submitted answer
            temperature: LLM temperature for evaluation
            
        Returns:
            Evaluation result with score and feedback
        """
        
        try:
            question_type = question.get('type')
            correct_answer = question.get('correct_answer')
            
            # For multiple choice and true/false, simple comparison
            if question_type in ['multiple_choice', 'true_false']:
                is_correct = str(user_answer).strip().upper() == str(correct_answer).strip().upper()
                
                return {
                    "success": True,
                    "is_correct": is_correct,
                    "score": 1.0 if is_correct else 0.0,
                    "correct_answer": correct_answer,
                    "user_answer": user_answer,
                    "feedback": question.get('explanation', ''),
                    "evaluated_at": datetime.utcnow().isoformat()
                }
            
            # For short answer, use LLM to evaluate
            elif question_type == 'short_answer':
                return self._evaluate_short_answer(
                    question=question,
                    user_answer=user_answer,
                    correct_answer=correct_answer,
                    temperature=temperature
                )
            
            else:
                return {
                    "success": False,
                    "error": f"Unknown question type: {question_type}"
                }
                
        except Exception as e:
            print(f"[PRACTICE QUESTIONS] Error evaluating answer: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _evaluate_short_answer(
        self,
        question: Dict[str, Any],
        user_answer: str,
        correct_answer: str,
        temperature: float
    ) -> Dict[str, Any]:
        """
        Use LLM to evaluate short answer questions
        """
        
        prompt = f"""Evaluate the following short answer question response.

QUESTION: {question['question']}

CORRECT ANSWER: {correct_answer}

USER'S ANSWER: {user_answer}

EVALUATION CRITERIA:
1. Does the answer demonstrate understanding of the key concepts?
2. Are the main points covered?
3. Is the information accurate?

Provide:
1. A score from 0.0 to 1.0 (0.0 = completely wrong, 1.0 = perfect)
2. Brief feedback (2-3 sentences) explaining the score
3. What the user did well and what could be improved

OUTPUT FORMAT (JSON):
{{
  "score": 0.85,
  "feedback": "Your answer covers the main points well...",
  "strengths": "Good understanding of...",
  "improvements": "Could also mention..."
}}

Evaluate now:"""
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a fair and constructive legal educator evaluating student answers."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=500
            )
            
            evaluation_text = response.choices[0].message.content.strip()
            
            # Parse evaluation
            if "```json" in evaluation_text:
                start = evaluation_text.find("```json") + 7
                end = evaluation_text.find("```", start)
                evaluation_text = evaluation_text[start:end].strip()
            
            evaluation = json.loads(evaluation_text)
            
            return {
                "success": True,
                "is_correct": evaluation.get('score', 0) >= 0.7,  # 70% threshold
                "score": evaluation.get('score', 0),
                "correct_answer": correct_answer,
                "user_answer": user_answer,
                "feedback": evaluation.get('feedback', ''),
                "strengths": evaluation.get('strengths', ''),
                "improvements": evaluation.get('improvements', ''),
                "evaluated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"[PRACTICE QUESTIONS] Error in short answer evaluation: {e}")
            # Fallback to simple comparison
            return {
                "success": True,
                "is_correct": False,
                "score": 0.5,
                "feedback": "Unable to fully evaluate. Please review the correct answer.",
                "correct_answer": correct_answer,
                "user_answer": user_answer,
                "evaluated_at": datetime.utcnow().isoformat()
            }
    
    def generate_quiz(
        self,
        document_ids: List[str],
        document_chunks_map: Dict[str, List[Dict[str, Any]]],
        quiz_name: str,
        question_count: int = 10,
        difficulty: str = "medium",
        question_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive quiz from multiple documents
        
        Args:
            document_ids: List of document IDs to include
            document_chunks_map: Map of document_id to chunks
            quiz_name: Name for the quiz
            question_count: Total questions for the quiz
            difficulty: Difficulty level
            question_types: Types of questions to include
            
        Returns:
            Quiz with questions from all documents
        """
        
        try:
            all_questions = []
            questions_per_doc = max(2, question_count // len(document_ids))
            
            for doc_id in document_ids:
                chunks = document_chunks_map.get(doc_id, [])
                if not chunks:
                    continue
                
                result = self.generate_questions(
                    document_chunks=chunks,
                    document_id=doc_id,
                    question_count=questions_per_doc,
                    question_types=question_types,
                    difficulty=difficulty
                )
                
                if result.get('success'):
                    questions = result.get('questions', [])
                    # Add document context to each question
                    for q in questions:
                        q['document_id'] = doc_id
                        q['document_name'] = result.get('document_name')
                    all_questions.extend(questions)
            
            # Limit to requested count
            all_questions = all_questions[:question_count]
            
            # Renumber questions
            for i, q in enumerate(all_questions, 1):
                q['id'] = i
            
            return {
                "success": True,
                "quiz_name": quiz_name,
                "questions": all_questions,
                "question_count": len(all_questions),
                "document_count": len(document_ids),
                "difficulty": difficulty,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"[PRACTICE QUESTIONS] Error generating quiz: {e}")
            return {
                "success": False,
                "error": str(e)
            }

