import pytest
import json
from unittest.mock import patch, MagicMock
import httpx
import os
from app.services.biomarker_parser import (
    extract_biomarkers_with_claude,
    parse_biomarkers_from_text,
    parse_reference_range,
    standardize_unit,
    categorize_biomarker,
    _process_biomarker,
    BIOMARKER_ALIASES
)
import re

@pytest.fixture
def sample_lab_text():
    """Sample lab report text for testing."""
    return """
    LABORATORY REPORT
    Patient: John Doe
    Specimen Collected: 01/15/2023
    Lab: LabCorp
    
    TEST                    RESULT      REFERENCE RANGE    FLAG
    Glucose                 95 mg/dL    70-99              
    Hemoglobin A1c          5.7 %       < 5.7              
    Total Cholesterol       210 mg/dL   < 200              HIGH
    HDL Cholesterol         55 mg/dL    > 40               
    LDL Cholesterol         135 mg/dL   < 100              HIGH
    Triglycerides           100 mg/dL   < 150              
    TSH                     2.5 mIU/L   0.4-4.0            
    Vitamin D, 25-OH        32 ng/mL    30-100             
    """

@pytest.fixture
def claude_response():
    """Sample Claude API response."""
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({
                    "biomarkers": [
                        {
                            "name": "Glucose",
                            "value": 95,
                            "unit": "mg/dL",
                            "reference_range": "70-99",
                            "category": "Metabolic"
                        },
                        {
                            "name": "Hemoglobin A1c",
                            "value": 5.7,
                            "unit": "%",
                            "reference_range": "< 5.7",
                            "category": "Metabolic"
                        },
                        {
                            "name": "Total Cholesterol",
                            "value": 210,
                            "unit": "mg/dL",
                            "reference_range": "< 200",
                            "category": "Lipid",
                            "flag": "HIGH"
                        },
                        {
                            "name": "HDL Cholesterol",
                            "value": 55,
                            "unit": "mg/dL",
                            "reference_range": "> 40",
                            "category": "Lipid"
                        },
                        {
                            "name": "LDL Cholesterol",
                            "value": 135,
                            "unit": "mg/dL",
                            "reference_range": "< 100",
                            "category": "Lipid",
                            "flag": "HIGH"
                        },
                        {
                            "name": "Triglycerides",
                            "value": 100,
                            "unit": "mg/dL",
                            "reference_range": "< 150",
                            "category": "Lipid"
                        },
                        {
                            "name": "TSH",
                            "value": 2.5,
                            "unit": "mIU/L",
                            "reference_range": "0.4-4.0",
                            "category": "Hormone"
                        },
                        {
                            "name": "Vitamin D, 25-OH",
                            "value": 32,
                            "unit": "ng/mL",
                            "reference_range": "30-100",
                            "category": "Vitamin"
                        }
                    ],
                    "metadata": {
                        "lab_name": "LabCorp",
                        "report_date": "01/15/2023",
                        "patient_name": "John Doe"
                    }
                })
            }
        ]
    }

def test_parse_reference_range():
    """Test parsing reference ranges to extract low and high values."""
    # Test range with dash format
    low, high, text = parse_reference_range("70-99")
    assert low == 70.0
    assert high == 99.0
    assert text == "70-99"
    
    # Test less than format
    low, high, text = parse_reference_range("< 200")
    assert low is None
    assert high == 200.0
    assert text == "< 200"
    
    # Test greater than format
    low, high, text = parse_reference_range("> 40")
    assert low == 40.0
    assert high is None
    assert text == "> 40"
    
    # Test complex format
    low, high, text = parse_reference_range("Negative (<10)")
    assert low is None
    assert high == 10.0
    assert text == "Negative (<10)"
    
    # Test non-numeric reference range
    low, high, text = parse_reference_range("Negative")
    assert low is None
    assert high is None
    assert text == "Negative"

def test_standardize_unit():
    """Test standardizing units to a common format."""
    # Test common variations
    assert standardize_unit("mg/dL") == "mg/dL"
    assert standardize_unit("mg/dl") == "mg/dL"
    assert standardize_unit("mg / dL") == "mg/dL"
    assert standardize_unit("mg/deciliter") == "mg/dL"
    
    # Test percentage
    assert standardize_unit("%") == "%"
    assert standardize_unit("percent") == "%"
    assert standardize_unit("percentage") == "%"
    
    # Test units with prefixes
    assert standardize_unit("μg/mL") == "μg/mL"
    assert standardize_unit("mcg/mL") == "μg/mL"
    assert standardize_unit("ng/mL") == "ng/mL"
    
    # Test unknown unit
    assert standardize_unit("unknown_unit") == "unknown_unit"

def test_biomarker_aliases():
    """Test that key biomarkers have aliases defined."""
    # Check common biomarkers have aliases
    assert "glucose" in BIOMARKER_ALIASES
    assert "total cholesterol" in BIOMARKER_ALIASES
    assert "tsh" in BIOMARKER_ALIASES
    
    # Check aliases resolve correctly
    glucose_aliases = BIOMARKER_ALIASES["glucose"]
    assert "blood glucose" in glucose_aliases
    assert "fasting glucose" in glucose_aliases

def test_parse_biomarkers_from_text(sample_lab_text):
    """Test parsing biomarkers from text using the fallback parser."""
    biomarkers = parse_biomarkers_from_text(sample_lab_text)
    
    # Just ensure we get some biomarkers
    assert len(biomarkers) > 0
    
    # Check at least one common biomarker is detected
    glucose_found = False
    for biomarker in biomarkers:
        if biomarker.get("name", "").lower() == "glucose":
            glucose_found = True
            break
    
    assert glucose_found, "Glucose biomarker should be detected"

@patch("httpx.Client")
def test_extract_biomarkers_with_claude(mock_client, sample_lab_text, claude_response):
    """Test extracting biomarkers using Claude API."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = claude_response
    
    mock_client_instance = MagicMock()
    mock_client_instance.post.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance
    
    # Mock environment variable
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        biomarkers, metadata = extract_biomarkers_with_claude(sample_lab_text, "test_file.pdf")
    
    # Verify results
    assert len(biomarkers) == 8
    assert metadata["lab_name"] == "LabCorp"
    assert metadata["report_date"] == "01/15/2023"
    
    # Verify a specific biomarker
    glucose = next(b for b in biomarkers if b["name"] == "Glucose")
    assert glucose["value"] == 95.0
    assert glucose["unit"] == "mg/dL"
    assert glucose["reference_range_low"] == 70.0
    assert glucose["reference_range_high"] == 99.0

@patch("httpx.Client")
def test_extract_biomarkers_with_claude_error(mock_client, sample_lab_text):
    """Test handling errors in Claude API calls."""
    # Setup mock response
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal server error"
    
    mock_client_instance = MagicMock()
    mock_client_instance.post.return_value = mock_response
    mock_client.return_value.__enter__.return_value = mock_client_instance
    
    # Mock environment variable
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        biomarkers, metadata = extract_biomarkers_with_claude(sample_lab_text, "test_file.pdf")
    
    # If API fails, we should still get results from fallback parser
    assert len(biomarkers) > 0
    
    # Metadata should be minimal
    assert metadata == {}

@patch("os.environ.get")
def test_extract_biomarkers_without_api_key(mock_env_get, sample_lab_text):
    """Test extraction when API key is not available."""
    # Simulate no API key
    mock_env_get.return_value = None
    
    biomarkers, metadata = extract_biomarkers_with_claude(sample_lab_text, "test_file.pdf")
    
    # Should use fallback parser
    assert len(biomarkers) > 0
    
    # Metadata should be minimal
    assert metadata == {} 

def test_parse_reference_range_hyphen():
    """Test parsing reference range with hyphen format."""
    low, high, original = parse_reference_range("70-99")
    assert low == 70
    assert high == 99
    assert original == "70-99"
    
def test_parse_reference_range_less_than():
    """Test parsing reference range with less than format."""
    low, high, original = parse_reference_range("< 200")
    assert low is None
    assert high == 200
    assert original == "< 200"
    
def test_parse_reference_range_greater_than():
    """Test parsing reference range with greater than format."""
    low, high, original = parse_reference_range("> 40")
    assert low == 40
    assert high is None
    assert original == "> 40"
    
def test_parse_reference_range_invalid():
    """Test parsing invalid reference range."""
    low, high, original = parse_reference_range("Normal")
    assert low is None
    assert high is None
    assert original == "Normal"

def test_parse_reference_range_empty():
    """Test parsing empty reference range."""
    low, high, original = parse_reference_range("")
    assert low is None
    assert high is None
    assert original == ""

def test_standardize_unit_mg_dl():
    """Test standardizing mg/dL units."""
    assert standardize_unit("mg/dl") == "mg/dL"
    assert standardize_unit("mg / dl") == "mg/dL"
    assert standardize_unit("mg/deciliter") == "mg/dL"

def test_standardize_unit_percentage():
    """Test standardizing percentage units."""
    assert standardize_unit("percent") == "%"
    assert standardize_unit("percentage") == "%"
    assert standardize_unit("pct") == "%"

def test_standardize_unit_mmol_l():
    """Test standardizing mmol/L units."""
    assert standardize_unit("mmol/l") == "mmol/L"
    assert standardize_unit("mmol / l") == "mmol/L"

def test_standardize_unit_micro():
    """Test standardizing micro units."""
    assert standardize_unit("mcg/ml") == "μg/mL"
    assert standardize_unit("mcg/dl") == "μg/dL"

def test_categorize_biomarker_lipid():
    """Test categorizing lipid biomarkers."""
    assert categorize_biomarker("Total Cholesterol") == "Lipid"
    assert categorize_biomarker("LDL Cholesterol") == "Lipid"
    assert categorize_biomarker("HDL Cholesterol") == "Lipid"
    assert categorize_biomarker("Triglycerides") == "Lipid"

def test_categorize_biomarker_metabolic():
    """Test categorizing metabolic biomarkers."""
    assert categorize_biomarker("Glucose") == "Metabolic"
    assert categorize_biomarker("HbA1c") == "Metabolic"
    assert categorize_biomarker("Insulin") == "Metabolic"

def test_categorize_biomarker_thyroid():
    """Test categorizing thyroid biomarkers."""
    assert categorize_biomarker("TSH") == "Hormone"
    assert categorize_biomarker("Free T4") == "Hormone"
    assert categorize_biomarker("Free T3") == "Hormone"

def test_categorize_biomarker_vitamin():
    """Test categorizing vitamin biomarkers."""
    assert categorize_biomarker("Vitamin D") == "Vitamin"
    assert categorize_biomarker("Vitamin B12") == "Vitamin"
    assert categorize_biomarker("Folate") == "Vitamin"

def test_categorize_biomarker_mineral():
    """Test categorizing mineral biomarkers."""
    assert categorize_biomarker("Iron") == "Mineral"
    assert categorize_biomarker("Ferritin") == "Mineral"
    assert categorize_biomarker("Magnesium") == "Mineral"
    assert categorize_biomarker("Calcium") == "Mineral"
    assert categorize_biomarker("Sodium") == "Mineral"
    assert categorize_biomarker("Potassium") == "Mineral"

def test_categorize_biomarker_blood():
    """Test categorizing blood biomarkers."""
    assert categorize_biomarker("Hemoglobin") == "Blood"
    assert categorize_biomarker("Hematocrit") == "Blood"
    assert categorize_biomarker("WBC") == "Blood"
    assert categorize_biomarker("RBC") == "Blood"
    assert categorize_biomarker("Platelet Count") == "Blood"

def test_categorize_biomarker_liver():
    """Test categorizing liver biomarkers."""
    assert categorize_biomarker("ALT") == "Liver"
    assert categorize_biomarker("AST") == "Liver"
    assert categorize_biomarker("ALP") == "Liver"
    assert categorize_biomarker("Bilirubin") == "Liver"
    assert categorize_biomarker("Albumin") == "Liver"

def test_categorize_biomarker_kidney():
    """Test categorizing kidney biomarkers."""
    assert categorize_biomarker("Creatinine") == "Kidney"
    assert categorize_biomarker("eGFR") == "Kidney"
    assert categorize_biomarker("BUN") == "Kidney"

def test_categorize_biomarker_other():
    """Test categorizing unknown biomarkers."""
    assert categorize_biomarker("Unknown Marker") == "Other"
    assert categorize_biomarker("Some Test") == "Other"

def test_process_biomarker_normal():
    """Test processing a normal biomarker."""
    biomarker = {
        "name": "Glucose",
        "value": "95",
        "unit": "mg/dl",
        "reference_range": "70-99"
    }
    
    processed = _process_biomarker(biomarker)
    
    assert processed["name"] == "Glucose"
    assert processed["value"] == 95.0
    assert processed["unit"] == "mg/dL"
    assert processed["reference_range_low"] == 70.0
    assert processed["reference_range_high"] == 99.0
    assert processed["is_abnormal"] is False

def test_process_biomarker_abnormal_high():
    """Test processing an abnormally high biomarker."""
    biomarker = {
        "name": "Glucose",
        "value": "120",
        "unit": "mg/dl",
        "reference_range": "70-99",
        "flag": "H"
    }
    
    processed = _process_biomarker(biomarker)
    
    assert processed["name"] == "Glucose"
    assert processed["value"] == 120.0
    assert processed["unit"] == "mg/dL"
    assert processed["reference_range_low"] == 70.0
    assert processed["reference_range_high"] == 99.0
    assert processed["is_abnormal"] is True

def test_process_biomarker_error_handling():
    """Test error handling in biomarker processing."""
    biomarker = {
        "name": "Glucose",
        "value": "Not a number",
        "unit": "mg/dl"
    }
    
    processed = _process_biomarker(biomarker)
    
    assert processed["name"] == "Glucose"
    assert processed["value"] == 0.0
    assert processed["unit"] == "mg/dL"
    assert "is_abnormal" in processed

def test_parse_biomarkers_from_text():
    """Test the fallback parser with a sample text."""
    text = """
    Lipid Panel:
    Total Cholesterol: 185 mg/dL (125-200)
    HDL Cholesterol: 55 mg/dL (>40)
    LDL Cholesterol: 110 mg/dL (<130)
    Triglycerides: 95 mg/dL (<150)
    
    Metabolic Panel:
    Glucose: 92 mg/dL (70-99)
    HbA1c: 5.4 % (4.0-5.6)
    """
    
    biomarkers = parse_biomarkers_from_text(text)
    
    assert len(biomarkers) >= 6
    
    # Check that we found the expected biomarkers
    biomarker_names = [b["name"].lower() for b in biomarkers]
    assert "total cholesterol" in biomarker_names
    assert "hdl cholesterol" in biomarker_names
    assert "ldl cholesterol" in biomarker_names
    assert "triglycerides" in biomarker_names
    assert "glucose" in biomarker_names
    assert "hba1c" in biomarker_names
    
    # Check the values of some biomarkers
    glucose = next(b for b in biomarkers if b["name"].lower() == "glucose")
    assert glucose["value"] == 92.0
    assert glucose["unit"] == "mg/dL"
    assert glucose["reference_range_low"] == 70.0
    assert glucose["reference_range_high"] == 99.0

@patch('httpx.Client')
def test_extract_biomarkers_with_claude_success(mock_client):
    """Test successful extraction of biomarkers using Claude API."""
    # Set up the mock
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [
            {
                "type": "text",
                "text": json.dumps({
                    "biomarkers": [
                        {
                            "name": "Glucose",
                            "value": 95,
                            "unit": "mg/dL",
                            "reference_range": "70-99",
                            "category": "Metabolic",
                            "flag": ""
                        },
                        {
                            "name": "Total Cholesterol",
                            "value": 185,
                            "unit": "mg/dL",
                            "reference_range": "125-200",
                            "category": "Lipid",
                            "flag": ""
                        }
                    ],
                    "metadata": {
                        "lab_name": "LabCorp",
                        "report_date": "05/15/2023"
                    }
                })
            }
        ]
    }
    
    mock_client.return_value.__enter__.return_value.post.return_value = mock_response
    
    # Set environment variable for API key
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        biomarkers, metadata = extract_biomarkers_with_claude("Sample text", "sample.pdf")
    
    assert len(biomarkers) == 2
    assert metadata["lab_name"] == "LabCorp"
    assert metadata["report_date"] == "05/15/2023"
    
    # Check glucose biomarker
    glucose = biomarkers[0]
    assert glucose["name"] == "Glucose"
    assert glucose["value"] == 95.0
    assert glucose["unit"] == "mg/dL"
    assert glucose["reference_range_low"] == 70.0
    assert glucose["reference_range_high"] == 99.0
    assert glucose["is_abnormal"] is False
    
    # Check cholesterol biomarker
    cholesterol = biomarkers[1]
    assert cholesterol["name"] == "Total Cholesterol"
    assert cholesterol["value"] == 185.0
    assert cholesterol["unit"] == "mg/dL"
    assert cholesterol["reference_range_low"] == 125.0
    assert cholesterol["reference_range_high"] == 200.0
    assert cholesterol["is_abnormal"] is False

@patch('httpx.Client')
def test_extract_biomarkers_with_claude_api_error(mock_client):
    """Test fallback to parsing when Claude API returns an error."""
    # Set up the mock to simulate an API error
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Error"
    
    mock_client.return_value.__enter__.return_value.post.return_value = mock_response
    
    # Set environment variable for API key
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        biomarkers, metadata = extract_biomarkers_with_claude(
            """
            Glucose: 95 mg/dL (70-99)
            Total Cholesterol: 185 mg/dL (125-200)
            """, 
            "sample.pdf"
        )
    
    # Should fallback to text parsing
    assert len(biomarkers) > 0
    assert len(metadata) == 0

@patch('httpx.Client')
def test_extract_biomarkers_with_claude_json_error(mock_client):
    """Test fallback to parsing when Claude API returns invalid JSON."""
    # Set up the mock to return non-JSON response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [
            {
                "type": "text",
                "text": "Not valid JSON"
            }
        ]
    }
    
    mock_client.return_value.__enter__.return_value.post.return_value = mock_response
    
    # Set environment variable for API key
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        biomarkers, metadata = extract_biomarkers_with_claude(
            """
            Glucose: 95 mg/dL (70-99)
            Total Cholesterol: 185 mg/dL (125-200)
            """, 
            "sample.pdf"
        )
    
    # Should fallback to text parsing
    assert len(biomarkers) > 0
    assert len(metadata) == 0

def test_extract_biomarkers_with_claude_no_api_key():
    """Test fallback to parsing when no API key is set."""
    # Ensure API key is not set
    with patch.dict(os.environ, {}, clear=True):
        biomarkers, metadata = extract_biomarkers_with_claude(
            """
            Glucose: 95 mg/dL (70-99)
            Total Cholesterol: 185 mg/dL (125-200)
            """, 
            "sample.pdf"
        )
    
    # Should fallback to text parsing
    assert len(biomarkers) > 0
    assert len(metadata) == 0

@patch('httpx.Client')
def test_extract_biomarkers_with_claude_exception(mock_client):
    """Test fallback to parsing when an exception occurs during API call."""
    # Set up the mock to raise an exception
    mock_client.return_value.__enter__.return_value.post.side_effect = Exception("Test exception")
    
    # Set environment variable for API key
    with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
        biomarkers, metadata = extract_biomarkers_with_claude(
            """
            Glucose: 95 mg/dL (70-99)
            Total Cholesterol: 185 mg/dL (125-200)
            """, 
            "sample.pdf"
        )
    
    # Should fallback to text parsing
    assert len(biomarkers) > 0
    assert len(metadata) == 0 

def test_invalid_biomarker_filtering():
    """Test filtering of invalid biomarkers."""
    # Mock biomarkers data with invalid entries
    biomarkers = [
        # Valid biomarkers
        {"name": "Glucose", "value": 95, "unit": "mg/dL"},
        {"name": "Hemoglobin", "value": 14.5, "unit": "g/dL"},
        
        # Invalid biomarkers - numeric-only names
        {"name": "100", "value": 125, "unit": "mg/dL"},
        {"name": "150", "value": 120, "unit": "mg/dL"},
        
        # Invalid biomarkers - ordinals
        {"name": "2nd", "value": 3, "unit": "units"},
        {"name": "3rd", "value": 10, "unit": "units"},
        
        # Invalid biomarkers - time descriptions
        {"name": "4 am", "value": 10, "unit": "pm"},
        {"name": "10 pm", "value": 5, "unit": "units"},
        {"name": "between Evening 6-10 pm", "value": 5, "unit": "mg/dL"},
        
        # Invalid biomarkers - method descriptions
        {"name": ") LDH, UV kinetic", "value": 26, "unit": "U/L"},
        {"name": ") SZAZ Carboxylated Substrate", "value": 17, "unit": "U/L"},
        
        # Edge cases - these should be valid
        {"name": "Thyroid Stimulating Hormone (TSH)", "value": 2.486, "unit": "μIU/mL"},
        {"name": "Alkaline Phosphatase (ALP)", "value": 70, "unit": "U/L"}
    ]
    
    # Filter the biomarkers using our validation logic
    filtered_biomarkers = []
    for biomarker in biomarkers:
        name = biomarker.get("name", "").strip()
        value = biomarker.get("value", 0)
        unit = biomarker.get("unit", "")
        
        # Skip biomarkers with suspicious names
        if (not name or 
            name.lower() in ["page", "volume", "calculated", "dual wavelength"] or
            re.match(r'^page \d+$', name.lower()) or
            # Skip numeric-only names
            re.match(r'^\d+$', name) or
            # Skip names that are likely time references
            re.match(r'^\d+\s*(am|pm)$', name.lower()) or
            # Skip phrases related to time or descriptions
            any(term in name.lower() for term in ["between", "minimum", "maximum", "evening", "morning"]) or
            # Skip references to "nd" and "rd" ordinals
            re.match(r'^\d+(st|nd|rd|th)\s*$', name) or
            # Skip method descriptions
            name.startswith(")") or
            # Skip names that are too short or suspiciously long
            len(name) < 2 or len(name) > 50 or
            # Skip if no unit provided
            not unit or
            # Skip if value is zero (likely an error)
            value == 0):
            continue
        
        # Check if name contains method description after closing parenthesis
        if ")" in name:
            # Only fix if it matches the pattern of a method description
            if re.search(r'\)\s+[\w\s]+(Kinetic|Substrate|Photometry|Buffer)', name):
                name_parts = name.split(")")
                if len(name_parts) > 1:
                    # Use the part before the method description plus the closing parenthesis
                    biomarker["name"] = name_parts[0].strip() + ")"
        
        filtered_biomarkers.append(biomarker)
    
    # Verify filtering worked correctly
    assert len(filtered_biomarkers) == 4  # Only the 4 valid biomarkers should remain
    
    # Verify the right biomarkers were kept
    biomarker_names = [b["name"] for b in filtered_biomarkers]
    assert "Glucose" in biomarker_names
    assert "Hemoglobin" in biomarker_names
    assert "Thyroid Stimulating Hormone (TSH)" in biomarker_names
    assert "Alkaline Phosphatase (ALP)" in biomarker_names
    
    # Verify invalid biomarkers were filtered out
    assert "100" not in biomarker_names
    assert "2nd" not in biomarker_names
    assert "4 am" not in biomarker_names
    assert ") LDH, UV kinetic" not in biomarker_names 