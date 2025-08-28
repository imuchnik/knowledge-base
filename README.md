# AI-Powered Knowledge Base Search & Enrichment

A high-performance semantic search and Q&A system for document management, built with FastAPI, ChromaDB, and Sentence Transformers.

## Features

- **Document Ingestion Pipeline**: Supports PDF, TXT, DOCX, Markdown, and HTML files
- **Vector Embeddings**: Uses Sentence Transformers for semantic search
- **Semantic Search**: Find relevant content across thousands of documents
- **Q&A System**: AI-powered question answering with context from your documents
- **Completeness Check**: Analyze knowledge base coverage for specific topics
- **Incremental Updates**: Efficient document updates without full reindexing
- **Batch Processing**: Upload and process multiple documents simultaneously
- **Large File Support**: Handles documents up to 100MB with chunking

## Architecture & Design Decisions

### Tech Stack
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **ChromaDB**: Embedded vector database for efficient similarity search
- **Sentence Transformers**: State-of-the-art embeddings for semantic search (all-MiniLM-L6-v2)
- **Local Q&A**: Extractive question answering using semantic search and sentence ranking

### Key Design Choices

1. **ChromaDB for Vector Storage**
   - Embedded database (no external dependencies)
   - Persistent storage with efficient similarity search
   - Supports incremental updates and deletions

2. **Chunking Strategy**
   - 1000-word chunks with 200-word overlap
   - Balances context preservation with search precision
   - Configurable chunk size for different use cases

3. **Asynchronous Processing**
   - Non-blocking I/O for file operations
   - Concurrent embedding generation
   - Better performance under load

4. **Modular Architecture**
   - Separate services for document processing, vector storage, and Q&A
   - Easy to extend and maintain
   - Clear separation of concerns

### Trade-offs (24h Time Constraint)

1. **Simplified Authentication**: No auth implemented - would add JWT/OAuth2 in production
2. **Basic Error Handling**: More comprehensive error recovery needed for production
3. **Limited File Types**: Could support more formats (Excel, PowerPoint, etc.)
4. **Single Embedding Model**: Production might use multiple models for different domains
5. **No Caching Layer**: Redis caching would improve response times for frequent queries
6. **Extractive Q&A**: Uses sentence extraction instead of generative models for fully local operation

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd knowledge-base-search
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env to customize settings (all values have defaults)
```

## Running the System

1. Start the API server:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

2. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

### Document Management
- `POST /api/v1/documents/upload` - Upload a single document
- `POST /api/v1/documents/upload-batch` - Upload multiple documents
- `DELETE /api/v1/documents/{document_id}` - Delete a document
- `PUT /api/v1/documents/{document_id}/update` - Update a document

### Search & Q&A
- `POST /api/v1/search` - Semantic search across documents
- `POST /api/v1/qa/ask` - Ask questions and get AI-powered answers
- `POST /api/v1/qa/completeness` - Check knowledge base completeness for topics

### System Status
- `GET /api/v1/index/status` - Get index statistics
- `GET /health` - Health check endpoint

## Usage Examples

### 1. Upload a Document
```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### 2. Search for Content
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "max_results": 5,
    "similarity_threshold": 0.7
  }'
```

### 3. Ask a Question
```bash
curl -X POST "http://localhost:8000/api/v1/qa/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the main types of machine learning?",
    "max_results": 5
  }'
```

### 4. Check Completeness
```bash
curl -X POST "http://localhost:8000/api/v1/qa/completeness" \
  -H "Content-Type: application/json" \
  -d '{
    "topics": ["supervised learning", "unsupervised learning", "reinforcement learning"]
  }'
```

## Testing

Run the test suite:
```bash
pytest tests/ -v
```

## Performance Considerations

- **Batch Processing**: Use batch upload for multiple documents
- **Chunk Size**: Adjust chunk_size in config for your use case
- **Embedding Model**: Smaller models (MiniLM) for speed, larger for accuracy
- **Index Optimization**: ChromaDB automatically optimizes for queries

## Future Enhancements

1. **Authentication & Authorization**
   - User management
   - Document-level permissions
   - API key management

2. **Advanced Features**
   - Real-time document updates via WebSockets
   - Document versioning
   - Multi-language support
   - Custom embedding fine-tuning

3. **Scalability**
   - Distributed vector database (Weaviate/Qdrant)
   - Kubernetes deployment
   - Horizontal scaling with load balancing

4. **Monitoring**
   - Prometheus metrics
   - Query performance tracking
   - Usage analytics

## License

MIT License