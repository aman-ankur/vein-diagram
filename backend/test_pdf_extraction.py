import os
import sys
import logging
import json
from datetime import datetime
import pdfplumber
import pandas as pd

# Set the ANTHROPIC_API_KEY environment variable
# Replace this with your actual API key or set it in your environment before running
# os.environ["ANTHROPIC_API_KEY"] = "your_api_key_here"

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Import our services
from app.services.biomarker_parser import extract_biomarkers_with_claude

def test_pdf_extraction(pdf_path):
    """
    Test PDF extraction and biomarker parsing with detailed logging, using page-by-page approach.
    
    Args:
        pdf_path: Path to the PDF file to process
    """
    logger.info(f"=== PDF EXTRACTION TEST STARTED ===")
    logger.info(f"Processing PDF: {pdf_path}")
    
    # Process the PDF page by page
    all_biomarkers = []
    all_metadata = {}
    filename = os.path.basename(pdf_path)
    
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        logger.info(f"PDF has {total_pages} pages")
        
        # Limit to first 6 pages to reduce API costs
        max_pages = min(6, total_pages)
        logger.info(f"Processing only the first {max_pages} pages to optimize API usage")
        
        for page_num in range(max_pages):
            logger.info(f"Processing page {page_num + 1} of {total_pages} (limited to {max_pages})")
            
            # Extract text from the page
            page = pdf.pages[page_num]
            page_text = page.extract_text() or ""
            
            # Extract tables from the page and append to page_text
            tables = page.extract_tables()
            for table in tables:
                table_df = pd.DataFrame(table)
                page_text += "\n" + table_df.to_string(index=False, header=False)
            
            # Skip empty pages or pages with very little text
            if len(page_text.strip()) < 100:
                logger.info(f"Skipping page {page_num + 1} - insufficient text (length: {len(page_text)})")
                continue
            
            # Save the extracted text for inspection
            with open(f"extracted_text_page_{page_num + 1}.txt", "w") as f:
                f.write(page_text)
            logger.info(f"Saved extracted text from page {page_num + 1}")
            
            # Extract biomarkers using Claude
            logger.info(f"Extracting biomarkers from page {page_num + 1} with Claude...")
            start_time = datetime.now()
            
            try:
                page_biomarkers, page_metadata = extract_biomarkers_with_claude(
                    page_text, 
                    f"{filename} - page {page_num + 1}"
                )
                
                biomarker_duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"Page {page_num + 1} biomarker extraction complete: {len(page_biomarkers)} biomarkers in {biomarker_duration:.2f} seconds")
                
                # Add biomarkers to the overall list
                if page_biomarkers:
                    all_biomarkers.extend(page_biomarkers)
                    
                    # Save the page biomarkers to a file
                    with open(f"extracted_biomarkers_page_{page_num + 1}.json", "w") as f:
                        json.dump(page_biomarkers, f, indent=2)
                    logger.info(f"Saved biomarkers from page {page_num + 1}")
                
                # Update metadata if useful
                if not all_metadata and page_metadata:
                    all_metadata = page_metadata
                    
            except Exception as e:
                logger.error(f"Error processing page {page_num + 1}: {str(e)}")
                # Continue with next page
    
    # Deduplicate biomarkers
    unique_biomarkers = []
    seen_biomarkers = set()
    for biomarker in all_biomarkers:
        key = (biomarker.get('name', ''), str(biomarker.get('value', '')))
        if key not in seen_biomarkers:
            seen_biomarkers.add(key)
            unique_biomarkers.append(biomarker)
    
    all_biomarkers = unique_biomarkers
    
    # Save all biomarkers to a file
    with open("extracted_biomarkers_all.json", "w") as f:
        json.dump(all_biomarkers, f, indent=2)
    logger.info(f"Saved all biomarkers to extracted_biomarkers_all.json")
    
    # Print metadata
    logger.info(f"Metadata: {json.dumps(all_metadata, indent=2)}")
    
    # Print found biomarkers
    logger.info(f"Found {len(all_biomarkers)} unique biomarkers across all pages:")
    for i, biomarker in enumerate(all_biomarkers):
        logger.info(f"{i+1}. {biomarker.get('name')} = {biomarker.get('value')} {biomarker.get('unit')} "
                   f"(Range: {biomarker.get('reference_range_text')})")
    
    logger.info("=== PDF EXTRACTION TEST COMPLETED ===")

if __name__ == "__main__":
    # Path to the sample report
    pdf_path = "/Users/aankur/workspace/vein-diagram/backend/sample_reports/Aman_full_body_march_2025.pdf"
    test_pdf_extraction(pdf_path) 