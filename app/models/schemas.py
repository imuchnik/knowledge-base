from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    DOCX = "docx"
    MD = "markdown"
    HTML = "html"

class DocumentMetadata(BaseModel):
    filename: str
    document_type: DocumentType
    size: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    chunk_count: int = 0
    
class DocumentUpload(BaseModel):
    id: str
    filename: str
    status: str
    chunks_processed: int
    embedding_time: float
    metadata: DocumentMetadata
    
class SearchQuery(BaseModel):
    query: str
    max_results: Optional[int] = Field(default=10, le=50)
    document_ids: Optional[List[str]] = None
    similarity_threshold: Optional[float] = Field(default=0.7, ge=0.0, le=1.0)
    
class SearchResult(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    
class QuestionAnswer(BaseModel):
    question: str
    max_results: Optional[int] = Field(default=5, le=20)
    
class AnswerResponse(BaseModel):
    question: str
    answer: str
    sources: List[SearchResult]
    confidence: float
    processing_time: float
    
class CompletenessCheck(BaseModel):
    topics: List[str]
    document_ids: Optional[List[str]] = None
    
class CompletenessResult(BaseModel):
    topic: str
    coverage_score: float
    covered_aspects: List[str]
    missing_aspects: List[str]
    relevant_chunks: List[SearchResult]
    
class CompletenessResponse(BaseModel):
    overall_completeness: float
    results: List[CompletenessResult]
    recommendations: List[str]
    
class IndexStatus(BaseModel):
    total_documents: int
    total_chunks: int
    index_size_mb: float
    last_update: datetime
    
class DocumentDelete(BaseModel):
    document_id: str
    status: str
    chunks_deleted: int