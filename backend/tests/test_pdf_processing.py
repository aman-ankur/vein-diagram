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
    test_db.refresh(pdf_record)
    
    # Mock extract_text_from_pdf
    with patch('app.services.pdf_service.extract_text_from_pdf') as mock_extract, \
         patch('app.services.pdf_service.parse_biomarkers_from_text') as mock_parse, \
         patch('os.path.exists', return_value=True):
        
        # Set up the mocks
        mock_extract.return_value = "Test laboratory report for John Doe\nDate: 01/15/2023\nGlucose: 85 mg/dL"
        mock_parse.return_value = [{"name": "Glucose", "value": 85.0, "unit": "mg/dL"}]
        
        # Call the function with the new signature
        process_pdf_background(pdf_record.id, test_db)
        
        # Get the updated record
        updated_record = test_db.query(PDFModel).filter(PDFModel.file_id == "test-process-123").first()
        
        # Check the record was updated correctly
        assert updated_record.status == "complete"
        assert updated_record.processed_date is not None
        
        # Check biomarkers were created
        from app.models.biomarker_model import Biomarker
        biomarkers = test_db.query(Biomarker).filter(Biomarker.pdf_id == updated_record.id).all()
        assert len(biomarkers) == 1
        assert biomarkers[0].name == "Glucose"
        assert biomarkers[0].value == 85.0
        assert biomarkers[0].unit == "mg/dL"


def test_process_pdf_background_error_handling(test_db):
    """Test error handling in the PDF processing function."""
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
    test_db.refresh(pdf_record)
    
    # Mock extract_text_from_pdf to raise an exception
    with patch('app.services.pdf_service.extract_text_from_pdf') as mock_extract, \
         patch('os.path.exists', return_value=True):
        
        mock_extract.side_effect = Exception("Test error")
        
        # Call the function
        process_pdf_background(pdf_record.id, test_db)
        
        # Get the updated record
        updated_record = test_db.query(PDFModel).filter(PDFModel.file_id == "test-error-123").first()
        
        # Check error handling worked correctly
        assert updated_record.status == "error"
        assert "Test error" in updated_record.error_message 