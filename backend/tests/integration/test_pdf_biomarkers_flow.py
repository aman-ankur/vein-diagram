import pytest
import os
import tempfile
import time
from io import BytesIO
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from reportlab.pdfgen import canvas
import json
from datetime import datetime

# Import the client from test_client.py
from tests.utils.test_client import client
from app.db.database import Base, engine, get_db
from app.api.routes.pdf_routes import UPLOAD_DIR
from app.services.biomarker_parser import extract_biomarkers_with_claude
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF

# Create test database tables
@pytest.fixture(scope="function")
def setup_test_db():
    """
    Create a clean database for testing.
    This fixture drops all tables and recreates them, providing a clean slate for each test.
    """
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    yield
    
    # Clean up: Drop all tables again
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_client():
    """Create a test client for FastAPI"""
    from tests.utils.test_client import client
    return client

@pytest.fixture
def sample_pdf_bytes():
    """Create a simple PDF file in memory with lab results data."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    
    # Add test data to PDF
    pdf.drawString(100, 800, "Lab Test Results")
    pdf.drawString(100, 780, "Date: 05/15/2023")
    pdf.drawString(100, 760, "Patient: John Doe")
    pdf.drawString(100, 740, "Lab: LabCorp")
    
    pdf.drawString(100, 700, "Glucose: 95 mg/dL (70-99)")
    pdf.drawString(100, 680, "Total Cholesterol: 185 mg/dL (125-200)")
    
    pdf.save()
    buffer.seek(0)
    return buffer.read()

@pytest.fixture
def sample_pdf_file(sample_pdf_bytes):
    """
    Create a temporary PDF file for testing.
    This fixture creates a real PDF file on disk that is cleaned up after the test.
    """
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(sample_pdf_bytes)
        tmp_path = tmp.name
    
    yield tmp_path
    
    # Clean up the file
    if os.path.exists(tmp_path):
        os.unlink(tmp_path)

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_pdf_upload_and_biomarker_extraction(mock_extract, setup_test_db, sample_pdf_bytes):
    """
    Test the complete flow of uploading a PDF and extracting biomarkers.
    This test covers:
    1. Uploading a PDF file
    2. Checking the processing status
    3. Verifying that biomarkers are extracted
    4. Retrieving the biomarkers via API
    """
    # Mock the biomarker extraction function
    mock_extract.return_value = (
        [
            {
                "name": "Glucose",
                "original_name": "Glucose",
                "value": 95.0,
                "original_value": "95",
                "unit": "mg/dL",
                "original_unit": "mg/dL",
                "reference_range_low": 70.0,
                "reference_range_high": 99.0,
                "reference_range_text": "70-99",
                "category": "Metabolic",
                "is_abnormal": False
            },
            {
                "name": "Total Cholesterol",
                "original_name": "Total Cholesterol",
                "value": 185.0,
                "original_value": "185",
                "unit": "mg/dL",
                "original_unit": "mg/dL",
                "reference_range_low": 125.0,
                "reference_range_high": 200.0,
                "reference_range_text": "125-200",
                "category": "Lipid",
                "is_abnormal": False
            }
        ],
        {
            "lab_name": "LabCorp",
            "report_date": "05/15/2023"
        }
    )
    
    # Step 1: Upload PDF
    files = {"file": ("test.pdf", sample_pdf_bytes, "application/pdf")}
    response = client.post("/api/pdf/upload", files=files)
    assert response.status_code == 200
    
    # Get the file_id from response
    file_id = response.json()["file_id"]
    assert file_id is not None
    
    # Step 2: Wait for processing to complete (with a timeout)
    max_tries = 10
    for _ in range(max_tries):
        status_response = client.get(f"/api/pdf/status/{file_id}")
        assert status_response.status_code == 200
        
        status = status_response.json()["status"]
        if status == "completed":
            break
        elif status == "error":
            assert False, f"PDF processing failed with error: {status_response.json().get('error', 'Unknown error')}"
        
        # Wait a bit before trying again
        time.sleep(0.5)
    
    assert status == "completed", f"PDF processing did not complete in time. Last status: {status}"
    
    # Step 3: Get extracted biomarkers
    biomarkers_response = client.get(f"/api/biomarkers/pdf/{file_id}")
    assert biomarkers_response.status_code == 200
    
    biomarkers_data = biomarkers_response.json()
    assert len(biomarkers_data) == 2
    
    # Verify the glucose biomarker data
    glucose = next(b for b in biomarkers_data if b["name"] == "Glucose")
    assert glucose["value"] == 95.0
    assert glucose["unit"] == "mg/dL"
    assert glucose["category"] == "Metabolic"
    assert glucose["is_abnormal"] is False
    
    # Verify the cholesterol biomarker data
    cholesterol = next(b for b in biomarkers_data if b["name"] == "Total Cholesterol")
    assert cholesterol["value"] == 185.0
    assert cholesterol["unit"] == "mg/dL"
    assert cholesterol["category"] == "Lipid"
    assert cholesterol["is_abnormal"] is False
    
    # Step 4: Test getting all biomarkers
    all_biomarkers_response = client.get("/api/biomarkers")
    assert all_biomarkers_response.status_code == 200
    
    all_biomarkers = all_biomarkers_response.json()
    assert len(all_biomarkers) == 2
    
    # Ensure the biomarkers were properly stored in the database with the file_id
    biomarker_ids = {b["id"] for b in all_biomarkers}
    assert len(biomarker_ids) == 2

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_pdf_upload_with_error_handling(mock_extract, setup_test_db, sample_pdf_bytes):
    """
    Test uploading a PDF that encounters an error during processing.
    This tests the error handling in the background processing.
    """
    # Mock the biomarker extraction function to raise an exception
    mock_extract.side_effect = Exception("Test processing error")
    
    # Upload PDF
    files = {"file": ("test_error.pdf", sample_pdf_bytes, "application/pdf")}
    response = client.post("/api/pdf/upload", files=files)
    assert response.status_code == 200
    
    # Get the file_id from response
    file_id = response.json()["file_id"]
    assert file_id is not None
    
    # Wait for processing to report error (with a timeout)
    max_tries = 10
    for _ in range(max_tries):
        status_response = client.get(f"/api/pdf/status/{file_id}")
        assert status_response.status_code == 200
        
        status = status_response.json()["status"]
        if status == "error":
            break
        
        # Wait a bit before trying again
        time.sleep(0.5)
    
    assert status == "error", f"Expected error status but got: {status}"
    assert "error" in status_response.json(), "Error status should include an error message"

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_searching_biomarkers_after_upload(mock_extract, setup_test_db, sample_pdf_bytes):
    """
    Test searching for biomarkers after uploading a PDF.
    This tests the search functionality in the biomarker routes.
    """
    # Mock the biomarker extraction function
    mock_extract.return_value = (
        [
            {
                "name": "Glucose",
                "original_name": "Glucose",
                "value": 95.0,
                "unit": "mg/dL",
                "reference_range_low": 70.0,
                "reference_range_high": 99.0,
                "category": "Metabolic",
                "is_abnormal": False
            },
            {
                "name": "Total Cholesterol",
                "original_name": "Total Cholesterol",
                "value": 185.0,
                "unit": "mg/dL",
                "reference_range_low": 125.0,
                "reference_range_high": 200.0,
                "category": "Lipid",
                "is_abnormal": False
            },
            {
                "name": "HDL Cholesterol",
                "original_name": "HDL Cholesterol",
                "value": 55.0,
                "unit": "mg/dL",
                "reference_range_low": 40.0,
                "reference_range_high": None,
                "category": "Lipid",
                "is_abnormal": False
            }
        ],
        {"lab_name": "LabCorp"}
    )
    
    # Upload PDF
    files = {"file": ("test.pdf", sample_pdf_bytes, "application/pdf")}
    response = client.post("/api/pdf/upload", files=files)
    assert response.status_code == 200
    
    # Get the file_id from response
    file_id = response.json()["file_id"]
    
    # Wait for processing to complete
    max_tries = 10
    for _ in range(max_tries):
        status_response = client.get(f"/api/pdf/status/{file_id}")
        if status_response.json()["status"] == "completed":
            break
        time.sleep(0.5)
    
    # Search for cholesterol biomarkers
    search_response = client.get("/api/biomarkers/search?q=cholesterol")
    assert search_response.status_code == 200
    
    search_results = search_response.json()
    assert len(search_results) == 2  # Should find both Total Cholesterol and HDL Cholesterol
    
    # Filter by category
    category_response = client.get("/api/biomarkers?category=Lipid")
    assert category_response.status_code == 200
    
    category_results = category_response.json()
    assert len(category_results) == 2  # Should find both cholesterol biomarkers
    
    # Get biomarker categories
    categories_response = client.get("/api/biomarkers/categories")
    assert categories_response.status_code == 200
    
    categories = categories_response.json()
    assert "Lipid" in categories
    assert "Metabolic" in categories 