import pytest
import os
import tempfile
import time
from io import BytesIO
from unittest.mock import patch, MagicMock
from reportlab.pdfgen import canvas
import json
from datetime import datetime

from tests.utils.test_client import client
from app.db.database import Base, engine, get_db
from app.api.routes.pdf_routes import UPLOAD_DIR
from app.services.biomarker_parser import extract_biomarkers_with_claude
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF

@pytest.fixture(scope="function")
def setup_test_db():
    """Create a clean database for testing."""
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    yield
    
    # Clean up
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def empty_pdf_bytes():
    """Create an empty PDF file in memory."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.save()
    buffer.seek(0)
    return buffer.read()

@pytest.fixture
def no_biomarkers_pdf_bytes():
    """Create a PDF file with text but no biomarkers."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    
    # Add text that doesn't contain biomarkers
    pdf.drawString(100, 800, "Medical Report")
    pdf.drawString(100, 780, "Date: 05/15/2023")
    pdf.drawString(100, 760, "Patient: John Doe")
    pdf.drawString(100, 740, "Doctor's Notes")
    pdf.drawString(100, 720, "Patient appears healthy and has no complaints.")
    pdf.drawString(100, 700, "Follow up in 6 months.")
    
    pdf.save()
    buffer.seek(0)
    return buffer.read()

@pytest.fixture
def special_chars_pdf_bytes():
    """Create a PDF file with biomarkers containing special characters."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    
    # Add biomarkers with special characters
    pdf.drawString(100, 800, "Lab Test Results with Special Characters")
    pdf.drawString(100, 780, "Date: 05/15/2023")
    pdf.drawString(100, 760, "Lab: SpecialLab™")
    
    pdf.drawString(100, 700, "Glucose (α-D): 95 mg/dL (70-99)")
    pdf.drawString(100, 680, "Vitamin-D₂₅: 32 ng/mL (30-100)")
    pdf.drawString(100, 660, "β-Carotene: 110 μg/dL (5-150)")
    
    pdf.save()
    buffer.seek(0)
    return buffer.read()

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_upload_empty_pdf(mock_extract, setup_test_db, empty_pdf_bytes):
    """Test uploading an empty PDF file."""
    # Mock the extraction function to return empty results
    mock_extract.return_value = ([], {})
    
    # Upload PDF
    files = {"file": ("empty.pdf", empty_pdf_bytes, "application/pdf")}
    response = client.post("/api/pdf/upload", files=files)
    assert response.status_code == 200
    
    file_id = response.json()["file_id"]
    assert file_id is not None
    
    # Wait for processing to complete
    max_tries = 10
    for _ in range(max_tries):
        status_response = client.get(f"/api/pdf/status/{file_id}")
        assert status_response.status_code == 200
        
        status = status_response.json()["status"]
        if status == "completed" or status == "error":
            break
        time.sleep(0.5)
    
    # The processing should complete but with no biomarkers
    assert status == "completed", "Processing should complete even for empty PDFs"
    
    # Get biomarkers (should be empty)
    biomarkers_response = client.get(f"/api/biomarkers/pdf/{file_id}")
    assert biomarkers_response.status_code == 200
    
    biomarkers_data = biomarkers_response.json()
    assert len(biomarkers_data) == 0, "Empty PDF should have no biomarkers"

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_upload_pdf_no_biomarkers(mock_extract, setup_test_db, no_biomarkers_pdf_bytes):
    """Test uploading a PDF file with no biomarkers."""
    # Mock the extraction function to return empty biomarkers but with metadata
    mock_extract.return_value = (
        [],
        {
            "lab_name": "Unknown",
            "report_date": "05/15/2023",
            "patient_name": "John Doe"
        }
    )
    
    # Upload PDF
    files = {"file": ("no_biomarkers.pdf", no_biomarkers_pdf_bytes, "application/pdf")}
    response = client.post("/api/pdf/upload", files=files)
    assert response.status_code == 200
    
    file_id = response.json()["file_id"]
    
    # Wait for processing to complete
    max_tries = 10
    for _ in range(max_tries):
        status_response = client.get(f"/api/pdf/status/{file_id}")
        if status_response.json()["status"] == "completed":
            break
        time.sleep(0.5)
    
    # Check PDF record has metadata but no biomarkers
    pdf_response = client.get(f"/api/pdf/{file_id}")
    assert pdf_response.status_code == 200
    
    pdf_data = pdf_response.json()
    assert pdf_data["lab_name"] == "Unknown"
    assert pdf_data["patient_name"] == "John Doe"
    
    # Get biomarkers (should be empty)
    biomarkers_response = client.get(f"/api/biomarkers/pdf/{file_id}")
    assert biomarkers_response.status_code == 200
    assert len(biomarkers_response.json()) == 0

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_upload_pdf_with_special_chars(mock_extract, setup_test_db, special_chars_pdf_bytes):
    """Test uploading a PDF file with biomarkers containing special characters."""
    # Mock the biomarker extraction with special characters
    mock_extract.return_value = (
        [
            {
                "name": "Glucose (α-D)",
                "original_name": "Glucose (α-D)",
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
                "name": "Vitamin-D₂₅",
                "original_name": "Vitamin-D₂₅",
                "value": 32.0,
                "original_value": "32",
                "unit": "ng/mL",
                "original_unit": "ng/mL",
                "reference_range_low": 30.0,
                "reference_range_high": 100.0,
                "reference_range_text": "30-100",
                "category": "Vitamin",
                "is_abnormal": False
            },
            {
                "name": "β-Carotene",
                "original_name": "β-Carotene",
                "value": 110.0,
                "original_value": "110",
                "unit": "μg/dL",
                "original_unit": "μg/dL",
                "reference_range_low": 5.0,
                "reference_range_high": 150.0,
                "reference_range_text": "5-150",
                "category": "Vitamin",
                "is_abnormal": False
            }
        ],
        {
            "lab_name": "SpecialLab™",
            "report_date": "05/15/2023"
        }
    )
    
    # Upload PDF
    files = {"file": ("special_chars.pdf", special_chars_pdf_bytes, "application/pdf")}
    response = client.post("/api/pdf/upload", files=files)
    assert response.status_code == 200
    
    file_id = response.json()["file_id"]
    
    # Wait for processing to complete
    max_tries = 10
    for _ in range(max_tries):
        status_response = client.get(f"/api/pdf/status/{file_id}")
        if status_response.json()["status"] == "completed":
            break
        time.sleep(0.5)
    
    # Get biomarkers
    biomarkers_response = client.get(f"/api/biomarkers/pdf/{file_id}")
    assert biomarkers_response.status_code == 200
    
    biomarkers_data = biomarkers_response.json()
    assert len(biomarkers_data) == 3
    
    # Verify special characters were preserved
    biomarker_names = [b["name"] for b in biomarkers_data]
    assert "Glucose (α-D)" in biomarker_names
    assert "Vitamin-D₂₅" in biomarker_names
    assert "β-Carotene" in biomarker_names
    
    # Verify unicode units were preserved
    beta_carotene = next(b for b in biomarkers_data if b["name"] == "β-Carotene")
    assert beta_carotene["unit"] == "μg/dL"

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_malformed_api_response(mock_extract, setup_test_db, empty_pdf_bytes):
    """Test handling of malformed API responses."""
    # Mock a malformed response with missing required fields
    mock_extract.return_value = (
        [
            {
                "name": "Glucose",
                # Missing value field
                "unit": "mg/dL"
                # Missing other fields
            }
        ],
        {
            "lab_name": "Test Lab"
        }
    )
    
    # Upload PDF
    files = {"file": ("malformed.pdf", empty_pdf_bytes, "application/pdf")}
    response = client.post("/api/pdf/upload", files=files)
    assert response.status_code == 200
    
    file_id = response.json()["file_id"]
    
    # Wait for processing to complete
    max_tries = 10
    for _ in range(max_tries):
        status_response = client.get(f"/api/pdf/status/{file_id}")
        status = status_response.json()["status"]
        if status == "completed" or status == "error":
            break
        time.sleep(0.5)
    
    # System should handle malformed response gracefully
    assert status == "completed" or status == "error"
    
    # If processing completed, the missing fields should be handled with defaults
    if status == "completed":
        biomarkers_response = client.get(f"/api/biomarkers/pdf/{file_id}")
        assert biomarkers_response.status_code == 200
        
        biomarkers_data = biomarkers_response.json()
        if len(biomarkers_data) > 0:
            glucose = biomarkers_data[0]
            assert glucose["name"] == "Glucose"
            assert "value" in glucose  # Should have a default value
            assert glucose["unit"] == "mg/dL"

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_large_number_of_biomarkers(mock_extract, setup_test_db, empty_pdf_bytes):
    """Test handling a large number of biomarkers."""
    # Generate a large set of biomarkers
    large_biomarker_set = []
    for i in range(100):  # Create 100 biomarkers
        large_biomarker_set.append({
            "name": f"Test Biomarker {i}",
            "original_name": f"Test Biomarker {i}",
            "value": float(i),
            "original_value": str(i),
            "unit": "mg/dL",
            "original_unit": "mg/dL",
            "reference_range_low": 0.0,
            "reference_range_high": 100.0,
            "reference_range_text": "0-100",
            "category": "Test",
            "is_abnormal": i > 100
        })
    
    # Mock the extraction function
    mock_extract.return_value = (
        large_biomarker_set,
        {"lab_name": "Large Lab"}
    )
    
    # Upload PDF
    files = {"file": ("large.pdf", empty_pdf_bytes, "application/pdf")}
    response = client.post("/api/pdf/upload", files=files)
    assert response.status_code == 200
    
    file_id = response.json()["file_id"]
    
    # Wait for processing to complete (may take longer)
    max_tries = 15
    for _ in range(max_tries):
        status_response = client.get(f"/api/pdf/status/{file_id}")
        if status_response.json()["status"] == "completed":
            break
        time.sleep(1)  # Longer wait time for large dataset
    
    # Get all biomarkers
    biomarkers_response = client.get(f"/api/biomarkers/pdf/{file_id}")
    assert biomarkers_response.status_code == 200
    
    biomarkers_data = biomarkers_response.json()
    assert len(biomarkers_data) == 100
    
    # Test pagination
    paginated_response = client.get("/api/biomarkers?limit=10&offset=0")
    assert paginated_response.status_code == 200
    
    paginated_data = paginated_response.json()
    assert len(paginated_data) == 10
    
    # Test the second page
    second_page = client.get("/api/biomarkers?limit=10&offset=10")
    assert second_page.status_code == 200
    assert len(second_page.json()) == 10
    
    # Ensure all biomarkers are different between pages
    first_page_ids = [b["id"] for b in paginated_data]
    second_page_ids = [b["id"] for b in second_page.json()]
    assert not any(bid in second_page_ids for bid in first_page_ids) 