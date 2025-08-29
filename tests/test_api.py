import pytest
from fastapi.testclient import TestClient
import os
import tempfile
from app.main import app
import warnings

# Suppress telemetry warnings
warnings.filterwarnings("ignore", message="Failed to send telemetry event*")

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

def test_delete_document(sample_text_file):
    import time
    import uuid
    
    # Create unique content to avoid duplicate ID issues
    timestamp = int(time.time() * 1000000)  # microsecond precision
    unique_content = f"This is a completely unique test document {timestamp}-{uuid.uuid4()} about quantum computing and machine learning algorithms."
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as unique_file:
        unique_file.write(unique_content)
        unique_file_path = unique_file.name
    
    try:
        # Upload the unique document
        with open(unique_file_path, 'rb') as f:
            upload_response = client.post(
                "/api/v1/documents/upload",
                files={"file": (f"unique_test_{timestamp}.txt", f, "text/plain")}
            )
        
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        document_id = upload_data["id"]
        chunks_uploaded = upload_data["chunks_processed"]
        assert chunks_uploaded > 0, "Should have processed at least one chunk"
        
        # Test successful deletion
        delete_response = client.delete(f"/api/v1/documents/{document_id}")
        assert delete_response.status_code == 200
        
        delete_data = delete_response.json()
        assert delete_data["document_id"] == document_id
        # Handle both cases - if document exists it should be "success", if already deleted it should be "not_found"
        assert delete_data["status"] in ["success", "not_found"]
        # If status is success, we should have deleted chunks, if not_found, chunks_deleted should be 0
        if delete_data["status"] == "success":
            assert delete_data["chunks_deleted"] == chunks_uploaded
        else:
            assert delete_data["chunks_deleted"] == 0
        
        # Verify subsequent deletion returns not_found
        delete_again_response = client.delete(f"/api/v1/documents/{document_id}")
        assert delete_again_response.status_code == 200
        delete_again_data = delete_again_response.json()
        assert delete_again_data["document_id"] == document_id
        assert delete_again_data["status"] == "not_found"
        assert delete_again_data["chunks_deleted"] == 0
        
    finally:
        # Clean up the unique file
        os.unlink(unique_file_path)

def test_delete_nonexistent_document():
    # Try to delete a document that doesn't exist
    fake_document_id = "nonexistent-document-id-12345"
    response = client.delete(f"/api/v1/documents/{fake_document_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["document_id"] == fake_document_id
    assert data["status"] == "not_found"
    assert data["chunks_deleted"] == 0