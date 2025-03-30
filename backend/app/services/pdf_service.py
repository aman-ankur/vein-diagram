import os
from typing import List, Dict, Any, Optional, Tuple
import PyPDF2
from PIL import Image
import pytesseract
import logging
import tempfile
import pdf2image
import io
import json
from datetime import datetime
from sqlalchemy.orm import Session
import pdfplumber
import pandas as pd
import re
import dateutil.parser

from app.services.biomarker_parser import (
    extract_biomarkers_with_claude,
    parse_biomarkers_from_text,
    standardize_unit,
    _preprocess_text_for_claude
)
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF  # Import the PDF model class
from app.db.database import SessionLocal  # Import SessionLocal for error handling

# Configure logging with more detailed format
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up a file handler to also log to a file
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'pdf_service.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
logger.addHandler(file_handler)

# Maximum number of pages to extract from PDFs
MAX_PAGES = 5

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using PyPDF2 or Tesseract OCR for image-based PDFs.
    Limited to the first MAX_PAGES pages.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    logger.info(f"[PDF_TEXT_EXTRACTION_START] Extracting text from PDF: {file_path}")
    start_time = datetime.utcnow()
    
    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Open the PDF file
        with open(file_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Log PDF metadata
            total_pages = len(pdf_reader.pages)
            logger.debug(f"[PDF_METADATA] Number of pages: {total_pages}")
            if pdf_reader.metadata:
                logger.debug(f"[PDF_METADATA] Author: {pdf_reader.metadata.get('/Author', 'None')}")
                logger.debug(f"[PDF_METADATA] Creation date: {pdf_reader.metadata.get('/CreationDate', 'None')}")
            
            # Initialize an empty string to store the text
            text = ""
            
            # Determine how many pages to extract (limited to MAX_PAGES)
            pages_to_extract = min(total_pages, MAX_PAGES)
            logger.info(f"[PAGE_LIMIT] Extracting only the first {pages_to_extract} pages of {total_pages} total pages")
            
            # Loop through each page and extract text (up to MAX_PAGES)
            for page_num in range(pages_to_extract):
                page = pdf_reader.pages[page_num]
                page_text = page.extract_text()
                text += page_text if page_text else ""
                logger.debug(f"[PAGE_EXTRACTION] Page {page_num+1}: Extracted {len(page_text) if page_text else 0} characters")
            
            # Log extracted text for debugging
            debug_text_path = os.path.join(log_dir, f"pdf_extracted_text_{os.path.basename(file_path)}.txt")
            try:
                with open(debug_text_path, "w") as f:
                    f.write(text if text.strip() else "No text extracted with PyPDF2")
                logger.debug(f"[EXTRACTED_TEXT_SAVED] PDF text saved to {debug_text_path}")
            except Exception as e:
                logger.error(f"[TEXT_SAVE_ERROR] Could not save extracted text: {str(e)}")
            
            # If no text was extracted, the PDF might be image-based
            if not text.strip():
                logger.info("[OCR_FALLBACK] No text extracted with PyPDF2, PDF might be image-based. Attempting OCR...")
                text = _extract_text_with_ocr(file_path)
                
                # Save OCR text for debugging
                debug_ocr_path = os.path.join(log_dir, f"pdf_ocr_text_{os.path.basename(file_path)}.txt")
                try:
                    with open(debug_ocr_path, "w") as f:
                        f.write(text)
                    logger.debug(f"[OCR_TEXT_SAVED] OCR text saved to {debug_ocr_path}")
                except Exception as e:
                    logger.error(f"[OCR_TEXT_SAVE_ERROR] Could not save OCR text: {str(e)}")
            
            extraction_time = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"[PDF_TEXT_EXTRACTION_COMPLETE] Extracted {len(text)} characters in {extraction_time:.2f} seconds")
            
            return text
    except Exception as e:
        logger.error(f"[PDF_EXTRACTION_ERROR] Error extracting text from PDF: {str(e)}")
        raise

def _extract_text_with_ocr(file_path: str) -> str:
    """
    Extract text from an image-based PDF using Tesseract OCR.
    Limited to the first MAX_PAGES pages.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        str: Extracted text from the PDF
    """
    try:
        logger.info(f"[OCR_START] Extracting text from image-based PDF using OCR: {file_path}")
        ocr_start_time = datetime.utcnow()
        
        # Create debug directory for OCR images
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        debug_img_dir = os.path.join(log_dir, f"ocr_images_{os.path.basename(file_path).replace('.pdf', '')}")
        os.makedirs(debug_img_dir, exist_ok=True)
        
        # Check if Tesseract is installed
        try:
            tesseract_path = os.environ.get('TESSERACT_PATH', '/usr/local/bin/tesseract')
            if not os.path.exists(tesseract_path):
                logger.error(f"[OCR_ERROR] Tesseract not found at path: {tesseract_path}")
                return "OCR processing failed: Tesseract not found."
            
            # Set Tesseract path
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.debug(f"[OCR_CONFIG] Using Tesseract at: {tesseract_path}")
            
            # Get Tesseract version for debugging
            try:
                import subprocess
                tesseract_version = subprocess.check_output([tesseract_path, '--version']).decode('utf-8').strip()
                logger.debug(f"[OCR_CONFIG] Tesseract version: {tesseract_version}")
            except Exception as e:
                logger.warning(f"[OCR_CONFIG] Could not get Tesseract version: {str(e)}")
        except Exception as e:
            logger.error(f"[OCR_CONFIG_ERROR] Error configuring Tesseract: {str(e)}")
        
        # Convert PDF to images
        logger.debug("[OCR_PROCESS] Converting PDF to images")
        # Limit to first MAX_PAGES pages
        pages = pdf2image.convert_from_path(file_path, dpi=300, first_page=1, last_page=MAX_PAGES)
        total_pages_converted = len(pages)
        logger.debug(f"[OCR_PROCESS] Converted {total_pages_converted} pages to images (limited to first {MAX_PAGES} pages)")
        
        # Extract text from each page
        full_text = ""
        for i, page in enumerate(pages):
            logger.debug(f"[OCR_PAGE_PROCESSING] Processing page {i+1} of {total_pages_converted}")
            page_start_time = datetime.utcnow()
            
            # Save the page image for debugging
            img_path = os.path.join(debug_img_dir, f"page_{i+1}.png")
            try:
                page.save(img_path)
                logger.debug(f"[OCR_IMAGE_SAVED] Saved page {i+1} image to {img_path}")
            except Exception as e:
                logger.error(f"[OCR_IMAGE_SAVE_ERROR] Could not save page image: {str(e)}")
            
            # Use pytesseract to get text from the image
            try:
                # Try different OCR configurations for better results
                page_text = pytesseract.image_to_string(page, config='--psm 6')  # Assume a single uniform block of text
                
                # If no text was extracted, try another mode
                if not page_text.strip():
                    logger.debug(f"[OCR_RETRY] No text found with default settings, trying alternative OCR mode")
                    page_text = pytesseract.image_to_string(page, config='--psm 3')  # Fully automatic page segmentation
                
                page_time = (datetime.utcnow() - page_start_time).total_seconds()
                
                # Save individual page OCR results
                page_text_path = os.path.join(debug_img_dir, f"page_{i+1}_text.txt")
                try:
                    with open(page_text_path, "w") as f:
                        f.write(page_text)
                    logger.debug(f"[OCR_PAGE_TEXT_SAVED] OCR text for page {i+1} saved to {page_text_path}")
                except Exception as e:
                    logger.error(f"[OCR_PAGE_TEXT_SAVE_ERROR] Could not save page OCR text: {str(e)}")
                
                logger.debug(f"[OCR_PAGE_COMPLETE] Page {i+1} processed in {page_time:.2f} seconds, extracted {len(page_text)} characters")
                full_text += f"\n--- Page {i+1} ---\n{page_text}\n"
            except Exception as e:
                logger.error(f"[OCR_PAGE_ERROR] Error performing OCR on page {i+1}: {str(e)}")
                full_text += f"\n--- Page {i+1} (OCR ERROR) ---\n"
        
        if not full_text.strip():
            logger.warning("[OCR_NO_TEXT] OCR could not extract any text from the PDF")
            return "OCR processing did not extract any text. The PDF might be encrypted or contain only images without text."
            
        ocr_time = (datetime.utcnow() - ocr_start_time).total_seconds()
        logger.info(f"[OCR_COMPLETE] OCR processing completed in {ocr_time:.2f} seconds")
        return full_text
        
    except Exception as e:
        logger.error(f"[OCR_ERROR] Error during OCR processing: {str(e)}")
        return f"OCR processing failed: {str(e)}"

def process_pdf_background(pdf_id: int, db_session=None):
    """
    Process PDF in the background.
    
    Args:
        pdf_id: PDF ID from database
        db_session: SQLAlchemy session
    """
    # Create new session if not provided
    if db_session is None:
        db_session = SessionLocal()
    
    # Get PDF from database
    try:
        pdf = db_session.query(PDF).filter(PDF.id == pdf_id).first()
        if not pdf:
            logger.error(f"PDF {pdf_id} not found in database")
            return
        
        # Update status
        logger.info(f"Starting to process PDF {pdf_id}")
        pdf.status = "processing"
        db_session.commit()
        
        # Extract text
        logger.info(f"Extracting text from PDF {pdf_id}")
        text = extract_text_from_pdf(pdf.file_path)
        
        # Save extracted text
        pdf.extracted_text = text
        db_session.commit()
        
        # Parse metadata using Claude API
        logger.info(f"Parsing metadata from text for PDF {pdf_id}")
        from app.services.metadata_parser import extract_metadata_with_claude
        metadata = extract_metadata_with_claude(text, pdf.filename)
        
        # Update PDF with extracted metadata
        if metadata:
            logger.info(f"Extracted metadata for PDF {pdf_id}: {metadata}")
            # First, handle the report_date separately to ensure proper conversion
            if metadata.get("report_date"):
                # Convert string date to datetime object
                report_date_str = metadata.get("report_date")
                try:
                    pdf.report_date = dateutil.parser.parse(report_date_str)
                    logger.info(f"Converted report date from '{report_date_str}' to {pdf.report_date}")
                    db_session.commit()  # Commit report_date change immediately
                except Exception as e:
                    logger.error(f"Failed to parse report date '{report_date_str}': {str(e)}")
            
            # Handle other metadata fields that don't require type conversion
            update_dict = {}
            if metadata.get("patient_name"):
                update_dict["patient_name"] = metadata.get("patient_name")
            if metadata.get("patient_gender"):
                update_dict["patient_gender"] = metadata.get("patient_gender")
            if metadata.get("patient_id"):
                update_dict["patient_id"] = metadata.get("patient_id")
            if metadata.get("lab_name"):
                update_dict["lab_name"] = metadata.get("lab_name")
            
            # Apply updates if there are any
            if update_dict:
                for key, value in update_dict.items():
                    setattr(pdf, key, value)
                logger.info(f"Updated PDF with metadata: {update_dict}")
                db_session.commit()
            
            # Finally, handle patient_age separately as it requires integer conversion
            if metadata.get("patient_age"):
                # Convert patient age to integer if it's a string
                age_str = metadata.get("patient_age")
                try:
                    # Extract numeric part if it includes units like "33 years"
                    age_numeric = re.search(r'\d+', str(age_str))
                    if age_numeric:
                        pdf.patient_age = int(age_numeric.group())
                        logger.info(f"Converted patient age from '{age_str}' to {pdf.patient_age}")
                        db_session.commit()  # Commit age change separately
                    else:
                        logger.warning(f"Could not extract numeric age from '{age_str}'")
                except Exception as e:
                    logger.error(f"Failed to parse patient age '{age_str}': {str(e)}")
        else:
            logger.warning(f"No metadata extracted for PDF {pdf_id}")
        
        # Parse biomarkers using Claude API
        logger.info(f"Parsing biomarkers from text for PDF {pdf_id}")
        biomarkers, metadata = extract_biomarkers_with_claude(text, pdf.filename)
        
        if not biomarkers:
            logger.warning(f"No biomarkers found in PDF {pdf_id}")
        else:
            logger.info(f"Extracted {len(biomarkers)} biomarkers from PDF {pdf_id}")
            
            # Save biomarkers to database
            for biomarker in biomarkers:
                db_session.add(Biomarker(
                    pdf_id=pdf.id,
                    profile_id=pdf.profile_id,
                    name=biomarker.get("name", "Unknown"),
                    original_name=biomarker.get("original_name", "Unknown"),
                    original_value=biomarker.get("original_value", ""),
                    value=biomarker.get("value", 0.0),
                    original_unit=biomarker.get("original_unit", ""),
                    unit=biomarker.get("unit", ""),
                    reference_range_low=biomarker.get("reference_range_low"),
                    reference_range_high=biomarker.get("reference_range_high"),
                    reference_range_text=biomarker.get("reference_range_text", ""),
                    category=biomarker.get("category", "Other"),
                    is_abnormal=biomarker.get("is_abnormal", False)
                ))
            
            # Update parsing confidence
            confidence = 0.0
            for biomarker in biomarkers:
                confidence += biomarker.get("confidence", 0.0)
            confidence = confidence / len(biomarkers) if biomarkers else 0.0
            pdf.parsing_confidence = confidence
        
        # Update status
        pdf.status = "processed"
        pdf.processed_date = datetime.utcnow()
        db_session.commit()
        
        logger.info(f"Completed processing PDF {pdf_id}")
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_id}: {str(e)}")
        pdf.status = "error"
        pdf.error_message = str(e)
        try:
            db_session.rollback()  # Rollback any pending transactions
            db_session.commit()
        except Exception as commit_error:
            logger.error(f"Error during error handling commit: {str(commit_error)}")
    finally:
        # Only close the session if we created it in this function
        if db_session is not None:
            db_session.close()
            logger.debug(f"Database session closed for PDF {pdf_id}")

# This is kept for backward compatibility
def parse_biomarkers_from_text(text: str, pdf_id=None) -> Tuple[List[Dict[str, Any]], float]:
    """
    Parse biomarker data from extracted text.
    
    Args:
        text: Extracted text from the PDF
        pdf_id: Optional PDF ID (for backward compatibility)
        
    Returns:
        Tuple containing a list of biomarker dictionaries and a confidence score
    """
    # Use the improved parser from biomarker_parser.py
    from app.services.biomarker_parser import parse_biomarkers_from_text as fallback_parser
    
    try:
        # First try to use the Claude API for better results
        if os.environ.get('ANTHROPIC_API_KEY'):
            from app.services.biomarker_parser import extract_biomarkers_with_claude
            # Ensure the pdf_id is properly formatted and sanitized to avoid format specifier issues
            pdf_filename = f"pdf_{pdf_id if pdf_id else 'unknown'}.pdf"
            biomarkers, _ = extract_biomarkers_with_claude(text, pdf_filename)
            
            # Calculate average confidence
            confidence = 0.0
            if biomarkers:
                for biomarker in biomarkers:
                    confidence += biomarker.get("confidence", 0.0)
                confidence = confidence / len(biomarkers)
            
            return biomarkers, confidence
    except Exception as e:
        logger.warning(f"Failed to extract biomarkers with Claude API: {str(e)}. Falling back to pattern matching.")
    
    # Fallback to pattern matching
    biomarkers = fallback_parser(text)
    confidence = 0.5  # Lower confidence for fallback parser
    
    return biomarkers, confidence 