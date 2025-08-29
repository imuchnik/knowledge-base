import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import numpy as np
from tqdm import tqdm
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

from app.core.config import settings
from app.models.schemas import SearchResult

class VectorStore:
    def __init__(self):
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.collection_name = "knowledge_base"
        self._ensure_collection()
        
    def _ensure_collection(self):
        try:
            self.collection = self.chroma_client.get_collection(self.collection_name)
        except:
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    async def add_documents(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not chunks:
            return {"status": "error", "message": "No chunks to process"}
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            embeddings = await loop.run_in_executor(
                executor,
                self._batch_encode,
                [chunk["content"] for chunk in chunks]
            )
        
        ids = [chunk["chunk_id"] for chunk in chunks]
        documents = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        batch_size = settings.batch_size
        for i in range(0, len(chunks), batch_size):
            batch_ids = ids[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]
            batch_documents = documents[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            
            self.collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings.tolist(),
                documents=batch_documents,
                metadatas=batch_metadatas
            )
        
        return {
            "status": "success",
            "chunks_added": len(chunks),
            "document_id": chunks[0]["document_id"] if chunks else None
        }
    
    def _batch_encode(self, texts: List[str]) -> np.ndarray:
        return self.embedding_model.encode(texts, show_progress_bar=True)
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[SearchResult]:
        
        query_embedding = self.embedding_model.encode([query])
        
        results = self.collection.query(
            query_embeddings=query_embedding.tolist(),
            n_results=max_results
        )
        
        search_results = []
        for i, (doc_id, document, metadata, distance) in enumerate(
            zip(results["ids"][0], results["documents"][0], 
                results["metadatas"][0], results["distances"][0])
        ):
            similarity_score = 1 - distance
            
            if similarity_score >= similarity_threshold:
                search_results.append(SearchResult(
                    document_id=metadata.get("document_id", ""),
                    filename=metadata.get("filename", ""),
                    chunk_id=doc_id,
                    content=document,
                    similarity_score=similarity_score,
                    metadata=metadata
                ))
        
        return search_results
    
    async def delete_document(self, document_id: str) -> Dict[str, Any]:
        # Get all chunks and filter by document_id prefix in chunk_id
        all_results = self.collection.get()
        
        chunks_to_delete = []
        if all_results and all_results.get("ids"):
            for chunk_id in all_results["ids"]:
                # Check if chunk_id starts with document_id followed by underscore
                if chunk_id.startswith(f"{document_id}_"):
                    chunks_to_delete.append(chunk_id)
        
        if chunks_to_delete:
            self.collection.delete(ids=chunks_to_delete)
            
        return {
            "document_id": document_id,
            "chunks_deleted": len(chunks_to_delete)
        }
    
    async def update_document(self, chunks: List[Dict[str, Any]], document_id: str) -> Dict[str, Any]:
        await self.delete_document(document_id)
        return await self.add_documents(chunks)
    
    def get_index_stats(self) -> Dict[str, Any]:
        count = self.collection.count()
        
        persist_dir_size = 0
        for dirpath, dirnames, filenames in os.walk(settings.chroma_persist_directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                persist_dir_size += os.path.getsize(filepath)
        
        return {
            "total_chunks": count,
            "index_size_mb": persist_dir_size / (1024 * 1024),
            "collection_name": self.collection_name
        }
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        all_data = self.collection.get()
        
        if not all_data or not all_data.get("ids"):
            return []
        
        documents = {}
        
        for i, (chunk_id, metadata) in enumerate(zip(all_data["ids"], all_data["metadatas"])):
            if not metadata:
                continue
                
            document_id = chunk_id.rsplit("_", 1)[0] if chunk_id else None
            
            if document_id:
                if document_id not in documents:
                    documents[document_id] = {
                        "document_id": document_id,
                        "filename": metadata.get("filename", ""),
                        "document_type": metadata.get("document_type", ""),
                        "created_at": metadata.get("created_at", ""),
                        "chunk_count": 0
                    }
                documents[document_id]["chunk_count"] += 1
        
        return list(documents.values())