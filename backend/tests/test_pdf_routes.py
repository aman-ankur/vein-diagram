import pytest
from fastapi.testclient import TestClient
import os
import tempfile
from app.main import app

# Import client from our shared test_client module instead
from tests.utils.test_client import client

def test_health_check():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_upload_pdf_invalid_file():
    """Test uploading a non-PDF file."""
    # Create a temporary text file
    with tempfile.NamedTemporaryFile(suffix='.txt') as temp_file:
        temp_file.write(b'This is a text file, not a PDF')
        temp_file.flush()
        
        # Try to upload the text file
        with open(temp_file.name, 'rb') as f:
            response = client.post(
                "/api/pdf/upload",
                files={"file": ("test.txt", f, "text/plain")}
            )
        
        # Check that the request was rejected
        assert response.status_code == 400
        assert "File must be a PDF" in response.json()["detail"]

def test_get_pdf_status_not_found():
    """Test getting the status of a non-existent PDF."""
    response = client.get("/api/pdf/status/nonexistent-file-id")
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"] 