"""
Case Brief Generation Service
Extracts structured legal case briefs from uploaded documents
"""

from typing import List, Dict, Any, Optional
import openai
import os
from datetime import datetime
import re


class CaseBriefPromptTemplates:
    """Specialized prompts for extracting case brief components"""
    
    @staticmethod
    def get_full_brief_prompt(document_text: str) -> str:
        """Generate a comprehensive case brief from document text"""
        
        prompt = f"""You are a legal research assistant specializing in creating case briefs. 
Analyze the following legal case document and create a comprehensive, well-structured case brief.

INSTRUCTIONS:
1. Extract all relevant information from the provided case text
2. Format the brief using the standard IRAC/FIRAC structure
3. Be precise and cite specific details from the case
4. If certain information is not available in the text, indicate "Not specified in document"

CASE DOCUMENT:
{document_text}

Generate a detailed case brief with the following sections:

**CASE BRIEF FORMAT:**

## Case Name and Citation
[Full case name, citation, court, date]

## Parties
- Plaintiff/Appellant: [Name and brief description]
- Defendant/Appellee: [Name and brief description]

## Facts
[Detailed factual background - what happened that led to this case? Include relevant procedural history]

## Procedural History
[How the case moved through the courts - lower court decisions, appeals, etc.]

## Issues
[Precise legal questions the court needs to decide - frame as questions]
1. [Issue 1]
2. [Issue 2]
...

## Rule of Law
[The legal principles, statutes, or precedents that apply to this case]

## Holding
[The court's specific decision on each issue - typically yes/no answers to the issues]

## Reasoning
[Detailed analysis of WHY the court decided this way - the court's logic, application of law to facts, policy considerations]

## Disposition
[What happened to the case? Affirmed, reversed, remanded, etc.]

## Significance/Notes
[Why this case matters - precedent set, doctrinal impact, practical implications]

Please provide a thorough, well-organized case brief:"""
        
        return prompt
    
    @staticmethod
    def get_quick_summary_prompt(document_text: str) -> str:
        """Generate a quick summary of a case"""
        
        prompt = f"""Provide a concise 2-3 paragraph summary of this legal case.

Include:
1. Who the parties are and what happened (facts)
2. What legal issue(s) the court addressed
3. How the court ruled and why

CASE TEXT:
{document_text}

SUMMARY:"""
        
        return prompt
    
    @staticmethod
    def extract_section_prompt(document_text: str, section: str) -> str:
        """Extract a specific section from a case"""
        
        section_instructions = {
            "facts": "Extract and summarize the factual background - what events led to this lawsuit?",
            "issues": "Identify the precise legal questions the court needed to decide. Format as clear questions.",
            "holding": "State the court's decision on each issue - what did the court decide?",
            "reasoning": "Explain the court's legal reasoning - WHY did they reach this decision?",
            "rule": "Identify the legal rule, statute, or precedent the court applied",
            "disposition": "State the final outcome - was the case affirmed, reversed, remanded, etc.?"
        }
        
        instruction = section_instructions.get(section.lower(), f"Extract information about: {section}")
        
        prompt = f"""{instruction}

CASE TEXT:
{document_text}

{section.upper()}:"""
        
        return prompt


class CaseBriefService:
    """
    Service for generating legal case briefs from documents
    Integrates with vector search and RAG for comprehensive analysis
    """
    
    def __init__(self, openai_api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        """
        Initialize case brief service
        
        Args:
            openai_api_key: OpenAI API key
            model: OpenAI model to use (gpt-4o-mini recommended for speed/cost)
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
        
        openai.api_key = self.api_key
        self.model = model
        self.templates = CaseBriefPromptTemplates()
        
        print(f"[CASE BRIEF] Initialized with model: {model}")
    
    def generate_case_brief(
        self,
        document_chunks: List[Dict[str, Any]],
        document_id: str,
        brief_type: str = "full",
        temperature: float = 0.2,
        max_tokens: int = 2500
    ) -> Dict[str, Any]:
        """
        Generate a case brief from document chunks
        
        Args:
            document_chunks: List of text chunks from the case document
            document_id: ID of the document
            brief_type: "full" for complete brief, "summary" for quick summary
            temperature: LLM temperature (lower = more focused)
            max_tokens: Maximum response length
            
        Returns:
            Dictionary containing the generated brief and metadata
        """
        
        try:
            if not document_chunks:
                return {
                    "success": False,
                    "error": "No document content provided",
                    "brief": None
                }
            
            # Combine chunks into full document text
            # Sort by chunk_id to maintain order
            sorted_chunks = sorted(document_chunks, key=lambda x: x.get('chunk_id', 0))
            document_text = "\n\n".join([chunk.get('text', '') for chunk in sorted_chunks])
            
            # Truncate if too long (keep first portions which usually have case header/facts)
            max_chars = 20000  # Approximately 5000 tokens worth of text
            if len(document_text) > max_chars:
                print(f"[CASE BRIEF] Truncating document from {len(document_text)} to {max_chars} chars")
                document_text = document_text[:max_chars] + "\n\n[Document truncated for processing...]"
            
            # Select appropriate prompt
            if brief_type == "summary":
                prompt = self.templates.get_quick_summary_prompt(document_text)
                max_tokens = 800
            else:
                prompt = self.templates.get_full_brief_prompt(document_text)
            
            print(f"[CASE BRIEF] Generating {brief_type} brief for document {document_id}")
            print(f"[CASE BRIEF] Processing {len(document_chunks)} chunks, {len(document_text)} characters")
            
            # Call OpenAI API
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert legal assistant specializing in case brief analysis. Provide clear, structured, and accurate case briefs."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.95
            )
            
            brief_content = response.choices[0].message.content.strip()
            
            # Extract structured sections from the brief
            sections = self._parse_brief_sections(brief_content)
            
            # Calculate token usage
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
            
            print(f"[CASE BRIEF] Generated brief ({usage['total_tokens']} tokens)")
            
            # Extract case name if possible
            case_name = self._extract_case_name(brief_content, document_chunks)
            
            result = {
                "success": True,
                "document_id": document_id,
                "case_name": case_name,
                "brief_type": brief_type,
                "brief_content": brief_content,
                "sections": sections,
                "metadata": {
                    "model": self.model,
                    "chunks_processed": len(document_chunks),
                    "character_count": len(document_text),
                    "usage": usage,
                    "generated_at": datetime.utcnow().isoformat()
                }
            }
            
            return result
            
        except Exception as e:
            print(f"[CASE BRIEF] Error generating brief: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                "success": False,
                "error": str(e),
                "brief": None,
                "document_id": document_id
            }
    
    def extract_specific_section(
        self,
        document_chunks: List[Dict[str, Any]],
        section: str,
        temperature: float = 0.2,
        max_tokens: int = 800
    ) -> Dict[str, Any]:
        """
        Extract a specific section from a case (e.g., just facts, just holding)
        
        Args:
            document_chunks: Document chunks
            section: Section to extract (facts, issues, holding, reasoning, rule, disposition)
            temperature: LLM temperature
            max_tokens: Maximum response length
            
        Returns:
            Dictionary with extracted section
        """
        
        try:
            sorted_chunks = sorted(document_chunks, key=lambda x: x.get('chunk_id', 0))
            document_text = "\n\n".join([chunk.get('text', '') for chunk in sorted_chunks])
            
            if len(document_text) > 20000:
                document_text = document_text[:20000]
            
            prompt = self.templates.extract_section_prompt(document_text, section)
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal research assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            content = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "section": section,
                "content": content,
                "usage": {
                    "total_tokens": response.usage.total_tokens
                }
            }
            
        except Exception as e:
            print(f"[CASE BRIEF] Error extracting section {section}: {e}")
            return {
                "success": False,
                "error": str(e),
                "section": section,
                "content": None
            }
    
    def _parse_brief_sections(self, brief_content: str) -> Dict[str, str]:
        """
        Parse the generated brief into structured sections
        """
        sections = {}
        
        # Common section headers to look for
        section_patterns = [
            r'##\s*(Case Name and Citation|Case Name)',
            r'##\s*(Parties)',
            r'##\s*(Facts)',
            r'##\s*(Procedural History)',
            r'##\s*(Issues?)',
            r'##\s*(Rule of Law|Legal Rule|Applicable Law)',
            r'##\s*(Holding)',
            r'##\s*(Reasoning|Analysis|Rationale)',
            r'##\s*(Disposition|Outcome)',
            r'##\s*(Significance|Notes|Importance)'
        ]
        
        # Try to extract each section
        for pattern in section_patterns:
            match = re.search(pattern, brief_content, re.IGNORECASE)
            if match:
                section_name = match.group(1).lower().replace(' ', '_')
                start_pos = match.end()
                
                # Find the next section or end of document
                next_match = re.search(r'##\s*\w+', brief_content[start_pos:])
                if next_match:
                    end_pos = start_pos + next_match.start()
                else:
                    end_pos = len(brief_content)
                
                section_content = brief_content[start_pos:end_pos].strip()
                sections[section_name] = section_content
        
        return sections
    
    def _extract_case_name(self, brief_content: str, document_chunks: List[Dict[str, Any]]) -> Optional[str]:
        """
        Try to extract the case name from the brief or document
        """
        # Try to find case name in the brief content
        case_name_pattern = r'(?:Case Name[:\s]+)([A-Z][^\n]+v\.?\s+[A-Z][^\n]+)'
        match = re.search(case_name_pattern, brief_content, re.IGNORECASE)
        
        if match:
            return match.group(1).strip()
        
        # Try from first chunk
        if document_chunks and len(document_chunks) > 0:
            first_text = document_chunks[0].get('text', '')
            match = re.search(r'([A-Z][^\n]+v\.?\s+[A-Z][^\n]+)', first_text)
            if match:
                return match.group(1).strip()
        
        return None
    
    def compare_cases(
        self,
        case_briefs: List[Dict[str, Any]],
        comparison_focus: Optional[str] = None,
        temperature: float = 0.3,
        max_tokens: int = 1500
    ) -> Dict[str, Any]:
        """
        Compare multiple case briefs and analyze similarities/differences
        
        Args:
            case_briefs: List of generated case briefs
            comparison_focus: Optional focus area (e.g., "holdings", "reasoning", "facts")
            temperature: LLM temperature
            max_tokens: Maximum response length
            
        Returns:
            Comparative analysis
        """
        
        try:
            if len(case_briefs) < 2:
                return {
                    "success": False,
                    "error": "At least 2 case briefs required for comparison"
                }
            
            # Format the cases for comparison
            cases_text = ""
            for i, brief in enumerate(case_briefs, 1):
                case_name = brief.get('case_name', f'Case {i}')
                content = brief.get('brief_content', '')
                cases_text += f"\n\n=== CASE {i}: {case_name} ===\n{content}\n"
            
            focus_instruction = f"\nFocus your comparison on: {comparison_focus}" if comparison_focus else ""
            
            prompt = f"""Compare and analyze the following legal cases. Provide a structured comparison covering:

1. **Summary**: Brief overview of each case
2. **Similarities**: Common legal issues, rules, or reasoning
3. **Differences**: How the cases differ in facts, holdings, or outcomes
4. **Legal Principles**: Key doctrines or rules illustrated
5. **Precedential Value**: How these cases relate to each other{focus_instruction}

CASES TO COMPARE:
{cases_text}

COMPARATIVE ANALYSIS:"""
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a legal scholar expert in comparative case analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            analysis = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "comparison": analysis,
                "cases_compared": len(case_briefs),
                "case_names": [brief.get('case_name', f'Case {i}') for i, brief in enumerate(case_briefs, 1)],
                "usage": {
                    "total_tokens": response.usage.total_tokens
                },
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"[CASE BRIEF] Error comparing cases: {e}")
            return {
                "success": False,
                "error": str(e)
            }

