import pytest
import os
import tempfile
from app.services.pdf_service import extract_text_from_pdf, parse_biomarkers_from_text

def test_extract_text_from_pdf_invalid_file():
    """Test that an exception is raised when trying to extract text from an invalid file."""
    with tempfile.NamedTemporaryFile(suffix='.pdf') as temp_file:
        # Write some non-PDF content to the file
        temp_file.write(b'This is not a valid PDF file')
        temp_file.flush()
        
        # Attempt to extract text from the invalid file
        with pytest.raises(Exception):
            extract_text_from_pdf(temp_file.name)

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