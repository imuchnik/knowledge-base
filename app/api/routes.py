from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
import os
import time
from datetime import datetime
import aiofiles

from app.core.config import settings
from app.models.schemas import (
    DocumentUpload, SearchQuery, SearchResult, QuestionAnswer, 
    AnswerResponse, CompletenessCheck, CompletenessResponse,
    IndexStatus, DocumentDelete, DocumentListResponse
)
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStore
from app.services.qa_service import QAService

router = APIRouter()

document_processor = DocumentProcessor()
vector_store = VectorStore()
qa_service = QAService(vector_store)

@router.post("/documents/upload", response_model=DocumentUpload)
async def upload_document(file: UploadFile = File(...)):
    if file.size > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds maximum allowed size of {settings.max_file_size} bytes"
        )
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    allowed_extensions = ['.pdf', '.txt', '.docx', '.md', '.html']
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"File type {file_extension} not supported. Allowed types: {allowed_extensions}"
        )
    
    file_path = os.path.join(settings.upload_dir, file.filename)
    
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        start_time = time.time()
        
        chunks, metadata = await document_processor.process_document(file_path, file.filename)
        
        result = await vector_store.add_documents(chunks)
        
        embedding_time = time.time() - start_time
        
        return DocumentUpload(
            id=result.get("document_id", ""),
            filename=file.filename,
            status="success",
            chunks_processed=len(chunks),
            embedding_time=embedding_time,
            metadata=metadata
        )
        
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/upload-batch", response_model=List[DocumentUpload])
async def upload_documents_batch(files: List[UploadFile] = File(...)):
    results = []
    
    for file in files:
        try:
            result = await upload_document(file)
            results.append(result)
        except Exception as e:
            results.append(DocumentUpload(
                id="",
                filename=file.filename,
                status="failed",
                chunks_processed=0,
                embedding_time=0.0,
                metadata=None
            ))
    
    return results

@router.post("/search", response_model=List[SearchResult])
async def search_documents(query: SearchQuery):
    results = await vector_store.search(
        query=query.query,
        max_results=query.max_results,
        document_ids=query.document_ids,
        similarity_threshold=query.similarity_threshold
    )
    
    return results

@router.post("/qa/ask", response_model=AnswerResponse)
async def ask_question(question: QuestionAnswer):
    answer = await qa_service.answer_question(
        question=question.question,
        max_results=question.max_results
    )
    
    return answer

@router.post("/qa/completeness", response_model=CompletenessResponse)
async def check_completeness(check: CompletenessCheck):
    result = await qa_service.check_completeness(
        topics=check.topics,
        document_ids=check.document_ids
    )
    
    return result

@router.get("/index/status", response_model=IndexStatus)
async def get_index_status():
    stats = vector_store.get_index_stats()
    
    documents_count = len(os.listdir(settings.upload_dir))
    
    return IndexStatus(
        total_documents=documents_count,
        total_chunks=stats["total_chunks"],
        index_size_mb=stats["index_size_mb"],
        last_update=datetime.utcnow()
    )

@router.delete("/documents/{document_id}", response_model=DocumentDelete)
async def delete_document(document_id: str):
    result = await vector_store.delete_document(document_id)
    
    return DocumentDelete(
        document_id=document_id,
        status="success" if result["chunks_deleted"] > 0 else "not_found",
        chunks_deleted=result["chunks_deleted"]
    )

@router.put("/documents/{document_id}/update", response_model=DocumentUpload)
async def update_document(document_id: str, file: UploadFile = File(...)):
    await delete_document(document_id)
    
    return await upload_document(file)

@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    documents = vector_store.get_all_documents()
    
    return DocumentListResponse(
        total_documents=len(documents),
        documents=documents
    )