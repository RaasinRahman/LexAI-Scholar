"""
PDF Processing Service
Handles text extraction, chunking, and metadata extraction from PDF documents
"""
import PyPDF2
import pdfplumber
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import io


class PDFProcessor:
    """
    Comprehensive PDF processing with text extraction and metadata handling
    """
    
    def __init__(self):
        self.chunk_size = 1000  # characters per chunk
        self.chunk_overlap = 200  # overlap between chunks
        
    def extract_text_from_pdf(self, pdf_file: bytes) -> str:
        """
        Extract text from PDF using multiple methods for robustness
        """
        text = ""
        
        try:
            # Method 1: pdfplumber (better for complex layouts)
            with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            
            # Fallback to PyPDF2
            try:
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            except Exception as e2:
                print(f"PyPDF2 extraction also failed: {e2}")
                raise Exception("Failed to extract text from PDF")
        
        return text.strip()
    
    def extract_metadata(self, pdf_file: bytes, filename: str) -> Dict[str, Any]:
        """
        Extract metadata from PDF document
        """
        metadata = {
            "filename": filename,
            "extracted_at": datetime.utcnow().isoformat(),
            "title": None,
            "author": None,
            "subject": None,
            "creator": None,
            "producer": None,
            "creation_date": None,
            "page_count": 0,
            "file_size_bytes": len(pdf_file)
        }
        
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file))
            metadata["page_count"] = len(pdf_reader.pages)
            
            # Extract PDF metadata
            if pdf_reader.metadata:
                pdf_meta = pdf_reader.metadata
                metadata["title"] = str(pdf_meta.get('/Title', '')) if pdf_meta.get('/Title') else None
                metadata["author"] = str(pdf_meta.get('/Author', '')) if pdf_meta.get('/Author') else None
                metadata["subject"] = str(pdf_meta.get('/Subject', '')) if pdf_meta.get('/Subject') else None
                metadata["creator"] = str(pdf_meta.get('/Creator', '')) if pdf_meta.get('/Creator') else None
                metadata["producer"] = str(pdf_meta.get('/Producer', '')) if pdf_meta.get('/Producer') else None
                
                # Handle creation date
                creation_date = pdf_meta.get('/CreationDate')
                if creation_date:
                    metadata["creation_date"] = str(creation_date)
            
            # If no title in metadata, try to extract from filename
            if not metadata["title"]:
                metadata["title"] = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
                
        except Exception as e:
            print(f"Error extracting metadata: {e}")
        
        return metadata
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for better context preservation
        """
        if not text:
            return []
        
        # Clean the text
        text = self._clean_text(text)
        
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            # Calculate end position
            end = start + self.chunk_size
            
            # If not the last chunk, try to break at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the next 100 characters
                sentence_end = self._find_sentence_boundary(text, end, end + 100)
                if sentence_end > end:
                    end = sentence_end
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:  # Only add non-empty chunks
                chunks.append({
                    "chunk_id": chunk_id,
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": end,
                    "chunk_length": len(chunk_text),
                    "filename": metadata.get("filename", "unknown"),
                    "title": metadata.get("title"),
                    "author": metadata.get("author"),
                    "page_count": metadata.get("page_count", 0)
                })
                chunk_id += 1
            
            # Move start position with overlap
            start = end - self.chunk_overlap
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """
        Clean extracted text by removing extra whitespace and normalizing
        """
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)
        
        # Remove leading/trailing whitespace from each line
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        """
        Find the nearest sentence boundary (., !, ?) within a range
        """
        search_text = text[start:end]
        
        # Look for sentence endings
        for match in re.finditer(r'[.!?]\s+', search_text):
            return start + match.end()
        
        # If no sentence boundary found, return the end
        return end
    
    def process_pdf(self, pdf_file: bytes, filename: str) -> Dict[str, Any]:
        """
        Complete PDF processing pipeline
        Returns extracted text, chunks, and metadata
        """
        # Extract text
        text = self.extract_text_from_pdf(pdf_file)
        
        # Extract metadata
        metadata = self.extract_metadata(pdf_file, filename)
        
        # Create chunks
        chunks = self.chunk_text(text, metadata)
        
        return {
            "text": text,
            "metadata": metadata,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "character_count": len(text)
        }

