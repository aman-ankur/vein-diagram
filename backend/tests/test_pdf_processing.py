import pytest
from unittest.mock import patch, MagicMock
import os
import io
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.pdf_service import process_pdf_background
from app.models.pdf_model import PDF as PDFModel

def test_process_pdf_background(test_db):
    """Test the PDF background processing function."""
    # Create a test PDF record
    pdf_record = PDFModel(
        file_id="test-process-123",
        filename="test_process.pdf",
        upload_date=datetime.utcnow(),
        status="pending",
        file_path="/tmp/test_process.pdf"
    )
    
    test_db.add(pdf_record)
    test_db.commit()
    
    # Mock extract_text_from_pdf
    with patch('app.services.pdf_service.extract_text_from_pdf') as mock_extract, \
         patch('app.services.pdf_service.parse_biomarkers_from_text') as mock_parse, \
         patch('os.path.exists', return_value=True):
        
        # Set up the mocks
        mock_extract.return_value = "Test laboratory report for John Doe\nDate: 01/15/2023\nGlucose: 85 mg/dL"
        mock_parse.return_value = [{"name": "Glucose", "value": 85.0, "unit": "mg/dL"}]
        
        # Call the function
        process_pdf_background("/tmp/test_process.pdf", "test-process-123", test_db)
        
        # Get the updated record
        updated_record = test_db.query(PDFModel).filter(PDFModel.file_id == "test-process-123").first()
        
        # Check the record was updated correctly
        assert updated_record.status == "processed"
        assert updated_record.extracted_text is not None
        assert "Test laboratory report" in updated_record.extracted_text
        assert updated_record.processed_date is not None
        assert updated_record.report_date is not None
        assert updated_record.report_date.year == 2023
        assert updated_record.report_date.month == 1
        assert updated_record.report_date.day == 15

def test_process_pdf_background_error_handling(test_db):
    """Test error handling in the PDF background processing function."""
    # Create a test PDF record
    pdf_record = PDFModel(
        file_id="test-error-123",
        filename="test_error.pdf",
        upload_date=datetime.utcnow(),
        status="pending",
        file_path="/tmp/test_error.pdf"
    )
    
    test_db.add(pdf_record)
    test_db.commit()
    
    # Mock extract_text_from_pdf to raise an exception
    with patch('app.services.pdf_service.extract_text_from_pdf') as mock_extract:
        mock_extract.side_effect = Exception("Test extraction error")
        
        # Call the function
        process_pdf_background("/tmp/test_error.pdf", "test-error-123", test_db)
        
        # Get the updated record
        updated_record = test_db.query(PDFModel).filter(PDFModel.file_id == "test-error-123").first()
        
        # Check the record has error status
        assert updated_record.status == "error"
        assert "Test extraction error" in updated_record.error_message 