import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime
from sqlalchemy.orm import Session

import PyPDF2
from app.services.pdf_service import (
    extract_text_from_pdf,
    _extract_text_with_ocr,
    process_pdf_background,
    parse_biomarkers_from_text
)
from app.models.pdf_model import PDF
from app.models.biomarker_model import Biomarker

@pytest.fixture
def sample_pdf_bytes():
    """Create a simple PDF file in memory"""
    # This is a very basic test PDF with minimal content
    return b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Parent 2 0 R/Resources<</Font<</F1<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>>>>>>endobj 4 0 obj<</Length 44>>stream\nBT /F1 12 Tf 100 700 Td (Glucose: 95 mg/dL) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000010 00000 n\n0000000056 00000 n\n0000000111 00000 n\n0000000254 00000 n\ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n345\n%%EOF"

@pytest.fixture
def sample_pdf_file(sample_pdf_bytes):
    """Create a temporary PDF file for testing"""
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(sample_pdf_bytes)
        pdf_path = f.name
    
    yield pdf_path
    
    # Clean up the temporary file
    if os.path.exists(pdf_path):
        os.remove(pdf_path)

@pytest.fixture
def mock_db_session():
    """Create a mock database session"""
    session = MagicMock(spec=Session)
    
    # Mock query builder
    query_mock = MagicMock()
    session.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = None
    
    return session

@pytest.fixture
def sample_pdf_model():
    """Create a sample PDF model for testing"""
    return PDF(
        id=1,
        file_id="test_file_id",
        filename="test.pdf",
        file_path="/path/to/test.pdf",
        status="pending",
        upload_date=datetime.utcnow()
    )

def test_extract_text_from_pdf(sample_pdf_file):
    """Test extracting text from a PDF file"""
    # Extract text from the test PDF
    text = extract_text_from_pdf(sample_pdf_file)
    
    # Verify that some text was extracted
    assert text is not None
    assert len(text) > 0
    
    # Check for specific content (might vary based on PDF library version)
    # This test might be brittle due to differences in PDF parsing libraries
    assert "Glucose" in text or "glucose" in text or "95" in text or "mg/dL" in text

@patch("pdf2image.convert_from_path")
@patch("pytesseract.image_to_string")
def test_extract_text_with_ocr(mock_image_to_string, mock_convert_from_path):
    """Test OCR text extraction from image-based PDFs"""
    # Mock the conversion of PDF to images
    mock_image = MagicMock()
    mock_convert_from_path.return_value = [mock_image]
    
    # Mock the OCR result
    mock_image_to_string.return_value = "Glucose: 95 mg/dL"
    
    # Call the OCR function
    text = _extract_text_with_ocr("dummy_path.pdf")
    
    # Verify the result
    assert "Glucose: 95 mg/dL" in text
    
    # Verify the mocks were called
    mock_convert_from_path.assert_called_once_with("dummy_path.pdf", dpi=300)
    mock_image_to_string.assert_called_once_with(mock_image)

@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
def test_process_pdf_background_success(mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model):
    """Test successful PDF processing in the background"""
    # Setup mocks
    mock_extract_text.return_value = "Glucose: 95 mg/dL"
    
    # Mock biomarker extraction
    mock_extract_biomarkers.return_value = (
        [
            {
                "name": "Glucose",
                "original_name": "Glucose",
                "original_value": "95",
                "original_unit": "mg/dL",
                "value": 95.0,
                "unit": "mg/dL",
                "reference_range_low": 70.0,
                "reference_range_high": 99.0,
                "reference_range_text": "70-99",
                "category": "Metabolic",
                "is_abnormal": False
            }
        ],
        {
            "lab_name": "Test Lab",
            "report_date": "01/15/2023"
        }
    )
    
    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model
    
    # Call the function
    process_pdf_background("/path/to/test.pdf", "test_file_id", mock_db_session)
    
    # Verify text extraction was called
    mock_extract_text.assert_called_once_with("/path/to/test.pdf")
    
    # Verify biomarker extraction was called
    mock_extract_biomarkers.assert_called_once()
    
    # Verify database operations
    assert sample_pdf_model.status == "processed"
    assert sample_pdf_model.processed_date is not None
    assert sample_pdf_model.lab_name == "Test Lab"
    
    # Verify that a biomarker was added to the database
    mock_db_session.add.assert_called()
    
    # Verify commit was called
    mock_db_session.commit.assert_called()

@patch("app.services.pdf_service.extract_text_from_pdf")
def test_process_pdf_background_error(mock_extract_text, mock_db_session, sample_pdf_model):
    """Test error handling during PDF processing"""
    # Setup mock to raise an exception
    mock_extract_text.side_effect = Exception("Test error")
    
    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model
    
    # Call the function
    process_pdf_background("/path/to/test.pdf", "test_file_id", mock_db_session)
    
    # Verify status is set to error
    assert sample_pdf_model.status == "error"
    assert sample_pdf_model.error_message == "Test error"
    
    # Verify commit was called
    mock_db_session.commit.assert_called()

@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
def test_process_pdf_background_with_metadata(mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model):
    """Test PDF processing with metadata extraction"""
    # Setup mocks
    mock_extract_text.return_value = "Lab: LabCorp\nDate: 01/15/2023\nPatient: John Doe\nGlucose: 95 mg/dL"
    
    # Mock biomarker extraction with metadata
    mock_extract_biomarkers.return_value = (
        [
            {
                "name": "Glucose",
                "original_name": "Glucose",
                "original_value": "95",
                "original_unit": "mg/dL",
                "value": 95.0,
                "unit": "mg/dL",
                "reference_range_low": 70.0,
                "reference_range_high": 99.0,
                "reference_range_text": "70-99",
                "category": "Metabolic",
                "is_abnormal": False
            }
        ],
        {
            "lab_name": "LabCorp",
            "report_date": "01/15/2023",
            "patient_name": "John Doe",
            "custom_field": "custom_value"
        }
    )
    
    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model
    
    # Call the function
    process_pdf_background("/path/to/test.pdf", "test_file_id", mock_db_session)
    
    # Verify standard fields were updated
    assert sample_pdf_model.lab_name == "LabCorp"
    assert sample_pdf_model.patient_name == "John Doe"
    
    # Verify custom fields were saved in processing_details
    assert "custom_field" in sample_pdf_model.processing_details
    assert sample_pdf_model.processing_details["custom_field"] == "custom_value"

@patch("app.services.biomarker_parser.parse_biomarkers_from_text")
def test_parse_biomarkers_from_text_wrapper(mock_parser):
    """Test the parse_biomarkers_from_text wrapper function"""
    # Setup mock
    mock_parser.return_value = [
        {
            "name": "Glucose",
            "value": 95.0,
            "unit": "mg/dL",
            "reference_range": "70-99",
            "category": "Metabolic"
        }
    ]
    
    # Call the function
    result = parse_biomarkers_from_text("Glucose: 95 mg/dL")
    
    # Verify the result
    assert result == mock_parser.return_value
    
    # Verify the mock was called
    mock_parser.assert_called_once_with("Glucose: 95 mg/dL")

@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
def test_extract_report_date_fallback(mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model):
    """Test extraction of report date when not provided by Claude"""
    # Setup mocks
    mock_extract_text.return_value = "Test report from 01/15/2023 with Glucose: 95 mg/dL"
    
    # Mock biomarker extraction without report date
    mock_extract_biomarkers.return_value = (
        [
            {
                "name": "Glucose",
                "original_name": "Glucose",
                "original_value": "95",
                "original_unit": "mg/dL",
                "value": 95.0,
                "unit": "mg/dL",
                "category": "Metabolic"
            }
        ],
        {
            "lab_name": "Test Lab"
            # No report_date here
        }
    )
    
    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model
    
    # Call the function
    process_pdf_background("/path/to/test.pdf", "test_file_id", mock_db_session)
    
    # Verify report date was extracted from text
    assert sample_pdf_model.report_date is not None
    # The date formatting might vary in the actual implementation
    
@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
def test_confidence_score_calculation(mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model):
    """Test calculation of confidence score from biomarker data"""
    # Setup mocks
    mock_extract_text.return_value = "Test report with Glucose: 95 mg/dL"
    
    # Mock biomarker extraction with confidence scores
    mock_extract_biomarkers.return_value = (
        [
            {
                "name": "Glucose",
                "original_name": "Glucose",
                "original_value": "95",
                "original_unit": "mg/dL",
                "value": 95.0,
                "unit": "mg/dL",
                "confidence": 0.9
            },
            {
                "name": "Cholesterol",
                "original_name": "Cholesterol",
                "original_value": "200",
                "original_unit": "mg/dL",
                "value": 200.0,
                "unit": "mg/dL",
                "confidence": 0.7
            }
        ],
        {
            "lab_name": "Test Lab"
        }
    )
    
    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model
    
    # Call the function
    process_pdf_background("/path/to/test.pdf", "test_file_id", mock_db_session)
    
    # Verify confidence score was calculated
    assert sample_pdf_model.parsing_confidence is not None
    assert sample_pdf_model.parsing_confidence == 0.8  # (0.9 + 0.7) / 2 