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
    pages_text_dict = extract_text_from_pdf(sample_pdf_file)

    # Verify that a dictionary was returned
    assert isinstance(pages_text_dict, dict)
    assert 0 in pages_text_dict # Check if page 0 exists

    # Verify that some text was extracted for page 0
    text_page_0 = pages_text_dict[0]
    assert text_page_0 is not None
    assert len(text_page_0) > 0

    # Check for specific content (might vary based on PDF library version)
    assert "Glucose" in text_page_0 or "glucose" in text_page_0 or "95" in text_page_0 or "mg/dL" in text_page_0

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
    pages_text_dict = _extract_text_with_ocr("dummy_path.pdf")

    # Verify the result is a dictionary and contains expected text for page 0
    assert isinstance(pages_text_dict, dict)
    assert 0 in pages_text_dict
    assert "Glucose: 95 mg/dL" in pages_text_dict[0]

    # Verify the mocks were called
    mock_convert_from_path.assert_called_once_with("dummy_path.pdf", dpi=300)
    mock_image_to_string.assert_called_once_with(mock_image)

@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
@patch("app.services.metadata_parser.extract_metadata_with_claude") # Mock metadata parser
def test_process_pdf_background_success(mock_metadata_parser, mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model):
    """Test successful PDF processing in the background"""
    # Setup mocks
    mock_extract_text.return_value = {0: "Glucose: 95 mg/dL"}
    mock_metadata_parser.return_value = { # Mock metadata response
        "lab_name": "Test Lab",
        "report_date": "01/15/2023"
    }

    # Mock biomarker extraction
    mock_extract_biomarkers.return_value = ( # Returns tuple (biomarkers, metadata_ignored)
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
                "is_abnormal": False,
                "confidence": 0.95 # Added confidence
            }
        ],
        {} # Metadata from biomarker call is ignored now
    )

    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model

    # Call the function
    process_pdf_background(sample_pdf_model.id, mock_db_session)

    # Verify text extraction was called
    mock_extract_text.assert_called_once_with(sample_pdf_model.file_path)

    # Verify metadata extraction was called (with combined text for now)
    mock_metadata_parser.assert_called_once_with("Glucose: 95 mg/dL", sample_pdf_model.filename)

    # Verify biomarker extraction was called (with combined text for now)
    mock_extract_biomarkers.assert_called_once_with("Glucose: 95 mg/dL", sample_pdf_model.filename)

    # Verify database operations
    assert sample_pdf_model.status == "processed"
    assert sample_pdf_model.processed_date is not None
    assert sample_pdf_model.lab_name == "Test Lab" # From mock_metadata_parser
    assert sample_pdf_model.parsing_confidence == 0.95 # Check confidence calculation

    # Verify that a biomarker was added to the database
    mock_db_session.add.assert_called()
    added_biomarker = mock_db_session.add.call_args[0][0]
    assert isinstance(added_biomarker, Biomarker)
    assert added_biomarker.name == "Glucose"

    # Verify commit was called multiple times (after status, text, metadata, biomarkers)
    assert mock_db_session.commit.call_count >= 4

@patch("app.services.pdf_service.extract_text_from_pdf")
def test_process_pdf_background_error(mock_extract_text, mock_db_session, sample_pdf_model):
    """Test error handling during PDF processing"""
    # Setup mock to raise an exception during text extraction
    mock_extract_text.side_effect = Exception("Text extraction failed")

    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model

    # Call the function
    process_pdf_background(sample_pdf_model.id, mock_db_session)

    # Verify status is set to error
    assert sample_pdf_model.status == "error"
    assert sample_pdf_model.error_message == "Text extraction failed"

    # Verify commit was called (at least for status updates)
    mock_db_session.commit.assert_called()
    # Verify rollback was called
    mock_db_session.rollback.assert_called_once()

@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
@patch("app.services.metadata_parser.extract_metadata_with_claude") # Mock metadata parser
def test_process_pdf_background_with_metadata(mock_metadata_parser, mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model):
    """Test PDF processing with metadata extraction"""
    # Setup mocks
    mock_extract_text.return_value = {
        0: "Lab: LabCorp\nDate: 01/15/2023\nPatient: John Doe",
        1: "Glucose: 95 mg/dL"
    }
    # Mock metadata response
    mock_metadata_parser.return_value = {
        "lab_name": "LabCorp",
        "report_date": "01/15/2023",
        "patient_name": "John Doe",
        "patient_age": "30 years",
        "patient_gender": "Male",
        "patient_id": "P123"
        # "custom_field": "custom_value" # Custom fields not handled by current logic
    }

    # Mock biomarker extraction (metadata part ignored)
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
                "is_abnormal": False,
                "confidence": 0.9
            }
        ],
        {} # Metadata ignored
    )

    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model

    # Call the function
    process_pdf_background(sample_pdf_model.id, mock_db_session)

    # Verify standard fields were updated from metadata parser
    assert sample_pdf_model.lab_name == "LabCorp"
    assert sample_pdf_model.patient_name == "John Doe"
    assert sample_pdf_model.patient_age == 30
    assert sample_pdf_model.patient_gender == "Male"
    assert sample_pdf_model.patient_id == "P123"
    assert sample_pdf_model.report_date == datetime(2023, 1, 15) # Check date parsing

    # Verify biomarker extraction was called (with combined text for now)
    combined_text = "Lab: LabCorp\nDate: 01/15/2023\nPatient: John Doe\n--- Page Break ---\nGlucose: 95 mg/dL"
    mock_extract_biomarkers.assert_called_once_with(combined_text, sample_pdf_model.filename)

    # Verify status
    assert sample_pdf_model.status == "processed"

@patch("app.services.biomarker_parser.extract_biomarkers_with_claude")
@patch("app.services.biomarker_parser.parse_biomarkers_from_text")
def test_parse_biomarkers_from_text_wrapper_claude_success(mock_fallback_parser, mock_claude_parser):
    """Test the parse_biomarkers_from_text wrapper function when Claude succeeds"""
    # Setup mock for Claude
    mock_claude_parser.return_value = (
        [
            {
                "name": "Glucose",
                "value": 95.0,
                "unit": "mg/dL",
                "confidence": 0.9
            }
        ],
        {} # Metadata ignored
    )

    # Call the function (which internally calls the Claude parser)
    biomarkers, confidence = parse_biomarkers_from_text("Glucose: 95 mg/dL", pdf_id=1)

    # Verify the result came from Claude mock
    assert len(biomarkers) == 1
    assert biomarkers[0]["name"] == "Glucose"
    assert confidence == 0.9

    # Verify Claude mock was called and fallback was not
    mock_claude_parser.assert_called_once_with("Glucose: 95 mg/dL", "pdf_1.pdf")
    mock_fallback_parser.assert_not_called()

@patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}) # Ensure API key is not set
@patch("app.services.biomarker_parser.parse_biomarkers_from_text")
def test_parse_biomarkers_from_text_wrapper_no_api_key(mock_fallback_parser):
    """Test the parse_biomarkers_from_text wrapper when Claude API key is missing"""
    # Setup mock for fallback parser
    mock_fallback_parser.return_value = [
        {
            "name": "Glucose",
            "value": 95.0,
            "unit": "mg/dL",
            "reference_range": "70-99",
            "category": "Metabolic"
        }
    ]

    # Call the function
    biomarkers, confidence = parse_biomarkers_from_text("Glucose: 95 mg/dL", pdf_id=1)

    # Verify the result came from fallback mock
    assert len(biomarkers) == 1
    assert biomarkers[0]["name"] == "Glucose"
    assert confidence == 0.5 # Default confidence for fallback

    # Verify the fallback mock was called
    mock_fallback_parser.assert_called_once_with("Glucose: 95 mg/dL")


@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
@patch("app.services.metadata_parser.extract_metadata_with_claude") # Mock metadata parser
def test_extract_report_date_parsing(mock_metadata_parser, mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model):
    """Test parsing of report date from metadata"""
    # Setup mocks
    mock_extract_text.return_value = {0: "Test report from 01/15/2023 with Glucose: 95 mg/dL"}
    mock_metadata_parser.return_value = { # Metadata provides the date
        "lab_name": "Test Lab",
        "report_date": "Jan 15, 2023" # Different format
    }

    # Mock biomarker extraction (metadata ignored)
    mock_extract_biomarkers.return_value = (
        [
            {
                "name": "Glucose",
                "original_name": "Glucose",
                "original_value": "95",
                "original_unit": "mg/dL",
                "value": 95.0,
                "unit": "mg/dL",
                "category": "Metabolic",
                "confidence": 0.9
            }
        ],
        {} # Metadata ignored
    )

    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model

    # Call the function
    process_pdf_background(sample_pdf_model.id, mock_db_session)

    # Verify report date was parsed correctly
    assert sample_pdf_model.report_date == datetime(2023, 1, 15)
    assert sample_pdf_model.status == "processed"

@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
@patch("app.services.metadata_parser.extract_metadata_with_claude") # Mock metadata parser
def test_confidence_score_calculation(mock_metadata_parser, mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model):
    """Test calculation of confidence score from biomarker data"""
    # Setup mocks
    mock_extract_text.return_value = {0: "Test report with Glucose: 95 mg/dL"}
    mock_metadata_parser.return_value = {"lab_name": "Test Lab"} # Basic metadata

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
        {} # Metadata ignored
    )

    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model

    # Call the function
    process_pdf_background(sample_pdf_model.id, mock_db_session)

    # Verify confidence score was calculated
    assert sample_pdf_model.parsing_confidence is not None
    assert sample_pdf_model.parsing_confidence == 0.8  # (0.9 + 0.7) / 2
    assert sample_pdf_model.status == "processed"
