import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime
import PyPDF2
from io import BytesIO
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

from app.services.pdf_service import (
    extract_text_from_pdf,
    _extract_text_with_ocr,
    process_pdf_background,
    parse_biomarkers_from_text
)
from app.models.pdf_model import PDF

@pytest.fixture
def multipage_pdf_bytes():
    """Create a multi-page PDF file with lab data."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    
    # Page 1: Patient info and glucose
    pdf.drawString(100, 750, "Lab Test Results")
    pdf.drawString(100, 730, "Date: 05/15/2023")
    pdf.drawString(100, 710, "Patient: John Doe")
    pdf.drawString(100, 690, "Lab: LabCorp")
    
    pdf.drawString(100, 650, "Glucose: 95 mg/dL (70-99)")
    pdf.drawString(100, 630, "HbA1c: 5.4 % (4.0-5.6)")
    
    pdf.showPage()  # End page 1
    
    # Page 2: Lipid panel
    pdf.drawString(100, 750, "Lipid Panel")
    pdf.drawString(100, 730, "Date: 05/15/2023")
    pdf.drawString(100, 710, "Patient: John Doe")
    
    pdf.drawString(100, 650, "Total Cholesterol: 185 mg/dL (125-200)")
    pdf.drawString(100, 630, "HDL Cholesterol: 55 mg/dL (>40)")
    pdf.drawString(100, 610, "LDL Cholesterol: 110 mg/dL (<130)")
    pdf.drawString(100, 590, "Triglycerides: 95 mg/dL (<150)")
    
    pdf.showPage()  # End page 2
    
    # Page 3: Vitamin panel
    pdf.drawString(100, 750, "Vitamin Panel")
    pdf.drawString(100, 730, "Date: 05/15/2023")
    pdf.drawString(100, 710, "Patient: John Doe")
    
    pdf.drawString(100, 650, "Vitamin D, 25-OH: 32 ng/mL (30-100)")
    pdf.drawString(100, 630, "Vitamin B12: 450 pg/mL (200-900)")
    pdf.drawString(100, 610, "Folate: 15 ng/mL (>5.9)")
    
    pdf.save()
    buffer.seek(0)
    return buffer.read()

@pytest.fixture
def table_pdf_bytes():
    """Create a PDF with tabular data."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Create table data
    data = [
        ["Test", "Result", "Units", "Reference", "Flag"],
        ["Glucose", "95", "mg/dL", "70-99", ""],
        ["HbA1c", "5.4", "%", "4.0-5.6", ""],
        ["Total Cholesterol", "185", "mg/dL", "125-200", ""],
        ["HDL Cholesterol", "55", "mg/dL", ">40", ""],
        ["LDL Cholesterol", "110", "mg/dL", "<130", ""],
        ["Triglycerides", "95", "mg/dL", "<150", ""],
        ["Vitamin D", "32", "ng/mL", "30-100", ""],
        ["Vitamin B12", "450", "pg/mL", "200-900", ""],
        ["Folate", "15", "ng/mL", ">5.9", ""]
    ]
    
    # Create table
    table = Table(data)
    
    # Add style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(style)
    
    # Build document
    elements = []
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    return buffer.read()

@pytest.fixture
def ocr_simulation_pdf():
    """Create a PDF file that simulates a scanned document requiring OCR."""
    # For testing purposes, we'll create a regular PDF but mock the text extraction
    # to return empty text so that the OCR path is triggered
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    
    # Add text that would be in an image in a real scanned PDF
    pdf.drawString(100, 750, "Lab Test Results")
    pdf.drawString(100, 730, "Date: 05/15/2023")
    pdf.drawString(100, 710, "Patient: John Doe")
    pdf.drawString(100, 690, "Lab: LabCorp")
    
    pdf.drawString(100, 650, "Glucose: 95 mg/dL (70-99)")
    pdf.drawString(100, 630, "HbA1c: 5.4 % (4.0-5.6)")
    
    pdf.save()
    buffer.seek(0)
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(buffer.read())
        pdf_path = f.name
    
    return pdf_path

@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    session = MagicMock()
    
    # Mock query builder
    query_mock = MagicMock()
    session.query.return_value = query_mock
    query_mock.filter.return_value = query_mock
    query_mock.first.return_value = None
    
    return session

@pytest.fixture
def sample_pdf_model():
    """Create a sample PDF model for testing."""
    return PDF(
        id=1,
        file_id="test_file_id",
        filename="test.pdf",
        file_path="/path/to/test.pdf",
        status="pending",
        upload_date=datetime.utcnow()
    )

def test_extract_text_from_multipage_pdf(multipage_pdf_bytes):
    """Test extracting text from a multi-page PDF."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(multipage_pdf_bytes)
        pdf_path = f.name
    
    try:
        # Extract text from the multi-page PDF
        text = extract_text_from_pdf(pdf_path)
        
        # Verify that text from all pages was extracted
        assert "Glucose: 95 mg/dL" in text
        assert "Lipid Panel" in text
        assert "Total Cholesterol: 185 mg/dL" in text
        assert "Vitamin Panel" in text
        assert "Vitamin D, 25-OH: 32 ng/mL" in text
        
        # Verify that we have content from all three pages
        assert text.count("John Doe") == 3
    finally:
        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

def test_extract_text_from_table_pdf(table_pdf_bytes):
    """Test extracting text from a PDF with tabular data."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(table_pdf_bytes)
        pdf_path = f.name
    
    try:
        # Extract text from the PDF with tables
        text = extract_text_from_pdf(pdf_path)
        
        # Verify that the table headers were extracted
        assert "Test" in text
        assert "Result" in text
        assert "Units" in text
        assert "Reference" in text
        
        # Verify that biomarker data was extracted
        assert "Glucose" in text
        assert "95" in text
        assert "mg/dL" in text
        assert "70-99" in text
        
        # Check for other biomarkers
        assert "HbA1c" in text
        assert "Total Cholesterol" in text
        assert "HDL Cholesterol" in text
    finally:
        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

@patch("PyPDF2.PdfReader")
@patch("app.services.pdf_service._extract_text_with_ocr")
def test_extract_text_falls_back_to_ocr(mock_ocr, mock_pdf_reader, ocr_simulation_pdf):
    """Test that text extraction falls back to OCR when PyPDF2 extracts no text."""
    # Setup mock to return empty text from PyPDF2
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    mock_pdf_reader.return_value.pages = [mock_page]
    
    # Setup OCR mock to return test text
    mock_ocr.return_value = "Glucose: 95 mg/dL (70-99)\nHbA1c: 5.4 % (4.0-5.6)"
    
    # Extract text from the PDF
    text = extract_text_from_pdf(ocr_simulation_pdf)
    
    # Verify OCR was called as a fallback
    mock_ocr.assert_called_once_with(ocr_simulation_pdf)
    
    # Verify the OCR-extracted text is returned
    assert "Glucose: 95 mg/dL" in text
    assert "HbA1c: 5.4 %" in text

@patch("pdf2image.convert_from_path")
@patch("pytesseract.image_to_string")
def test_ocr_extracts_text_from_all_pages(mock_image_to_string, mock_convert_from_path):
    """Test that OCR extracts text from all pages of a PDF."""
    # Create mock images for multiple pages
    mock_image1 = MagicMock()
    mock_image2 = MagicMock()
    mock_convert_from_path.return_value = [mock_image1, mock_image2]
    
    # Setup OCR responses for each page
    mock_image_to_string.side_effect = [
        "Glucose: 95 mg/dL (70-99)\nHbA1c: 5.4 % (4.0-5.6)",
        "Total Cholesterol: 185 mg/dL (125-200)\nHDL Cholesterol: 55 mg/dL (>40)"
    ]
    
    # Call the OCR function
    text = _extract_text_with_ocr("dummy_path.pdf")
    
    # Verify image_to_string was called for each page
    assert mock_image_to_string.call_count == 2
    
    # Verify the combined text from all pages
    assert "Glucose: 95 mg/dL" in text
    assert "Total Cholesterol: 185 mg/dL" in text

@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
def test_process_multipage_pdf(mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model, multipage_pdf_bytes):
    """Test processing a multi-page PDF."""
    # Setup text extraction mock
    mock_extract_text.return_value = """
    Lab Test Results
    Date: 05/15/2023
    Patient: John Doe
    Lab: LabCorp
    
    Glucose: 95 mg/dL (70-99)
    HbA1c: 5.4 % (4.0-5.6)
    
    Lipid Panel
    Date: 05/15/2023
    Patient: John Doe
    
    Total Cholesterol: 185 mg/dL (125-200)
    HDL Cholesterol: 55 mg/dL (>40)
    LDL Cholesterol: 110 mg/dL (<130)
    Triglycerides: 95 mg/dL (<150)
    
    Vitamin Panel
    Date: 05/15/2023
    Patient: John Doe
    
    Vitamin D, 25-OH: 32 ng/mL (30-100)
    Vitamin B12: 450 pg/mL (200-900)
    Folate: 15 ng/mL (>5.9)
    """
    
    # Setup biomarker extraction mock
    mock_extract_biomarkers.return_value = (
        [
            {
                "name": "Glucose",
                "original_name": "Glucose",
                "value": 95.0,
                "original_value": 95.0,
                "unit": "mg/dL",
                "original_unit": "mg/dL",
                "reference_range_low": 70.0,
                "reference_range_high": 99.0,
                "category": "Metabolic",
                "is_abnormal": False
            },
            {
                "name": "HbA1c",
                "original_name": "HbA1c",
                "value": 5.4,
                "original_value": 5.4,
                "unit": "%",
                "original_unit": "%",
                "reference_range_low": 4.0,
                "reference_range_high": 5.6,
                "category": "Metabolic",
                "is_abnormal": False
            },
            {
                "name": "Total Cholesterol",
                "original_name": "Total Cholesterol",
                "value": 185.0,
                "original_value": 185.0,
                "unit": "mg/dL",
                "original_unit": "mg/dL",
                "reference_range_low": 125.0,
                "reference_range_high": 200.0,
                "category": "Lipid",
                "is_abnormal": False
            },
            {
                "name": "HDL Cholesterol",
                "original_name": "HDL Cholesterol",
                "value": 55.0,
                "original_value": 55.0,
                "unit": "mg/dL",
                "original_unit": "mg/dL",
                "reference_range_low": 40.0,
                "reference_range_high": None,
                "category": "Lipid",
                "is_abnormal": False
            },
            {
                "name": "LDL Cholesterol",
                "original_name": "LDL Cholesterol",
                "value": 110.0,
                "original_value": 110.0,
                "unit": "mg/dL",
                "original_unit": "mg/dL",
                "reference_range_low": None,
                "reference_range_high": 130.0,
                "category": "Lipid",
                "is_abnormal": False
            },
            {
                "name": "Triglycerides",
                "original_name": "Triglycerides",
                "value": 95.0,
                "original_value": 95.0,
                "unit": "mg/dL",
                "original_unit": "mg/dL",
                "reference_range_low": None,
                "reference_range_high": 150.0,
                "category": "Lipid",
                "is_abnormal": False
            },
            {
                "name": "Vitamin D, 25-OH",
                "original_name": "Vitamin D, 25-OH",
                "value": 32.0,
                "original_value": 32.0,
                "unit": "ng/mL",
                "original_unit": "ng/mL",
                "reference_range_low": 30.0,
                "reference_range_high": 100.0,
                "category": "Vitamin",
                "is_abnormal": False
            },
            {
                "name": "Vitamin B12",
                "original_name": "Vitamin B12",
                "value": 450.0,
                "original_value": 450.0,
                "unit": "pg/mL",
                "original_unit": "pg/mL",
                "reference_range_low": 200.0,
                "reference_range_high": 900.0,
                "category": "Vitamin",
                "is_abnormal": False
            },
            {
                "name": "Folate",
                "original_name": "Folate",
                "value": 15.0,
                "original_value": 15.0,
                "unit": "ng/mL",
                "original_unit": "ng/mL",
                "reference_range_low": 5.9,
                "reference_range_high": None,
                "category": "Vitamin",
                "is_abnormal": False
            }
        ],
        {
            "lab_name": "LabCorp",
            "report_date": "05/15/2023",
            "patient_name": "John Doe"
        }
    )
    
    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model
    
    # Create a temporary file for the PDF path
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(multipage_pdf_bytes)
        pdf_path = f.name
    
    try:
        # Process the PDF
        process_pdf_background(pdf_path, "test_file_id", mock_db_session)
        
        # Verify text extraction was called
        mock_extract_text.assert_called_once_with(pdf_path)
        
        # Verify biomarker extraction was called with the full text
        mock_extract_biomarkers.assert_called_once()
        
        # Verify PDF model was updated correctly
        assert sample_pdf_model.status == "processed"
        assert sample_pdf_model.processed_date is not None
        assert sample_pdf_model.lab_name == "LabCorp"
        assert sample_pdf_model.patient_name == "John Doe"
        
        # Verify biomarkers were added to the database
        # The function should add 9 biomarkers, one for each in the mock response
        assert mock_db_session.add.call_count >= 9
        
        # Verify changes were committed
        mock_db_session.commit.assert_called()
    finally:
        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
def test_process_table_pdf(mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model, table_pdf_bytes):
    """Test processing a PDF with tabular data."""
    # Setup text extraction mock to return tabular text
    mock_extract_text.return_value = """
    Test Result Units Reference Flag
    Glucose 95 mg/dL 70-99 
    HbA1c 5.4 % 4.0-5.6 
    Total Cholesterol 185 mg/dL 125-200 
    HDL Cholesterol 55 mg/dL >40 
    LDL Cholesterol 110 mg/dL <130 
    Triglycerides 95 mg/dL <150 
    Vitamin D 32 ng/mL 30-100 
    Vitamin B12 450 pg/mL 200-900 
    Folate 15 ng/mL >5.9 
    """
    
    # Setup biomarker extraction mock
    mock_extract_biomarkers.return_value = (
        [
            {"name": "Glucose", "original_name": "Glucose", "value": 95.0, "original_value": 95.0, "unit": "mg/dL", "original_unit": "mg/dL", "reference_range_low": 70.0, "reference_range_high": 99.0, "category": "Metabolic"},
            {"name": "HbA1c", "original_name": "HbA1c", "value": 5.4, "original_value": 5.4, "unit": "%", "original_unit": "%", "reference_range_low": 4.0, "reference_range_high": 5.6, "category": "Metabolic"},
            {"name": "Total Cholesterol", "original_name": "Total Cholesterol", "value": 185.0, "original_value": 185.0, "unit": "mg/dL", "original_unit": "mg/dL", "reference_range_low": 125.0, "reference_range_high": 200.0, "category": "Lipid"},
            {"name": "HDL Cholesterol", "original_name": "HDL Cholesterol", "value": 55.0, "original_value": 55.0, "unit": "mg/dL", "original_unit": "mg/dL", "reference_range_low": 40.0, "reference_range_high": None, "category": "Lipid"},
            {"name": "LDL Cholesterol", "original_name": "LDL Cholesterol", "value": 110.0, "original_value": 110.0, "unit": "mg/dL", "original_unit": "mg/dL", "reference_range_low": None, "reference_range_high": 130.0, "category": "Lipid"},
            {"name": "Triglycerides", "original_name": "Triglycerides", "value": 95.0, "original_value": 95.0, "unit": "mg/dL", "original_unit": "mg/dL", "reference_range_low": None, "reference_range_high": 150.0, "category": "Lipid"},
            {"name": "Vitamin D", "original_name": "Vitamin D", "value": 32.0, "original_value": 32.0, "unit": "ng/mL", "original_unit": "ng/mL", "reference_range_low": 30.0, "reference_range_high": 100.0, "category": "Vitamin"},
            {"name": "Vitamin B12", "original_name": "Vitamin B12", "value": 450.0, "original_value": 450.0, "unit": "pg/mL", "original_unit": "pg/mL", "reference_range_low": 200.0, "reference_range_high": 900.0, "category": "Vitamin"},
            {"name": "Folate", "original_name": "Folate", "value": 15.0, "original_value": 15.0, "unit": "ng/mL", "original_unit": "ng/mL", "reference_range_low": 5.9, "reference_range_high": None, "category": "Vitamin"}
        ],
        {
            "lab_name": "Unknown Lab",
            "report_date": "Unknown"
        }
    )
    
    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model
    
    # Create a temporary file for the PDF path
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(table_pdf_bytes)
        pdf_path = f.name
    
    try:
        # Process the PDF
        process_pdf_background(pdf_path, "test_file_id", mock_db_session)
        
        # Verify text extraction was called
        mock_extract_text.assert_called_once_with(pdf_path)
        
        # Verify biomarker extraction was called with the tabular text
        mock_extract_biomarkers.assert_called_once()
        args, _ = mock_extract_biomarkers.call_args
        extracted_text = args[0]
        assert "Test Result Units Reference Flag" in extracted_text
        
        # Verify PDF model was updated correctly
        assert sample_pdf_model.status == "processed"
        assert sample_pdf_model.processed_date is not None
        
        # Verify biomarkers were added to the database
        assert mock_db_session.add.call_count >= 9
        
        # Verify changes were committed
        mock_db_session.commit.assert_called()
    finally:
        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

@patch("app.services.pdf_service.extract_text_from_pdf")
@patch("app.services.pdf_service.extract_biomarkers_with_claude")
def test_handle_very_long_pdf_text(mock_extract_biomarkers, mock_extract_text, mock_db_session, sample_pdf_model):
    """Test handling of very long PDF text."""
    # Create a very long text that might exceed API limits
    very_long_text = "Test line " * 10000  # Approximately 100,000 characters
    
    # Setup text extraction mock
    mock_extract_text.return_value = very_long_text
    
    # Setup biomarker extraction mock
    mock_extract_biomarkers.return_value = ([], {"lab_name": "Unknown"})
    
    # Setup mock PDF query
    pdf_query = mock_db_session.query.return_value.filter.return_value
    pdf_query.first.return_value = sample_pdf_model
    
    # Process the PDF
    process_pdf_background("/path/to/test.pdf", "test_file_id", mock_db_session)
    
    # Verify biomarker extraction was called with the long text
    mock_extract_biomarkers.assert_called_once()
    args, _ = mock_extract_biomarkers.call_args
    assert len(args[0]) == len(very_long_text)
    
    # Verify PDF model was updated correctly despite the long text
    assert sample_pdf_model.status == "processed"
    assert sample_pdf_model.processed_date is not None
    
    # Verify changes were committed
    mock_db_session.commit.assert_called()

@patch("app.services.biomarker_parser.parse_biomarkers_from_text")
def test_parse_biomarkers_from_tabular_text(mock_parser):
    """Test parsing biomarkers from tabular text format."""
    tabular_text = """
    Test Result Units Reference Flag
    Glucose 95 mg/dL 70-99 
    HbA1c 5.4 % 4.0-5.6 
    Total Cholesterol 185 mg/dL 125-200 
    """
    
    # Setup mock
    mock_parser.return_value = [
        {"name": "Glucose", "value": 95.0, "unit": "mg/dL", "reference_range": "70-99"},
        {"name": "HbA1c", "value": 5.4, "unit": "%", "reference_range": "4.0-5.6"},
        {"name": "Total Cholesterol", "value": 185.0, "unit": "mg/dL", "reference_range": "125-200"}
    ]
    
    # Call the function
    result = parse_biomarkers_from_text(tabular_text)
    
    # Verify the result
    assert len(result) == 3
    
    # Verify the mock was called with the tabular text
    mock_parser.assert_called_once_with(tabular_text) 