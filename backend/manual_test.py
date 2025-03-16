#!/usr/bin/env python3
"""
Manual test script for biomarker validation.
This script includes hardcoded examples of problematic biomarker data
and tests our improved validation logic.
"""

import sys
import json
import logging
import re
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, ".")


def validate_biomarker(biomarker_data: Dict[str, Any]) -> bool:
    """
    Validate a biomarker data dictionary.
    
    Args:
        biomarker_data: Dictionary containing biomarker data
        
    Returns:
        True if valid, False otherwise
    """
    # Get biomarker name
    name = biomarker_data.get("name", "").strip()
    
    # Check name validity
    if (not name or 
        len(name) < 2 or 
        len(name) > 50 or
        name.isdigit() or  # Skip numeric-only names
        re.match(r'^\d+(st|nd|rd|th)\s*$', name) or  # Skip ordinals
        name.startswith(")") or  # Skip method descriptions
        re.match(r'^page \d+$', name.lower()) or  # Skip page numbers
        # Additional patterns for time descriptions
        re.match(r'^\d+\s*(am|pm)$', name.lower()) or  # Skip times like "4 am"
        'between' in name.lower() or  # Skip phrases with "between"
        'minimum' in name.lower() or  # Skip phrases with "minimum"
        'maximum' in name.lower() or  # Skip phrases with "maximum"
        'evening' in name.lower() or  # Skip phrases with "evening"
        'morning' in name.lower()):  # Skip phrases with "morning"
        logger.warning(f"[INVALID_BIOMARKER_NAME] Invalid biomarker name: {name}")
        return False
    
    # Check value validity
    try:
        value = float(biomarker_data.get("value", 0))
        if value == 0 and "0" not in str(biomarker_data.get("original_value", "")):
            logger.warning(f"[INVALID_BIOMARKER_VALUE] Invalid biomarker value (0): {name}")
            return False
    except (ValueError, TypeError):
        logger.warning(f"[INVALID_BIOMARKER_VALUE] Could not convert value to float: {biomarker_data.get('value')}")
        return False
    
    # Check unit validity
    unit = biomarker_data.get("unit", "").strip()
    if not unit:
        logger.warning(f"[INVALID_BIOMARKER_UNIT] Biomarker has no unit: {name}")
        return False
    
    # Check if name contains method description after closing parenthesis
    if ")" in name:
        # Only fix if it matches the pattern of a method description
        if re.search(r'\)\s+[\w\s]+(Kinetic|Substrate|Photometry|Buffer)', name):
            name_parts = name.split(")")
            if len(name_parts) > 1:
                # Use the part before the method description
                cleaned_name = name_parts[0].strip() + ")"
                logger.info(f"[BIOMARKER_NAME_FIXED] Fixed method description in name: '{name}' -> '{cleaned_name}'")
                biomarker_data["name"] = cleaned_name
    
    return True


def main():
    """Main function to test biomarker validation."""
    # List of problematic biomarker data examples
    problematic_biomarkers = [
        # Numeric-only names
        {"name": "100", "value": 125, "unit": "mg/dL"},
        {"name": "150", "value": 120, "unit": "mg/dL"},
        
        # Ordinal numbers
        {"name": "2nd", "value": 3, "unit": "units"},
        {"name": "3rd", "value": 10, "unit": "units"},
        
        # Time descriptions
        {"name": "4 am and at a minimum between Evening 6-", "value": 10, "unit": "pm"},
        {"name": "10 pm", "value": 5, "unit": "units"},
        
        # Method descriptions
        {"name": ") LDH, UV kinetic", "value": 26, "unit": "U/L"},
        {"name": ") Quantitative Capillary Photometry", "value": 30, "unit": "U/L"},
        {"name": ") SZAZ Carboxylated Substrate", "value": 17, "unit": "U/L"},
        
        # Valid biomarkers for comparison
        {"name": "Glucose", "value": 95, "unit": "mg/dL"},
        {"name": "Total Bilirubin", "value": 0.65, "unit": "mg/dL"},
        {"name": "Albumin", "value": 4.4, "unit": "g/dL"},
        
        # Edge cases
        {"name": "Thyroid Stimulating Hormone (TSH)", "value": 2.486, "unit": "μIU/mL"},
        {"name": "Alkaline Phosphatase (ALP)", "value": 70, "unit": "U/L"},
    ]
    
    print("Testing biomarker validation...")
    print("-" * 50)
    
    valid_biomarkers = []
    invalid_biomarkers = []
    
    for biomarker in problematic_biomarkers:
        print(f"\nTesting: {biomarker['name']}")
        print(f"Value: {biomarker['value']} {biomarker['unit']}")
        
        is_valid = validate_biomarker(biomarker)
        
        if is_valid:
            print(f"Result: VALID")
            valid_biomarkers.append(biomarker)
        else:
            print(f"Result: INVALID")
            invalid_biomarkers.append(biomarker)
    
    print("\n" + "=" * 50)
    print(f"Summary: {len(valid_biomarkers)} valid, {len(invalid_biomarkers)} invalid")
    
    print("\nValid biomarkers:")
    for i, biomarker in enumerate(valid_biomarkers, 1):
        print(f"{i}. {biomarker['name']} = {biomarker['value']} {biomarker['unit']}")
    
    print("\nInvalid biomarkers:")
    for i, biomarker in enumerate(invalid_biomarkers, 1):
        print(f"{i}. {biomarker['name']} = {biomarker['value']} {biomarker['unit']}")


if __name__ == "__main__":
    main() 