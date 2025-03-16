#!/usr/bin/env python3
"""
Test script for biomarker extraction.
This script processes a PDF file and prints the extracted biomarkers for validation.

Usage:
    python test_extraction.py <pdf_file_path>
"""

import os
import sys
import json
import logging
from datetime import datetime
import pdfplumber
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the extraction functions
from app.services.biomarker_parser import extract_biomarkers_with_claude, parse_biomarkers_from_text
from app.services.pdf_service import extract_text_from_pdf


def main():
    """Main function to test biomarker extraction."""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <pdf_file_path>")
        sys.exit(1)
        
    pdf_path = sys.argv[1]
    if not os.path.exists(pdf_path):
        print(f"Error: File not found - {pdf_path}")
        sys.exit(1)
        
    print(f"Processing PDF: {pdf_path}")
    
    # Extract text from PDF
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            
        if not text:
            print("Error: Could not extract text from PDF")
            sys.exit(1)
            
        print(f"Extracted {len(text)} characters of text from PDF")
        
        # Check if Anthropic API key is available
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            print("Using Claude API for extraction...")
            biomarkers, metadata = extract_biomarkers_with_claude(text, os.path.basename(pdf_path))
        else:
            print("Anthropic API key not available. Using fallback parser...")
            biomarkers = parse_biomarkers_from_text(text)
            metadata = {}
        
        # Print results
        print(f"\n=== Extracted {len(biomarkers)} biomarkers ===")
        for i, biomarker in enumerate(biomarkers, 1):
            print(f"\n{i}. {biomarker['name']}")
            print(f"   Value: {biomarker['value']} {biomarker['unit']}")
            print(f"   Reference Range: {biomarker.get('reference_range_text', 'Not available')}")
            print(f"   Category: {biomarker.get('category', 'Other')}")
            print(f"   Abnormal: {biomarker.get('is_abnormal', False)}")
        
        # Save to JSON file for further analysis
        output_file = f"extraction_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w") as f:
            json.dump({
                "biomarkers": biomarkers,
                "metadata": metadata
            }, f, indent=2)
            
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 