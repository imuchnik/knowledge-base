import os
import hashlib
from typing import List, Dict, Any, Tuple
from pathlib import Path
import pypdf
from docx import Document as DocxDocument
import markdown
from bs4 import BeautifulSoup
import aiofiles
from datetime import datetime

from app.models.schemas import DocumentType, DocumentMetadata
from app.core.config import settings

class DocumentProcessor:
    def __init__(self):
        self.chunk_size = settings.chunk_size
        self.chunk_overlap = settings.chunk_overlap
        
    async def process_document(self, file_path: str, filename: str) -> Tuple[List[Dict[str, Any]], DocumentMetadata]:
        file_extension = Path(filename).suffix.lower()
        document_type = self._get_document_type(file_extension)
        
        content = await self._extract_content(file_path, document_type)
        chunks = self._chunk_text(content)
        
        file_stats = os.stat(file_path)
        metadata = DocumentMetadata(
            filename=filename,
            document_type=document_type,
            size=file_stats.st_size,
            created_at=datetime.utcnow(),
            chunk_count=len(chunks)
        )
        
        document_id = self._generate_document_id(filename, content)
        
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            chunk_data = {
                "document_id": document_id,
                "chunk_id": f"{document_id}_{i}",
                "content": chunk,
                "metadata": {
                    "filename": filename,
                    "document_type": document_type.value,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "created_at": metadata.created_at.isoformat()
                }
            }
            processed_chunks.append(chunk_data)
            
        return processed_chunks, metadata
    
    def _get_document_type(self, extension: str) -> DocumentType:
        extension_map = {
            ".pdf": DocumentType.PDF,
            ".txt": DocumentType.TXT,
            ".docx": DocumentType.DOCX,
            ".md": DocumentType.MD,
            ".html": DocumentType.HTML,
            ".htm": DocumentType.HTML
        }
        return extension_map.get(extension, DocumentType.TXT)
    
    async def _extract_content(self, file_path: str, document_type: DocumentType) -> str:
        if document_type == DocumentType.PDF:
            return await self._extract_pdf(file_path)
        elif document_type == DocumentType.DOCX:
            return await self._extract_docx(file_path)
        elif document_type == DocumentType.MD:
            return await self._extract_markdown(file_path)
        elif document_type == DocumentType.HTML:
            return await self._extract_html(file_path)
        else:
            return await self._extract_text(file_path)
    
    async def _extract_pdf(self, file_path: str) -> str:
        with open(file_path, 'rb') as file:
            pdf_reader = pypdf.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text.strip()
    
    async def _extract_docx(self, file_path: str) -> str:
        doc = DocxDocument(file_path)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    
    async def _extract_markdown(self, file_path: str) -> str:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')
        return soup.get_text().strip()
    
    async def _extract_html(self, file_path: str) -> str:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            content = await file.read()
        soup = BeautifulSoup(content, 'html.parser')
        return soup.get_text().strip()
    
    async def _extract_text(self, file_path: str) -> str:
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
            return await file.read()
    
    def _chunk_text(self, text: str) -> List[str]:
        if not text:
            return []
            
        chunks = []
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk = ' '.join(words[i:i + self.chunk_size])
            if chunk:
                chunks.append(chunk)
                
        return chunks
    
    def _generate_document_id(self, filename: str, content: str) -> str:
        unique_string = f"{filename}_{len(content)}_{content[:100]}"
        return hashlib.md5(unique_string.encode()).hexdigest()