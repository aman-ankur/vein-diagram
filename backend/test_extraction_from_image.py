#!/usr/bin/env python3
"""
Test script for biomarker extraction from an image.
This script uses OCR to extract text from an image file and processes it to extract biomarkers.

Usage:
    python test_extraction_from_image.py <image_file_path>
"""

import os
import sys
import json
import logging
import tempfile
from datetime import datetime
from typing import List, Dict, Any
from PIL import Image

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the extraction functions
from app.services.biomarker_parser import parse_biomarkers_from_text
from app.services.pdf_service import extract_text_from_pdf


def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using OCR.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Extracted text
    """
    try:
        # Check if pytesseract is installed
        import pytesseract
    except ImportError:
        print("Error: pytesseract not installed. Please install it with: pip install pytesseract")
        print("You also need to install Tesseract OCR on your system.")
        sys.exit(1)
    
    try:
        # Load the image
        img = Image.open(image_path)
        
        # Extract text using Tesseract OCR
        text = pytesseract.image_to_string(img)
        
        return text
    except Exception as e:
        print(f"Error extracting text from image: {str(e)}")
        sys.exit(1)


def write_text_to_temp_file(text: str) -> str:
    """
    Write text to a temporary file.
    
    Args:
        text: Text to write
        
    Returns:
        Path to the temporary file
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
            tmp.write(text.encode('utf-8'))
            return tmp.name
    except Exception as e:
        print(f"Error writing text to temporary file: {str(e)}")
        sys.exit(1)


def main():
    """Main function to test biomarker extraction from an image."""
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} <image_file_path>")
        sys.exit(1)
        
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: File not found - {image_path}")
        sys.exit(1)
        
    print(f"Processing image: {image_path}")
    
    try:
        # Extract text from image
        print("Extracting text from image...")
        text = extract_text_from_image(image_path)
        
        if not text:
            print("Error: Could not extract text from image")
            sys.exit(1)
            
        print(f"Extracted {len(text)} characters of text from image")
        
        # Create a temporary file with the extracted text for debugging
        temp_file = write_text_to_temp_file(text)
        print(f"Extracted text saved to: {temp_file}")
        
        # Extract biomarkers
        print("Extracting biomarkers...")
        biomarkers = parse_biomarkers_from_text(text)
        
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
                "metadata": {}
            }, f, indent=2)
            
        print(f"\nResults saved to {output_file}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 