from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.routes import router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["knowledge-base"])

@app.get("/")
async def root():
    return {
        "message": "Knowledge Base Search & Enrichment API",
        "version": "1.0.0",
        "endpoints": {
            "upload": "/api/v1/documents/upload",
            "batch_upload": "/api/v1/documents/upload-batch",
            "search": "/api/v1/search",
            "ask": "/api/v1/qa/ask",
            "completeness": "/api/v1/qa/completeness",
            "index_status": "/api/v1/index/status",
            "delete": "/api/v1/documents/{document_id}",
            "update": "/api/v1/documents/{document_id}/update"
        }
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)