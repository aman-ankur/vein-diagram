import pytest
import os
import tempfile
import time
import concurrent.futures
from io import BytesIO
from unittest.mock import patch, MagicMock
import threading
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

def create_test_pdf(content=""):
    """Create a test PDF with given content."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    
    # Add basic lab data
    pdf.drawString(100, 750, "Lab Test Results")
    pdf.drawString(100, 730, f"Test ID: {content}")
    pdf.drawString(100, 710, "Date: 05/15/2023")
    pdf.drawString(100, 690, "Patient: John Doe")
    
    pdf.drawString(100, 650, "Glucose: 95 mg/dL (70-99)")
    pdf.drawString(100, 630, "HbA1c: 5.4 % (4.0-5.6)")
    pdf.drawString(100, 610, "Total Cholesterol: 185 mg/dL (125-200)")
    
    pdf.save()
    buffer.seek(0)
    return buffer.read()

def upload_pdf(pdf_bytes, filename="test.pdf"):
    """Upload a PDF file and return the response."""
    files = {"file": (filename, pdf_bytes, "application/pdf")}
    return client.post("/api/pdf/upload", files=files)

def check_processing_status(file_id):
    """Check the processing status of a PDF file."""
    max_tries = 20
    status = "pending"
    
    for _ in range(max_tries):
        response = client.get(f"/api/pdf/status/{file_id}")
        if response.status_code == 200:
            status = response.json()["status"]
            if status in ["completed", "error"]:
                break
        time.sleep(0.5)
    
    return status

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_single_pdf_upload_performance(mock_extract, setup_test_db):
    """Test the performance of a single PDF upload and processing."""
    # Mock the biomarker extraction
    mock_extract.return_value = (
        [
            {
                "name": "Glucose",
                "value": 95.0,
                "unit": "mg/dL",
                "reference_range_low": 70.0,
                "reference_range_high": 99.0,
                "category": "Metabolic",
                "is_abnormal": False
            },
            {
                "name": "HbA1c",
                "value": 5.4,
                "unit": "%",
                "reference_range_low": 4.0,
                "reference_range_high": 5.6,
                "category": "Metabolic",
                "is_abnormal": False
            },
            {
                "name": "Total Cholesterol",
                "value": 185.0,
                "unit": "mg/dL",
                "reference_range_low": 125.0,
                "reference_range_high": 200.0,
                "category": "Lipid",
                "is_abnormal": False
            }
        ],
        {
            "lab_name": "Test Lab",
            "report_date": "05/15/2023"
        }
    )
    
    # Create a test PDF
    pdf_bytes = create_test_pdf("single-test")
    
    # Measure upload time
    start_time = time.time()
    response = upload_pdf(pdf_bytes, "performance_test_single.pdf")
    upload_time = time.time() - start_time
    
    # Verify the upload was successful
    assert response.status_code == 200
    file_id = response.json()["file_id"]
    
    # Measure processing time
    start_time = time.time()
    status = check_processing_status(file_id)
    processing_time = time.time() - start_time
    
    # Verify processing was successful
    assert status == "completed"
    
    # Log performance metrics
    print(f"\nSingle PDF Upload Performance:")
    print(f"Upload time: {upload_time:.4f} seconds")
    print(f"Processing time: {processing_time:.4f} seconds")
    print(f"Total time: {upload_time + processing_time:.4f} seconds")
    
    # Assert reasonable performance (these values may need adjustment)
    assert upload_time < 1.0, "Upload took too long"
    assert processing_time < 5.0, "Processing took too long"

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_multiple_concurrent_uploads(mock_extract, setup_test_db):
    """Test the system's ability to handle multiple concurrent PDF uploads."""
    # Mock the biomarker extraction
    mock_extract.return_value = (
        [
            {"name": "Glucose", "value": 95.0, "unit": "mg/dL", "reference_range_low": 70.0, "reference_range_high": 99.0, "category": "Metabolic"},
            {"name": "Total Cholesterol", "value": 185.0, "unit": "mg/dL", "reference_range_low": 125.0, "reference_range_high": 200.0, "category": "Lipid"}
        ],
        {"lab_name": "Test Lab", "report_date": "05/15/2023"}
    )
    
    # Number of concurrent uploads
    num_pdfs = 5
    
    # Create test PDFs
    pdf_files = [(create_test_pdf(f"concurrent-test-{i}"), f"concurrent_test_{i}.pdf") for i in range(num_pdfs)]
    
    # Function to upload a PDF and check processing
    def upload_and_check(pdf_data):
        pdf_bytes, filename = pdf_data
        response = upload_pdf(pdf_bytes, filename)
        assert response.status_code == 200
        file_id = response.json()["file_id"]
        status = check_processing_status(file_id)
        return file_id, status
    
    # Measure total execution time
    start_time = time.time()
    
    # Use ThreadPoolExecutor to run uploads concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_pdfs) as executor:
        futures = [executor.submit(upload_and_check, pdf_data) for pdf_data in pdf_files]
        
        # Get results as they complete
        results = []
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Verify all uploads completed successfully
    for file_id, status in results:
        assert status == "completed", f"Processing failed for file {file_id}"
    
    # Log performance metrics
    print(f"\nConcurrent Uploads Performance ({num_pdfs} PDFs):")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Average time per PDF: {total_time / num_pdfs:.4f} seconds")
    
    # Assert reasonable performance
    assert total_time < 10.0, "Concurrent processing took too long"
    
    # Verify biomarkers were extracted for all PDFs
    for file_id, _ in results:
        response = client.get(f"/api/biomarkers/pdf/{file_id}")
        assert response.status_code == 200
        biomarkers = response.json()
        assert len(biomarkers) == 2

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_sequential_uploads_performance(mock_extract, setup_test_db):
    """Test the performance of sequential PDF uploads compared to concurrent uploads."""
    # Mock the biomarker extraction
    mock_extract.return_value = (
        [
            {"name": "Glucose", "value": 95.0, "unit": "mg/dL", "reference_range_low": 70.0, "reference_range_high": 99.0, "category": "Metabolic"},
            {"name": "Total Cholesterol", "value": 185.0, "unit": "mg/dL", "reference_range_low": 125.0, "reference_range_high": 200.0, "category": "Lipid"}
        ],
        {"lab_name": "Test Lab", "report_date": "05/15/2023"}
    )
    
    # Number of sequential uploads
    num_pdfs = 5
    
    # Create test PDFs
    pdf_files = [(create_test_pdf(f"sequential-test-{i}"), f"sequential_test_{i}.pdf") for i in range(num_pdfs)]
    
    # Measure total execution time
    start_time = time.time()
    
    # Process PDFs sequentially
    results = []
    for pdf_bytes, filename in pdf_files:
        response = upload_pdf(pdf_bytes, filename)
        assert response.status_code == 200
        file_id = response.json()["file_id"]
        status = check_processing_status(file_id)
        results.append((file_id, status))
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Verify all uploads completed successfully
    for file_id, status in results:
        assert status == "completed", f"Processing failed for file {file_id}"
    
    # Log performance metrics
    print(f"\nSequential Uploads Performance ({num_pdfs} PDFs):")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Average time per PDF: {total_time / num_pdfs:.4f} seconds")
    
    # Verify biomarkers were extracted for all PDFs
    for file_id, _ in results:
        response = client.get(f"/api/biomarkers/pdf/{file_id}")
        assert response.status_code == 200
        biomarkers = response.json()
        assert len(biomarkers) == 2

@patch('app.services.pdf_service.extract_biomarkers_with_claude')
def test_system_under_load(mock_extract, setup_test_db):
    """Test the system's performance under load with many concurrent requests."""
    # Mock the biomarker extraction
    mock_extract.return_value = (
        [{"name": "Glucose", "value": 95.0, "unit": "mg/dL", "category": "Metabolic"}],
        {"lab_name": "Test Lab"}
    )
    
    # Number of concurrent uploads and API calls
    num_uploads = 3
    num_api_calls_per_upload = 10
    
    # Create and upload PDFs
    uploaded_file_ids = []
    for i in range(num_uploads):
        pdf_bytes = create_test_pdf(f"load-test-{i}")
        response = upload_pdf(pdf_bytes, f"load_test_{i}.pdf")
        assert response.status_code == 200
        uploaded_file_ids.append(response.json()["file_id"])
    
    # Wait for all PDFs to be processed
    for file_id in uploaded_file_ids:
        status = check_processing_status(file_id)
        assert status == "completed"
    
    # Function to make multiple API calls
    def make_api_calls(file_id):
        results = []
        for _ in range(num_api_calls_per_upload):
            # Make different types of API calls
            responses = [
                client.get(f"/api/biomarkers/pdf/{file_id}"),
                client.get("/api/biomarkers"),
                client.get("/api/biomarkers/categories"),
                client.get("/api/biomarkers/search?q=glucose")
            ]
            results.extend([r.status_code for r in responses])
        return results
    
    # Make concurrent API calls to simulate load
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(make_api_calls, file_id) for file_id in uploaded_file_ids]
        
        # Wait for all futures to complete
        all_results = []
        for future in concurrent.futures.as_completed(futures):
            all_results.extend(future.result())
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Verify all API calls were successful
    for status_code in all_results:
        assert status_code == 200
    
    total_calls = len(all_results)
    
    # Log performance metrics
    print(f"\nSystem Under Load Performance:")
    print(f"Total API calls: {total_calls}")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Average time per call: {total_time / total_calls:.4f} seconds")
    print(f"Calls per second: {total_calls / total_time:.2f}")
    
    # Assert reasonable performance
    assert total_time / total_calls < 0.1, "API calls too slow under load" 