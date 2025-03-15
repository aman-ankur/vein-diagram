import os
import logging
import json
from datetime import datetime
import pdfplumber
import pandas as pd

# Set the ANTHROPIC_API_KEY environment variable
# Replace this with your actual API key
os.environ["ANTHROPIC_API_KEY"] = "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"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import our services
from app.services.pdf_service import extract_text_from_pdf
from app.services.biomarker_parser import extract_biomarkers_with_claude

def test_pdf_extraction(pdf_path):
    """
    Test PDF extraction and biomarker parsing with detailed logging.
    
    Args:
        pdf_path: Path to the PDF file to process
    """
    logger.info(f"=== PDF EXTRACTION TEST STARTED ===")
    logger.info(f"Processing PDF: {pdf_path}")
    
    # Extract text from PDF
    logger.info("Extracting text from PDF...")
    start_time = datetime.now()
    pdf_text = extract_text_from_pdf(pdf_path)
    # pdf_text_first_page = pdf_text.split("Page 1 /")[1].split("Page 2 /")[0]
    # pdf_text_small = pdf_text[:1000]
    text_duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Text extraction complete: {len(pdf_text)} characters in {text_duration:.2f} seconds")
    
    # Save the extracted text for inspection
    with open("extracted_text.txt", "w") as f:
        f.write(pdf_text)
    logger.info(f"Saved extracted text to extracted_text.txt")
    
    # Extract biomarkers using Claude
    logger.info("Extracting biomarkers with Claude...")
    start_time = datetime.now()

    with pdfplumber.open(pdf_path) as pdf:
        # Check if the PDF has at least 6 pages
        if len(pdf.pages) < 6:
            print("Error: PDF has fewer than 6 pages.")
            return
        
        # Access the 6th page (index 5)
        page = pdf.pages[5]
        
        # Extract text from the 6th page
        page_text = page.extract_text() or ""  # Use empty string if no text is extracted
        
        # Extract tables from the 6th page (if any) and append to page_text
        tables = page.extract_tables()
        for table in tables:
            df = pd.DataFrame(table)
            page_text += "\n" + df.to_string(index=False, header=False)

    biomarkers, metadata = extract_biomarkers_with_claude(page_text, os.path.basename(pdf_path))
    biomarker_duration = (datetime.now() - start_time).total_seconds()
    logger.info(f"Biomarker extraction complete: {len(biomarkers)} biomarkers in {biomarker_duration:.2f} seconds")
    
    # Save biomarkers to a file
    with open("extracted_biomarkers.json", "w") as f:
        json.dump(biomarkers, f, indent=2)
    logger.info(f"Saved biomarkers to extracted_biomarkers.json")
    
    # Print metadata
    logger.info(f"Metadata: {json.dumps(metadata, indent=2)}")
    
    # Print found biomarkers
    logger.info(f"Found {len(biomarkers)} biomarkers:")
    for i, biomarker in enumerate(biomarkers):
        logger.info(f"{i+1}. {biomarker.get('name')} = {biomarker.get('value')} {biomarker.get('unit')} "
                   f"(Range: {biomarker.get('reference_range_text')})")
    
    logger.info("=== PDF EXTRACTION TEST COMPLETED ===")

if __name__ == "__main__":
    # Path to the sample report
    pdf_path = "/Users/aankur/workspace/vein-diagram/backend/sample_reports/Aman_full_body_march_2025.pdf"
    test_pdf_extraction(pdf_path) 