from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "Knowledge Base Search API"
    debug: bool = False
    
    chroma_persist_directory: str = "./chroma_db"
    upload_dir: str = "./uploaded_documents"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    
    batch_size: int = 10
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    max_search_results: int = 10
    similarity_threshold: float = 0.7
    
    class Config:
        env_file = ".env"
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Path(self.upload_dir).mkdir(parents=True, exist_ok=True)
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)

settings = Settings()