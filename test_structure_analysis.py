#!/usr/bin/env python
"""
Test script for document structure analysis validation.
Run this script with a sample PDF to validate the Phase 1 implementation.

Usage:
    python test_structure_analysis.py path/to/sample.pdf
"""

import sys
import os
import logging
from pathlib import Path
import json

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Enable document structure debug output
os.environ["DEBUG_DOCUMENT_STRUCTURE"] = "1"

# Add the project root to path if needed
script_path = Path(__file__).resolve()
project_root = script_path.parent
sys.path.append(str(project_root))

try:
    # Import required modules
    from backend.app.services.document_analyzer import analyze_document_structure, debug_document_structure
    from backend.app.services.pdf_service import extract_text_from_pdf, filter_relevant_pages
    from backend.app.core.config import DOCUMENT_ANALYZER_CONFIG
except ImportError as e:
    logging.error(f"Import error: {e}. Make sure you're running from the project root.")
    sys.exit(1)

def test_pdf_structure(pdf_path):
    """Test document structure analysis on a PDF and output results."""
    logging.info(f"Testing document structure analysis on: {pdf_path}")
    
    # Check if feature is enabled
    if not DOCUMENT_ANALYZER_CONFIG.get("enabled", False) or not DOCUMENT_ANALYZER_CONFIG.get("structure_analysis", {}).get("enabled", False):
        logging.warning("Document structure analysis is disabled in config. Enabling for this test.")
    
    # Extract text from PDF
    logging.info("Extracting text from PDF...")
    try:
        pages_text_dict = extract_text_from_pdf(pdf_path)
        logging.info(f"Successfully extracted text from {len(pages_text_dict)} pages")
    except Exception as e:
        logging.error(f"Failed to extract text: {e}")
        return
    
    # Analyze document structure
    logging.info("Analyzing document structure...")
    try:
        document_structure = analyze_document_structure(pdf_path, pages_text_dict)
        
        # Print summary of document structure
        logging.info(f"Document type: {document_structure.get('document_type', 'Unknown')}")
        logging.info(f"Confidence: {document_structure.get('confidence', 0):.2f}")
        logging.info(f"Pages with tables: {len(document_structure.get('tables', {}))}")
        logging.info(f"Biomarker regions: {len(document_structure.get('biomarker_regions', []))}")
        
        # Save results to JSON for inspection
        output_file = f"structure_analysis_{Path(pdf_path).stem}.json"
        with open(output_file, 'w') as f:
            # Use a custom encoder to handle non-serializable objects
            json.dump(document_structure, f, indent=2, default=lambda o: str(o))
        logging.info(f"Saved detailed analysis to {output_file}")
        
        # Test page filtering with structure info
        relevant_pages = filter_relevant_pages(pages_text_dict, document_structure=document_structure)
        logging.info(f"Relevant pages with structure info: {relevant_pages}")
        
        # Compare with legacy filtering (without structure)
        legacy_pages = filter_relevant_pages(pages_text_dict)
        logging.info(f"Relevant pages without structure info: {legacy_pages}")
        
        # Compare differences
        structure_only = set(relevant_pages) - set(legacy_pages)
        legacy_only = set(legacy_pages) - set(relevant_pages)
        if structure_only:
            logging.info(f"Pages only relevant with structure analysis: {structure_only}")
        if legacy_only:
            logging.info(f"Pages only relevant without structure analysis: {legacy_only}")
            
        return document_structure
        
    except Exception as e:
        logging.error(f"Error during document analysis: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} path/to/sample.pdf")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        logging.error(f"PDF file not found: {pdf_path}")
        sys.exit(1)
        
    test_pdf_structure(pdf_path) 