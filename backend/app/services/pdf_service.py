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
import asyncio

from app.services.biomarker_parser import (
    extract_biomarkers_with_claude,
    parse_biomarkers_from_text,
    standardize_unit,
    _preprocess_text_for_claude
)
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF  # Import the PDF model class
from app.db.database import SessionLocal  # Import SessionLocal for error handling
from app.services.health_summary_service import generate_and_update_health_summary # Import the new service function
from app.services.document_analyzer import (
    analyze_document_structure,
    optimize_content_for_extraction,
    create_adaptive_prompt,
    update_extraction_context,
    create_default_extraction_context,
    DocumentStructure
)
from app.core.config import DOCUMENT_ANALYZER_CONFIG

# Get logger for this module
logger = logging.getLogger(__name__)

# --- Helper Functions for Page Filtering (Phase 2) ---

def _load_biomarker_aliases() -> List[str]:
    """Loads biomarker names and aliases from the JSON file."""
    aliases = []
    try:
        # Construct the path relative to the current file's directory
        current_dir = os.path.dirname(__file__)
        aliases_path = os.path.join(current_dir, '..', 'utils', 'biomarker_aliases.json')
        
        with open(aliases_path, 'r') as f:
            data = json.load(f)
            for biomarker_info in data.get("biomarkers", []):
                # Add the main name
                if name := biomarker_info.get("name"):
                    aliases.append(name.lower())
                # Add all aliases
                for alias in biomarker_info.get("aliases", []):
                    aliases.append(alias.lower())
        logger.info(f"Loaded {len(aliases)} biomarker names and aliases.")
    except FileNotFoundError:
        logger.error(f"Biomarker aliases file not found at {aliases_path}")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from biomarker aliases file at {aliases_path}")
    except Exception as e:
        logger.error(f"Error loading biomarker aliases: {str(e)}")
    return list(set(aliases)) # Return unique list

def score_page_relevance(page_text: str, all_aliases: List[str]) -> int:
    """Scores a page based on the presence of biomarker keywords, units, and table patterns."""
    score = 0
    if not page_text:
        return 0

    # 1. Check for biomarker names/aliases (case-insensitive)
    # Create a regex pattern for aliases (ensure proper escaping)
    # Limit alias length to avoid overly broad matches
    valid_aliases = [re.escape(alias) for alias in all_aliases if 2 < len(alias) < 50]
    if valid_aliases:
        alias_pattern = r'\b(' + '|'.join(valid_aliases) + r')\b'
        try:
            # Use finditer to count occurrences efficiently
            matches = list(re.finditer(alias_pattern, page_text, re.IGNORECASE))
            if matches:
                score += 10 * len(matches) # Score per alias found
                logger.debug(f"Found {len(matches)} alias matches on page.")
        except re.error as re_err:
             logger.error(f"Regex error checking aliases: {re_err}")


    # 2. Check for common units associated with numeric values
    # Pattern: number (optional decimal) followed by common units
    unit_pattern = r'\b\d+(\.\d+)?\s*(mg/dL|g/dL|%|mmol/L|U/L|IU/L|ng/mL|pg/mL|mIU/L|μIU/mL|μg/dL|ug/dL|mEq/L|meq/L|K/μL|K/uL|M/μL|M/uL|fL|pg|mm/hr)\b'
    try:
        unit_matches = list(re.finditer(unit_pattern, page_text, re.IGNORECASE))
        if unit_matches:
            score += 1 * len(unit_matches) # Lower score for units
            logger.debug(f"Found {len(unit_matches)} unit matches on page.")
    except re.error as re_err:
        logger.error(f"Regex error checking units: {re_err}")

    # 3. Check for potential table structures (heuristic)
    # Look for multiple lines with similar indentation and potential delimiters (spaces, tabs)
    lines = page_text.strip().split('\n')
    table_like_lines = 0
    if len(lines) > 3: # Need at least a few lines to suggest a table
        potential_table_pattern = r'^\s*[\w\s\(\)\-\+,/]+(\s{2,}|\t)[\d\.<>\-\s]+' # Line starts with text, then space/tab, then numbers/symbols
        for line in lines:
            if re.search(potential_table_pattern, line):
                table_like_lines += 1
        if table_like_lines > 2: # If more than 2 lines look like table rows
            score += 5
            logger.debug(f"Found {table_like_lines} table-like lines.")

    logger.debug(f"Page scored with relevance: {score}")
    return score

def filter_relevant_pages(
    pages_text_dict,
    document_structure=None
) -> Dict[int, str]:
    """Filter pages with relevant content for biomarker extraction, now with structure awareness."""
    relevant_pages = []
    # Initialize filtered_pages here to prevent reference before assignment
    filtered_pages = {}
    
    all_aliases = _load_biomarker_aliases()
    if not all_aliases:
        logger.warning("No aliases loaded, cannot perform relevance scoring. Returning all pages.")
        # Fallback: return all pages if aliases couldn't be loaded
        return sorted(pages_text_dict.items())

    min_relevance_score = 1 # Minimum score to be considered relevant (at least one unit match or part of a table)

    for page_num, page_text in pages_text_dict.items():
        score = score_page_relevance(page_text, all_aliases)
        if score >= min_relevance_score:
            relevant_pages.append((page_num, page_text))
            logger.info(f"Page {page_num} deemed relevant with score {score}.")
        else:
             logger.info(f"Page {page_num} deemed irrelevant with score {score}.")

    # Sort by page number
    relevant_pages.sort(key=lambda x: x[0])
    logger.info(f"Filtered down to {len(relevant_pages)} relevant pages out of {len(pages_text_dict)} total.")

    # Enhanced version with structure awareness
    if document_structure is not None:
        logging.info("Using document structure to filter relevant pages")
        filtered_pages = {}
        
        for page_num, text in pages_text_dict.items():
            # Higher relevance if page has tables (likely to contain biomarkers)
            has_tables = page_num in document_structure.get("tables", {}) and document_structure["tables"][page_num]
            
            if has_tables:
                logging.info(f"Page {page_num} contains tables, including for biomarker extraction")
                filtered_pages[page_num] = text
                continue
            
            # Check if this is a content page (not just header/footer)
            page_zones = document_structure.get("page_zones", {}).get(page_num, {})
            content_zone = page_zones.get("content", {})
            
            # If we have a content zone with high confidence
            if content_zone and content_zone.get("confidence", 0) > 0.7:
                # Use the existing biomarker pattern matching logic
                if contain_biomarker_patterns(text):
                    logging.info(f"Page {page_num} contains biomarker patterns in content zone")
                    filtered_pages[page_num] = text
            else:
                # Fallback to original pattern matching
                if contain_biomarker_patterns(text):
                    logging.info(f"Page {page_num} contains biomarker patterns (fallback method)")
                    filtered_pages[page_num] = text
        
        if filtered_pages:
            return filtered_pages
        
        # If we filtered out all pages, fall back to original method
        logging.warning("Structure-based filtering removed all pages, falling back to original method")
    
    # Fall back to original method if structure not available or no pages found
    # Convert relevant_pages list to dictionary for consistent return type
    if not filtered_pages:
        filtered_pages = {page_num: text for page_num, text in relevant_pages}
    
    return filtered_pages

async def process_pages_sequentially(
    relevant_pages,
    document_structure=None
) -> List[Dict]:
    """Process pages sequentially, now with structure awareness and content optimization."""
    all_biomarkers = []
    extraction_context = None
    
    # Use enhanced processing if enabled
    if document_structure is not None and DOCUMENT_ANALYZER_CONFIG["enabled"]:
        logging.info("Using enhanced page processing with structure awareness")
        
        # Create initial extraction context
        extraction_context = create_default_extraction_context()
        
        # Optimize content into chunks based on structure
        if DOCUMENT_ANALYZER_CONFIG["content_optimization"]["enabled"]:
            content_chunks = optimize_content_for_extraction(relevant_pages, document_structure)
            
            # Process chunks instead of whole pages
            for chunk in content_chunks:
                # Skip chunks with very low biomarker confidence
                if chunk["biomarker_confidence"] < 0.3:
                    logging.info(f"Skipping low-confidence chunk from page {chunk['page_num']}")
                    continue
                
                # Create adaptive prompt if enabled
                if DOCUMENT_ANALYZER_CONFIG["adaptive_context"]["enabled"] and extraction_context:
                    prompt = create_adaptive_prompt(chunk, extraction_context)
                else:
                    # Use standard prompt
                    prompt = f"Extract biomarkers from the following text from page {chunk['page_num']}:\n\n{chunk['text']}"
                
                # Extract biomarkers with Claude
                biomarkers = await extract_biomarkers_with_claude(prompt)
                
                # Update context with results
                if DOCUMENT_ANALYZER_CONFIG["adaptive_context"]["enabled"] and extraction_context:
                    extraction_context = update_extraction_context(
                        extraction_context,
                        chunk,
                        biomarkers
                    )
                
                # Add page number to biomarkers
                for b in biomarkers:
                    b["page"] = chunk["page_num"]
                
                all_biomarkers.extend(biomarkers)
            
            # Log token usage statistics
            if extraction_context:
                logging.info(f"Token usage: {extraction_context['token_usage']}")
                
            return all_biomarkers
    
    # Fall back to original method - implement original sequential processing
    logger.info(f"Using original sequential processing for {len(relevant_pages)} relevant pages")
    
    for page_num, page_text in relevant_pages.items():
        logger.info(f"Processing page {page_num} sequentially")
        try:
            # Call the biomarker extractor
            page_biomarkers = await extract_biomarkers_with_claude(page_text)
            
            if page_biomarkers:
                logger.info(f"Extracted {len(page_biomarkers)} biomarkers from page {page_num}")
                # Add page number info
                for bm in page_biomarkers:
                    bm['page'] = page_num
                all_biomarkers.extend(page_biomarkers)
            else:
                logger.info(f"No biomarkers found on page {page_num}")
        except Exception as e:
            logger.error(f"Error processing page {page_num} sequentially: {str(e)}")
    
    return all_biomarkers

def contain_biomarker_patterns(text):
    """
    Check if text contains potential biomarker patterns.
    
    Args:
        text: The text to check
        
    Returns:
        bool: True if the text contains potential biomarker patterns
    """
    if not text:
        return False
        
    # Common biomarker indicators
    indicators = [
        r'\b\d+\.?\d*\s*(?:mg/dL|g/dL|mmol/L|mol/L|U/L|IU/L|ng/mL|pg/mL|mIU/L|μIU/mL|μg/dL|mcg/dL|%|mEq/L)',  # Values with units
        r'\bnormal\s*range',
        r'\breference\s*range',
        r'\brange',
        r'\bvalue',
        r'\bresult',
        r'\blow\b|\bhigh\b',
        r'\bpositive\b|\bnegative\b',
        r'\bchemistry\b',
        r'\bhematology\b',
        r'\btest\b|\btests\b'
    ]
    
    for pattern in indicators:
        if re.search(pattern, text, re.IGNORECASE):
            return True
            
    return False

# --- End Helper Functions ---


def extract_text_from_pdf(file_path: str) -> Dict[int, str]:
    """
    Extract text from all pages of a PDF file using PyPDF2 or Tesseract OCR for image-based PDFs.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dict[int, str]: Dictionary mapping page number (0-indexed) to extracted text.
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

            # Initialize a dictionary to store text per page
            pages_text_dict: Dict[int, str] = {}

            # Loop through each page and extract text
            logger.info(f"[PAGE_EXTRACTION] Extracting text from all {total_pages} pages.")
            for page_num in range(total_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    pages_text_dict[page_num] = page_text if page_text else ""
                    logger.debug(f"[PAGE_EXTRACTION] Page {page_num}: Extracted {len(page_text) if page_text else 0} characters")
                except Exception as page_error:
                    logger.error(f"[PAGE_EXTRACTION_ERROR] Error extracting text from page {page_num}: {str(page_error)}")
                    pages_text_dict[page_num] = "" # Store empty string on error

            # Log extracted text for debugging (save as JSON)
            debug_text_path = os.path.join(log_dir, f"pdf_extracted_text_{os.path.basename(file_path)}.json")
            try:
                with open(debug_text_path, "w") as f:
                    json.dump(pages_text_dict, f, indent=2)
                logger.debug(f"[EXTRACTED_TEXT_SAVED] PDF text per page saved to {debug_text_path}")
            except Exception as e:
                logger.error(f"[TEXT_SAVE_ERROR] Could not save extracted text dictionary: {str(e)}")

            # If no text was extracted from any page, the PDF might be image-based
            if not any(pages_text_dict.values()):
                logger.info("[OCR_FALLBACK] No text extracted with PyPDF2 from any page, PDF might be image-based. Attempting OCR...")
                pages_text_dict = _extract_text_with_ocr(file_path)

                # Save OCR text for debugging (save as JSON)
                debug_ocr_path = os.path.join(log_dir, f"pdf_ocr_text_{os.path.basename(file_path)}.json")
                try:
                    with open(debug_ocr_path, "w") as f:
                        json.dump(pages_text_dict, f, indent=2)
                    logger.debug(f"[OCR_TEXT_SAVED] OCR text per page saved to {debug_ocr_path}")
                except Exception as e:
                    logger.error(f"[OCR_TEXT_SAVE_ERROR] Could not save OCR text dictionary: {str(e)}")

            extraction_time = (datetime.utcnow() - start_time).total_seconds()
            total_chars = sum(len(txt) for txt in pages_text_dict.values())
            logger.info(f"[PDF_TEXT_EXTRACTION_COMPLETE] Extracted {total_chars} characters across {len(pages_text_dict)} pages in {extraction_time:.2f} seconds")

            return pages_text_dict
    except Exception as e:
        logger.error(f"[PDF_EXTRACTION_ERROR] Error extracting text from PDF: {str(e)}")
        raise

def _extract_text_with_ocr(file_path: str) -> Dict[int, str]:
    """
    Extract text from all pages of an image-based PDF using Tesseract OCR.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dict[int, str]: Dictionary mapping page number (0-indexed) to extracted text.
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
        # Process all pages
        pages = pdf2image.convert_from_path(file_path, dpi=300) # Removed page limits
        total_pages_converted = len(pages)
        logger.debug(f"[OCR_PROCESS] Converted {total_pages_converted} pages to images")

        # Extract text from each page
        pages_text_dict: Dict[int, str] = {}
        for i, page in enumerate(pages):
            logger.debug(f"[OCR_PAGE_PROCESSING] Processing page {i} of {total_pages_converted-1}")
            page_start_time = datetime.utcnow()

            # Save the page image for debugging
            img_path = os.path.join(debug_img_dir, f"page_{i}.png")
            try:
                page.save(img_path)
                logger.debug(f"[OCR_IMAGE_SAVED] Saved page {i} image to {img_path}")
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
                page_text_path = os.path.join(debug_img_dir, f"page_{i}_text.txt")
                try:
                    with open(page_text_path, "w") as f:
                        f.write(page_text)
                    logger.debug(f"[OCR_PAGE_TEXT_SAVED] OCR text for page {i} saved to {page_text_path}")
                except Exception as e:
                    logger.error(f"[OCR_PAGE_TEXT_SAVE_ERROR] Could not save page OCR text: {str(e)}")

                logger.debug(f"[OCR_PAGE_COMPLETE] Page {i} processed in {page_time:.2f} seconds, extracted {len(page_text)} characters")
                pages_text_dict[i] = page_text
            except Exception as e:
                logger.error(f"[OCR_PAGE_ERROR] Error performing OCR on page {i}: {str(e)}")
                pages_text_dict[i] = "" # Store empty string on error

        if not any(pages_text_dict.values()):
            logger.warning("[OCR_NO_TEXT] OCR could not extract any text from the PDF")
            # Return empty dict, but log the issue
            return {}

        ocr_time = (datetime.utcnow() - ocr_start_time).total_seconds()
        logger.info(f"[OCR_COMPLETE] OCR processing completed in {ocr_time:.2f} seconds")
        return pages_text_dict

    except Exception as e:
        logger.error(f"[OCR_ERROR] Error during OCR processing: {str(e)}")
        # Return empty dict on major error
        return {}

async def process_pdf_background(pdf_id: int, db_session=None):
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
        
        # Extract text from all pages
        logger.info(f"Extracting text from PDF {pdf_id}")
        pages_text_dict = extract_text_from_pdf(pdf.file_path)

        # Combine text for saving (or consider saving page-wise if needed later)
        full_extracted_text = "\n--- Page Break ---\n".join(pages_text_dict.values())
        pdf.extracted_text = full_extracted_text # Store combined text for now
        db_session.commit()

        # After text extraction, analyze document structure
        document_structure = None
        if DOCUMENT_ANALYZER_CONFIG["enabled"] and DOCUMENT_ANALYZER_CONFIG["structure_analysis"]["enabled"]:
            logging.info(f"Analyzing document structure for {pdf_id}")
            document_structure = analyze_document_structure(pdf.file_path, pages_text_dict)
            logging.info(f"Document structure analysis complete with confidence {document_structure['confidence']}")
            
            # If analysis confidence is low and fallback is enabled, ignore structure
            if (document_structure["confidence"] < 0.5 and 
                DOCUMENT_ANALYZER_CONFIG["structure_analysis"]["fallback_to_legacy"]):
                logging.warning(f"Low structure confidence ({document_structure['confidence']}), using legacy processing")
                document_structure = None
        
        # Filter relevant pages with structure context
        relevant_pages = filter_relevant_pages(
            pages_text_dict,
            document_structure=document_structure
        )
        
        # Process pages with structure context
        extracted_biomarkers = await process_pages_sequentially(
            relevant_pages,
            document_structure=document_structure
        )

        # --- Metadata Extraction (Phase 3) ---
        # Extract metadata using only the first few pages (e.g., 0, 1, 2)
        num_pages_for_metadata = 3
        metadata_text = ""
        for i in range(num_pages_for_metadata):
            metadata_text += pages_text_dict.get(i, "") + "\n" # Add newline separator
        
        logger.info(f"Parsing metadata from first {num_pages_for_metadata} pages' text for PDF {pdf_id}")
        from app.services.metadata_parser import extract_metadata_with_claude
        
        # Properly handle the async function
        try:
            # We need to handle the async function without asyncio.run() as we might be in a context
            # where an event loop is already running
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            metadata = loop.run_until_complete(extract_metadata_with_claude(metadata_text.strip(), pdf.filename))
            loop.close()
            logger.info(f"Successfully extracted metadata")
        except Exception as metadata_error:
            logger.error(f"Error extracting metadata: {str(metadata_error)}")
            metadata = {}
        
        # Update PDF with extracted metadata (existing logic)
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
        
        # --- Save Biomarkers ---
        if not extracted_biomarkers:
            logger.warning(f"No biomarkers extracted after filtering and sequential processing for PDF {pdf_id}")
        else:
            logger.info(f"Extracted {len(extracted_biomarkers)} biomarkers from PDF {pdf_id}")

            # Save biomarkers to database
            for biomarker in extracted_biomarkers:
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
            for biomarker in extracted_biomarkers:
                confidence += biomarker.get("confidence", 0.0)
            confidence = confidence / len(extracted_biomarkers) if extracted_biomarkers else 0.0
            pdf.parsing_confidence = confidence
        
        # Update status
        pdf.status = "processed"
        pdf.processed_date = datetime.utcnow()
        db_session.commit() # Commit biomarker saves and status update

        # --- Trigger Health Summary Generation (Temporarily disabled) ---
        if pdf.profile_id and extracted_biomarkers: # Only generate if biomarkers were saved and profile exists
            try:
                logger.info(f"Triggering health summary generation for profile {pdf.profile_id} after processing PDF {pdf_id}")
                # Run the async function synchronously in this background task context
                asyncio.run(generate_and_update_health_summary(pdf.profile_id, db_session))
            except Exception as summary_error:
                # Log the error but don't let it fail the whole PDF processing
                logger.error(f"Error during triggered health summary generation for profile {pdf.profile_id}: {summary_error}", exc_info=True)
        elif not pdf.profile_id:
             logger.warning(f"PDF {pdf_id} has no associated profile_id, skipping health summary generation.")
        # If no biomarkers were found, summary generation is skipped implicitly by health_summary_service

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
