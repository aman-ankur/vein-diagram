import os
from typing import List, Dict, Any, Optional
import PyPDF2
from PIL import Image
import pytesseract
import logging
import tempfile
import pdf2image
import io
from datetime import datetime
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using PyPDF2 or Tesseract OCR for image-based PDFs.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    logger.info(f"Extracting text from PDF: {file_path}")
    
    try:
        # Open the PDF file
        with open(file_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Initialize an empty string to store the text
            text = ""
            
            # Loop through each page and extract text
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text if page_text else ""
            
            # If no text was extracted, the PDF might be image-based
            if not text.strip():
                logger.info("No text extracted, PDF might be image-based. Attempting OCR...")
                text = _extract_text_with_ocr(file_path)
            
            return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise

def _extract_text_with_ocr(file_path: str) -> str:
    """
    Extract text from an image-based PDF using Tesseract OCR.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        logger.info(f"Extracting text from image-based PDF using OCR: {file_path}")
        
        # Convert PDF to images
        pages = pdf2image.convert_from_path(file_path, dpi=300)
        
        # Extract text from each page
        full_text = ""
        for i, page in enumerate(pages):
            logger.info(f"Processing page {i+1} of {len(pages)}")
            
            # Use pytesseract to get text from the image
            page_text = pytesseract.image_to_string(page)
            full_text += f"\n--- Page {i+1} ---\n{page_text}\n"
        
        if not full_text.strip():
            logger.warning("OCR could not extract any text from the PDF")
            return "OCR processing did not extract any text. The PDF might be encrypted or contain only images without text."
        
        return full_text
    except Exception as e:
        logger.error(f"Error in OCR processing: {str(e)}")
        return f"Error in OCR processing: {str(e)}"

def process_pdf_background(file_path: str, file_id: str, db: Session) -> None:
    """
    Process PDF file in background.
    
    Args:
        file_path: Path to the PDF file
        file_id: Unique ID of the file
        db: Database session
    """
    try:
        # Get the PDF from the database
        from app.models.pdf_model import PDF as PDFModel
        
        pdf = db.query(PDFModel).filter(PDFModel.file_id == file_id).first()
        if not pdf:
            logger.error(f"PDF with ID {file_id} not found in database")
            return
        
        # Update status to processing
        pdf.status = "processing"
        db.commit()
        
        # Extract text from the PDF
        extracted_text = extract_text_from_pdf(file_path)
        
        # Extract biomarkers from the text (this will be enhanced in chunk #4)
        biomarkers = parse_biomarkers_from_text(extracted_text)
        
        # Extract report date if possible (simplified approach)
        try:
            # Try to find a date in the format MM/DD/YYYY or similar
            import re
            date_matches = re.findall(r'(0[1-9]|1[0-2])[/\-](0[1-9]|[12][0-9]|3[01])[/\-](20\d{2})', extracted_text)
            if date_matches:
                # Use the first date found (simplified)
                month, day, year = date_matches[0]
                report_date = datetime(int(year), int(month), int(day))
                pdf.report_date = report_date
        except Exception as date_error:
            logger.warning(f"Could not extract report date: {str(date_error)}")
        
        # Update the PDF record
        pdf.extracted_text = extracted_text
        pdf.status = "processed"
        pdf.processed_date = datetime.utcnow()
        
        # Save changes
        db.commit()
        
        logger.info(f"Successfully processed PDF: {file_id}")
    except Exception as e:
        logger.error(f"Error processing PDF {file_id}: {str(e)}")
        
        # Update the PDF record with error status
        try:
            pdf = db.query(PDFModel).filter(PDFModel.file_id == file_id).first()
            if pdf:
                pdf.status = "error"
                pdf.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating PDF record: {str(db_error)}")

def parse_biomarkers_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse biomarker data from extracted text.
    This is a placeholder for the actual implementation that will use Claude API.
    
    Args:
        text: Extracted text from the PDF
        
    Returns:
        List[Dict[str, Any]]: List of biomarker data
    """
    # This is a placeholder for the actual implementation
    # In the future, this will use Claude API to parse the text
    logger.info("Parsing biomarkers from text (placeholder)")
    
    # Return a placeholder response
    return [
        {
            "name": "Glucose",
            "value": 85.0,
            "unit": "mg/dL",
            "reference_range": "70-99",
            "category": "Metabolic"
        }
    ] 