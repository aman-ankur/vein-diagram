import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from app.services.pdf_service import extract_text_from_pdf, parse_biomarkers_from_text, _extract_text_with_ocr

def test_extract_text_from_pdf_invalid_file():
    """Test that an exception is raised when trying to extract text from an invalid file."""
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        # Write some non-PDF content to the file
        temp_file.write(b'This is not a valid PDF file')
        temp_file.flush()
        
        # Attempt to extract text from the invalid file
        with pytest.raises(Exception):
            extract_text_from_pdf(temp_file.name)

def test_extract_text_from_pdf_mock():
    """Test extracting text from a PDF using mocks."""
    # Create a simple PDF with mock content
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        # Write minimal PDF content
        temp_file.write(b'%PDF-1.7\nMock PDF content')
        temp_file.flush()
        
        # Mock the PdfReader to return a predefined text
        with patch('PyPDF2.PdfReader') as mock_reader:
            # Set up the mock to return some text
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Test biomarker data: Glucose 85 mg/dL"
            mock_reader.return_value.pages = [mock_page]
            
            # Extract text from the mocked PDF
            result = extract_text_from_pdf(temp_file.name)
            
            # Check the result
            assert "Test biomarker data" in result
            assert "Glucose 85 mg/dL" in result

def test_ocr_extraction_mock():
    """Test OCR extraction with mocked pdf2image and pytesseract."""
    with patch('pdf2image.convert_from_path') as mock_convert, \
         patch('pytesseract.image_to_string') as mock_ocr:
        
        # Set up mocks
        mock_image = MagicMock()
        mock_convert.return_value = [mock_image, mock_image]  # Two pages
        mock_ocr.return_value = "Sample OCR text with Glucose: 90 mg/dL"
        
        # Call the OCR function with any path
        result = _extract_text_with_ocr("/path/to/mock.pdf")
        
        # Check the result contains the OCR text
        assert "Sample OCR text" in result
        assert "Page 1" in result  # Page numbering
        assert "Page 2" in result  # Page numbering
        assert "Glucose" in result

def test_parse_biomarkers_from_text():
    """Test that biomarkers are parsed correctly from text."""
    # Sample text that might be extracted from a PDF
    sample_text = """
    Laboratory Results
    
    Patient: John Doe
    Date: 2023-01-15
    
    Test                Result      Reference Range
    ---------------------------------------------
    Glucose             85 mg/dL    70-99
    Cholesterol         180 mg/dL   <200
    """
    
    # Parse biomarkers from the sample text
    biomarkers = parse_biomarkers_from_text(sample_text)
    
    # Check that at least one biomarker was parsed
    assert len(biomarkers) > 0
    
    # Check that the first biomarker has the expected structure
    assert "name" in biomarkers[0]
    assert "value" in biomarkers[0]
    assert "unit" in biomarkers[0] 