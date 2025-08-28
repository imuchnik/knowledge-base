import pytest
from fastapi.testclient import TestClient
import os
import tempfile
from app.main import app

client = TestClient(app)

@pytest.fixture
def sample_text_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document about machine learning and artificial intelligence.")
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "Knowledge Base Search & Enrichment API" in response.json()["message"]

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_upload_document(sample_text_file):
    with open(sample_text_file, 'rb') as f:
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", f, "text/plain")}
        )
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["chunks_processed"] > 0
    assert data["filename"] == "test.txt"

def test_search_documents():
    response = client.post(
        "/api/v1/search",
        json={
            "query": "machine learning",
            "max_results": 5
        }
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_ask_question():
    response = client.post(
        "/api/v1/qa/ask",
        json={
            "question": "What is machine learning?",
            "max_results": 3
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "answer" in data
    assert "sources" in data
    assert "confidence" in data

def test_completeness_check():
    response = client.post(
        "/api/v1/qa/completeness",
        json={
            "topics": ["machine learning", "deep learning"]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "overall_completeness" in data
    assert "results" in data
    assert "recommendations" in data

def test_index_status():
    response = client.get("/api/v1/index/status")
    assert response.status_code == 200
    data = response.json()
    assert "total_documents" in data
    assert "total_chunks" in data
    assert "index_size_mb" in data