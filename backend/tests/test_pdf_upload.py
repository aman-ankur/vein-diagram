import pytest
import io
import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.pdf_model import PDF

client = TestClient(app)

@pytest.fixture
def mock_pdf_file():
    """Create a mock PDF file for testing."""
    # This is a minimal valid PDF file content, using only ASCII characters
    content = b"%PDF-1.7\n1 0 obj\n<</Type/Catalog/Pages 2 0 R>>\nendobj\n2 0 obj\n<</Type/Pages/Kids[3 0 R]/Count 1>>\nendobj\n3 0 obj\n<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<<>>>>\nendobj\nxref\n0 4\n0000000000 65535 f\n0000000015 00000 n\n0000000060 00000 n\n0000000111 00000 n\ntrailer\n<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF\n"
    return io.BytesIO(content)

def test_upload_pdf_valid(mock_pdf_file, test_db: Session, monkeypatch):
    """Test uploading a valid PDF file."""
    # Mock the background task to avoid actual processing
    mock_background = MagicMock()
    monkeypatch.setattr("app.api.routes.pdf_routes.process_pdf_background", mock_background)
    
    # Test file upload
    response = client.post(
        "/api/pdf/upload",
        files={"file": ("test.pdf", mock_pdf_file, "application/pdf")}
    )
    
    # Check the response
    assert response.status_code == 200
    response_data = response.json()
    assert "file_id" in response_data
    assert response_data["status"] == "pending"
    assert response_data["filename"] == "test.pdf"
    
    # Check that the file was saved in the database
    pdf_in_db = test_db.query(PDF).filter(PDF.file_id == response_data["file_id"]).first()
    assert pdf_in_db is not None
    assert pdf_in_db.filename == "test.pdf"
    assert pdf_in_db.status == "pending"
    
    # Verify the file exists on disk
    assert os.path.exists(pdf_in_db.file_path)
    
    # Clean up the file
    os.remove(pdf_in_db.file_path)

def test_upload_non_pdf_file(test_db: Session):
    """Test uploading a non-PDF file."""
    # Create a text file
    text_file = io.BytesIO(b"This is not a PDF file")
    
    # Test file upload
    response = client.post(
        "/api/pdf/upload",
        files={"file": ("test.txt", text_file, "text/plain")}
    )
    
    # Check the response
    assert response.status_code == 400
    assert "File must be a PDF" in response.json()["detail"]

def test_get_pdf_status(test_db: Session, mock_pdf_file, monkeypatch):
    """Test getting the status of a PDF file."""
    # Mock the background task to avoid actual processing
    mock_background = MagicMock()
    monkeypatch.setattr("app.api.routes.pdf_routes.process_pdf_background", mock_background)
    
    # First upload a file
    upload_response = client.post(
        "/api/pdf/upload",
        files={"file": ("test.pdf", mock_pdf_file, "application/pdf")}
    )
    file_id = upload_response.json()["file_id"]
    
    # Test getting the status
    status_response = client.get(f"/api/pdf/status/{file_id}")
    
    # Check the response
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["file_id"] == file_id
    assert status_data["status"] == "pending"
    assert status_data["filename"] == "test.pdf"
    
    # Clean up the file
    pdf_in_db = test_db.query(PDF).filter(PDF.file_id == file_id).first()
    os.remove(pdf_in_db.file_path)

def test_list_pdfs(test_db: Session, mock_pdf_file, monkeypatch):
    """Test listing PDF files."""
    # Mock the background task to avoid actual processing
    mock_background = MagicMock()
    monkeypatch.setattr("app.api.routes.pdf_routes.process_pdf_background", mock_background)
    
    # Upload two files
    file1 = mock_pdf_file
    file2 = io.BytesIO(file1.getvalue())  # Make a copy of the file
    
    client.post("/api/pdf/upload", files={"file": ("test1.pdf", file1, "application/pdf")})
    client.post("/api/pdf/upload", files={"file": ("test2.pdf", file2, "application/pdf")})
    
    # Test listing files
    list_response = client.get("/api/pdf/list")
    
    # Check the response
    assert list_response.status_code == 200
    response_data = list_response.json()
    assert "total" in response_data
    assert "pdfs" in response_data
    assert response_data["total"] >= 2  # At least our two uploads
    
    # Verify our uploaded files are in the list
    filenames = [pdf["filename"] for pdf in response_data["pdfs"]]
    assert "test1.pdf" in filenames
    assert "test2.pdf" in filenames
    
    # Clean up the files
    for pdf in test_db.query(PDF).filter(PDF.filename.in_(["test1.pdf", "test2.pdf"])).all():
        if os.path.exists(pdf.file_path):
            os.remove(pdf.file_path)

def test_delete_pdf(test_db: Session, mock_pdf_file, monkeypatch):
    """Test deleting a PDF file."""
    # Mock the background task to avoid actual processing
    mock_background = MagicMock()
    monkeypatch.setattr("app.api.routes.pdf_routes.process_pdf_background", mock_background)
    
    # First upload a file
    upload_response = client.post(
        "/api/pdf/upload",
        files={"file": ("test_delete.pdf", mock_pdf_file, "application/pdf")}
    )
    file_id = upload_response.json()["file_id"]
    
    # Get the file path
    pdf_in_db = test_db.query(PDF).filter(PDF.file_id == file_id).first()
    file_path = pdf_in_db.file_path
    
    # Test deleting the file
    delete_response = client.delete(f"/api/pdf/{file_id}")
    
    # Check the response
    assert delete_response.status_code == 200
    assert "deleted successfully" in delete_response.json()["message"]
    
    # Check that the file was deleted from the database
    assert test_db.query(PDF).filter(PDF.file_id == file_id).first() is None
    
    # Check that the file was deleted from disk
    assert not os.path.exists(file_path) 