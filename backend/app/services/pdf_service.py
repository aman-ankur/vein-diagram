import os
from typing import List, Dict, Any, Optional
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

from app.services.biomarker_parser import extract_biomarkers_with_claude, parse_biomarkers_from_text
from app.models.biomarker_model import Biomarker

# Configure logging with more detailed format
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up a file handler to also log to a file
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'pdf_service.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
logger.addHandler(file_handler)

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract text from a PDF file using PyPDF2 or Tesseract OCR for image-based PDFs.
    
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
            logger.debug(f"[PDF_METADATA] Number of pages: {len(pdf_reader.pages)}")
            if pdf_reader.metadata:
                logger.debug(f"[PDF_METADATA] Author: {pdf_reader.metadata.get('/Author', 'None')}")
                logger.debug(f"[PDF_METADATA] Creation date: {pdf_reader.metadata.get('/CreationDate', 'None')}")
            
            # Initialize an empty string to store the text
            text = ""
            
            # Loop through each page and extract text
            for page_num in range(len(pdf_reader.pages)):
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
        pages = pdf2image.convert_from_path(file_path, dpi=300)
        logger.debug(f"[OCR_PROCESS] Converted {len(pages)} pages to images")
        
        # Extract text from each page
        full_text = ""
        for i, page in enumerate(pages):
            logger.debug(f"[OCR_PAGE_PROCESSING] Processing page {i+1} of {len(pages)}")
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

def process_pdf_background(file_path: str, file_id: str, db: Session) -> None:
    """
    Process PDF file in background.
    
    Args:
        file_path: Path to the PDF file
        file_id: Unique ID of the file
        db: Database session
    """
    logger.info(f"[PDF_PROCESSING_START] Starting processing of PDF {file_id}")
    start_time = datetime.utcnow()
    
    try:
        # Get the PDF from the database
        from app.models.pdf_model import PDF as PDFModel
        
        pdf = db.query(PDFModel).filter(PDFModel.file_id == file_id).first()
        if not pdf:
            logger.error(f"[DB_ERROR] PDF with ID {file_id} not found in database")
            return
        
        # Update status to processing
        logger.debug(f"[STATUS_UPDATE] Setting status to 'processing' for PDF {file_id}")
        pdf.status = "processing"
        db.commit()
        
        # Extract text from the PDF
        logger.info(f"[TEXT_EXTRACTION] Extracting text from PDF {file_id}")
        text_start_time = datetime.utcnow()
        extracted_text = extract_text_from_pdf(file_path)
        text_extraction_time = (datetime.utcnow() - text_start_time).total_seconds()
        logger.info(f"[TEXT_EXTRACTION_COMPLETE] Text extraction took {text_extraction_time:.2f} seconds")
        
        # Extract biomarkers and metadata from the text
        logger.info(f"[BIOMARKER_EXTRACTION] Beginning biomarker extraction for PDF {file_id}")
        biomarker_start_time = datetime.utcnow()
        filename = os.path.basename(file_path)
        biomarkers_data, metadata = extract_biomarkers_with_claude(extracted_text, filename)
        biomarker_time = (datetime.utcnow() - biomarker_start_time).total_seconds()
        logger.info(f"[BIOMARKER_EXTRACTION_COMPLETE] Extracted {len(biomarkers_data)} biomarkers in {biomarker_time:.2f} seconds")
        
        # Log metadata
        logger.debug(f"[METADATA] Extracted metadata: {json.dumps(metadata)}")
        
        # Update the PDF record with extracted metadata
        if metadata:
            logger.debug(f"[METADATA_UPDATE] Updating PDF record with metadata")
            for key, value in metadata.items():
                if hasattr(pdf, key) and value:
                    logger.debug(f"[METADATA_FIELD] Setting {key} = {value}")
                    setattr(pdf, key, value)
            
            # Store any additional metadata that doesn't have a dedicated column
            processing_details = {}
            for key, value in metadata.items():
                if not hasattr(pdf, key):
                    processing_details[key] = value
            
            if processing_details:
                logger.debug(f"[ADDITIONAL_METADATA] Storing additional metadata: {json.dumps(processing_details)}")
                pdf.processing_details = processing_details
        
        # Extract report date if possible (if not already extracted by Claude)
        if not pdf.report_date:
            try:
                # Try to find a date in the format MM/DD/YYYY or similar
                import re
                date_matches = re.findall(r'(0[1-9]|1[0-2])[/\-](0[1-9]|[12][0-9]|3[01])[/\-](20\d{2})', extracted_text)
                if date_matches:
                    # Use the first date found (simplified)
                    month, day, year = date_matches[0]
                    report_date = datetime(int(year), int(month), int(day))
                    logger.info(f"[DATE_EXTRACTED] Found report date: {report_date.strftime('%m/%d/%Y')}")
                    pdf.report_date = report_date
            except Exception as date_error:
                logger.warning(f"[DATE_EXTRACTION_ERROR] Could not extract report date: {str(date_error)}")
        
        # Store the biomarker data
        logger.info(f"[BIOMARKER_STORAGE] Storing {len(biomarkers_data)} biomarkers in database")
        storage_start_time = datetime.utcnow()
        successful_biomarkers = 0
        
        for i, biomarker_data in enumerate(biomarkers_data):
            try:
                # Create a biomarker record
                biomarker = Biomarker(
                    pdf_id=pdf.id,
                    name=biomarker_data["name"],
                    original_name=biomarker_data["original_name"],
                    original_value=biomarker_data["original_value"],
                    original_unit=biomarker_data["original_unit"],
                    value=biomarker_data["value"],
                    unit=biomarker_data["unit"],
                    reference_range_low=biomarker_data.get("reference_range_low"),
                    reference_range_high=biomarker_data.get("reference_range_high"),
                    reference_range_text=biomarker_data.get("reference_range_text", ""),
                    category=biomarker_data.get("category", "Other"),
                    is_abnormal=biomarker_data.get("is_abnormal", False),
                    notes=biomarker_data.get("notes", "")
                )
                
                db.add(biomarker)
                successful_biomarkers += 1
                
                if i % 20 == 0 and i > 0:  # Log progress for every 20 biomarkers
                    logger.debug(f"[STORAGE_PROGRESS] Stored {i} of {len(biomarkers_data)} biomarkers")
                
            except Exception as biomarker_error:
                logger.error(f"[BIOMARKER_STORAGE_ERROR] Error adding biomarker {i} ({biomarker_data.get('name', 'Unknown')}): {str(biomarker_error)}")
                continue
        
        storage_time = (datetime.utcnow() - storage_start_time).total_seconds()
        logger.info(f"[BIOMARKER_STORAGE_COMPLETE] Successfully stored {successful_biomarkers} of {len(biomarkers_data)} biomarkers in {storage_time:.2f} seconds")
        
        # Update the PDF record
        pdf.extracted_text = extracted_text
        pdf.status = "processed"
        pdf.processed_date = datetime.utcnow()
        
        # Calculate the confidence score based on biomarker data
        if biomarkers_data:
            confidence_values = [b.get("confidence", 0.0) for b in biomarkers_data if "confidence" in b]
            if confidence_values:
                confidence_avg = sum(confidence_values) / len(confidence_values)
                logger.debug(f"[CONFIDENCE_SCORE] Average confidence: {confidence_avg:.2f}")
                pdf.parsing_confidence = confidence_avg
        
        # Save changes
        logger.debug(f"[DB_COMMIT] Committing changes to database for PDF {file_id}")
        db.commit()
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        logger.info(f"[PDF_PROCESSING_COMPLETE] Successfully processed PDF {file_id} in {total_time:.2f} seconds with {len(biomarkers_data)} biomarkers")
    except Exception as e:
        logger.error(f"[PDF_PROCESSING_ERROR] Error processing PDF {file_id}: {str(e)}")
        
        # Update the PDF record with error status
        try:
            pdf = db.query(PDFModel).filter(PDFModel.file_id == file_id).first()
            if pdf:
                logger.debug(f"[ERROR_STATUS_UPDATE] Setting status to 'error' for PDF {file_id}")
                pdf.status = "error"
                pdf.error_message = str(e)
                db.commit()
        except Exception as db_error:
            logger.error(f"[DB_ERROR] Error updating PDF record: {str(db_error)}")

# This is kept for backward compatibility
def parse_biomarkers_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Parse biomarker data from extracted text.
    
    Args:
        text: Extracted text from the PDF
        
    Returns:
        List[Dict[str, Any]]: List of biomarker data
    """
    # Use the improved parser from biomarker_parser.py
    from app.services.biomarker_parser import parse_biomarkers_from_text as new_parser
    return new_parser(text) 