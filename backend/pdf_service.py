import PyPDF2
import pdfplumber
from typing import List, Dict, Any, Optional
from datetime import datetime
import re
import io


class PDFProcessor:
    def __init__(self):
        self.chunk_size = 1500
        self.chunk_overlap = 300
        
    def extract_text_from_pdf(self, pdf_file: bytes) -> str:
        text = ""
        
        try:
            with pdfplumber.open(io.BytesIO(pdf_file)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
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
            
            if pdf_reader.metadata:
                pdf_meta = pdf_reader.metadata
                metadata["title"] = str(pdf_meta.get('/Title', '')) if pdf_meta.get('/Title') else None
                metadata["author"] = str(pdf_meta.get('/Author', '')) if pdf_meta.get('/Author') else None
                metadata["subject"] = str(pdf_meta.get('/Subject', '')) if pdf_meta.get('/Subject') else None
                metadata["creator"] = str(pdf_meta.get('/Creator', '')) if pdf_meta.get('/Creator') else None
                metadata["producer"] = str(pdf_meta.get('/Producer', '')) if pdf_meta.get('/Producer') else None
                
                creation_date = pdf_meta.get('/CreationDate')
                if creation_date:
                    metadata["creation_date"] = str(creation_date)
            
            if not metadata["title"]:
                metadata["title"] = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
                
        except Exception as e:
            print(f"Error extracting metadata: {e}")
        
        return metadata
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not text:
            return []
        
        text = self._clean_text(text)
        paragraphs = self._split_into_paragraphs(text)
        
        chunks = []
        chunk_id = 0
        current_chunk = ""
        current_start = 0
        
        for para in paragraphs:
            if len(current_chunk) + len(para) > self.chunk_size:
                if current_chunk.strip():
                    chunks.append(self._create_chunk(
                        current_chunk.strip(),
                        chunk_id,
                        current_start,
                        current_start + len(current_chunk),
                        metadata
                    ))
                    chunk_id += 1
                    
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else current_chunk
                    current_chunk = overlap_text + " " + para
                    current_start = current_start + len(current_chunk) - len(overlap_text) - len(para)
                else:
                    if len(para) > self.chunk_size:
                        sub_chunks = self._split_large_paragraph(para, current_start, metadata, chunk_id)
                        chunks.extend(sub_chunks)
                        chunk_id += len(sub_chunks)
                        current_chunk = ""
                        current_start += len(para)
                    else:
                        current_chunk = para
            else:
                if current_chunk:
                    current_chunk += " " + para
                else:
                    current_chunk = para
        
        if current_chunk.strip():
            chunks.append(self._create_chunk(
                current_chunk.strip(),
                chunk_id,
                current_start,
                current_start + len(current_chunk),
                metadata
            ))
        
        return chunks
    
    def _split_into_paragraphs(self, text: str) -> List[str]:
        paragraphs = re.split(r'\n\n+', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    def _create_chunk(self, text: str, chunk_id: int, start: int, end: int, metadata: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "chunk_id": chunk_id,
            "text": text,
            "start_char": start,
            "end_char": end,
            "chunk_length": len(text),
            "filename": metadata.get("filename", "unknown"),
            "title": metadata.get("title"),
            "author": metadata.get("author"),
            "page_count": metadata.get("page_count", 0)
        }
    
    def _split_large_paragraph(self, para: str, start_pos: int, metadata: Dict[str, Any], start_chunk_id: int) -> List[Dict[str, Any]]:
        chunks = []
        start = 0
        chunk_id = start_chunk_id
        
        while start < len(para):
            end = start + self.chunk_size
            
            if end < len(para):
                sentence_end = self._find_sentence_boundary(para, end, min(end + 200, len(para)))
                if sentence_end > end:
                    end = sentence_end
            
            chunk_text = para[start:end].strip()
            
            if chunk_text:
                chunks.append(self._create_chunk(
                    chunk_text,
                    chunk_id,
                    start_pos + start,
                    start_pos + end,
                    metadata
                ))
                chunk_id += 1
            
            start = end - self.chunk_overlap
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text
    
    def _find_sentence_boundary(self, text: str, start: int, end: int) -> int:
        if start >= end or start >= len(text):
            return end
            
        search_text = text[start:min(end, len(text))]
        sentence_ends = []
        for match in re.finditer(r'[.!?]\s+', search_text):
            sentence_ends.append(start + match.end())
        
        if sentence_ends:
            return sentence_ends[-1]
        
        return min(end, len(text))
    
    def process_pdf(self, pdf_file: bytes, filename: str) -> Dict[str, Any]:
        text = self.extract_text_from_pdf(pdf_file)
        metadata = self.extract_metadata(pdf_file, filename)
        chunks = self.chunk_text(text, metadata)
        
        return {
            "text": text,
            "metadata": metadata,
            "chunks": chunks,
            "chunk_count": len(chunks),
            "character_count": len(text)
        }

