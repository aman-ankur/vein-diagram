"""
Biomarker Parser Service

This module provides services for parsing biomarker data from lab reports using
Claude API and standardizing the extracted data using the biomarker dictionary.
"""
import json
import re
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
import httpx
from datetime import datetime

from app.services.biomarker_dictionary import (
    get_standardized_biomarker_name,
    convert_to_standard_unit,
    get_biomarker_category,
    get_reference_range,
    BIOMARKER_DICT
)

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set up a file handler to also log to a file
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'biomarker_parser.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
logger.addHandler(file_handler)

# Set debug level to enable all logging messages
logger.setLevel(logging.DEBUG)

# Load Claude API key from environment variable
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "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")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Set this to True to save all Claude API requests and responses for debugging
SAVE_CLAUDE_RESPONSES = True

# Dictionary of common biomarker aliases for robust matching
BIOMARKER_ALIASES = {
    "glucose": ["blood glucose", "fasting glucose", "plasma glucose", "gluc", "glu"],
    "hemoglobin a1c": ["hba1c", "a1c", "glycated hemoglobin", "glycosylated hemoglobin", "hemoglobin a1c"],
    "total cholesterol": ["cholesterol", "tc", "total chol", "chol, total"],
    "hdl cholesterol": ["hdl", "hdl-c", "high density lipoprotein", "good cholesterol"],
    "ldl cholesterol": ["ldl", "ldl-c", "low density lipoprotein", "bad cholesterol"],
    "triglycerides": ["tg", "trigs", "triglyceride"],
    "tsh": ["thyroid stimulating hormone", "thyrotropin", "thyroid function"],
    "free t4": ["ft4", "thyroxine", "free thyroxine"],
    "free t3": ["ft3", "triiodothyronine", "free triiodothyronine"],
    "vitamin d": ["25-hydroxyvitamin d", "25-oh vitamin d", "vitamin d, 25-hydroxy", "vit d"],
    "vitamin b12": ["b12", "cobalamin", "vit b12"],
    "ferritin": ["ferr", "serum ferritin"],
    "iron": ["fe", "serum iron"],
    "transferrin": ["tf", "trf"],
    "tibc": ["total iron binding capacity"],
    "creatinine": ["creat", "cr", "serum creatinine"],
    "bun": ["blood urea nitrogen", "urea nitrogen"],
    "egfr": ["estimated glomerular filtration rate", "gfr"],
    "alt": ["alanine aminotransferase", "sgpt"],
    "ast": ["aspartate aminotransferase", "sgot"],
    "alkaline phosphatase": ["alp", "alk phos"],
    "total bilirubin": ["tbili", "bilirubin total"],
    "albumin": ["alb", "serum albumin"],
    "total protein": ["tp", "protein, total"],
    "sodium": ["na", "na+", "serum sodium"],
    "potassium": ["k", "k+", "serum potassium"],
    "chloride": ["cl", "cl-", "serum chloride"],
    "bicarbonate": ["hco3", "hco3-", "co2", "carbon dioxide"],
    "calcium": ["ca", "ca2+", "serum calcium"],
    "magnesium": ["mg", "mg2+", "serum magnesium"],
    "phosphorus": ["p", "phos", "phosphate", "serum phosphorus"],
    "uric acid": ["ua", "serum uric acid"],
    "hemoglobin": ["hgb", "hb", "hg"],
    "hematocrit": ["hct", "ht"],
    "wbc": ["white blood cell count", "white blood cells", "leukocytes"],
    "platelet count": ["plt", "platelets"],
    "mch": ["mean corpuscular hemoglobin"],
    "mchc": ["mean corpuscular hemoglobin concentration"],
    "mcv": ["mean corpuscular volume"],
    "rdw": ["red cell distribution width"],
    "neutrophils": ["neut", "neutrophil count", "polys"],
    "lymphocytes": ["lymphs", "lymphocyte count"],
    "monocytes": ["mono", "monocyte count"],
    "eosinophils": ["eos", "eosinophil count"],
    "basophils": ["baso", "basophil count"],
    "psa": ["prostate specific antigen"],
    "c-reactive protein": ["crp", "c reactive protein"],
    "esr": ["erythrocyte sedimentation rate", "sed rate"],
    "homocysteine": ["hcy"],
    "cortisol": ["cort", "serum cortisol"],
    "testosterone": ["test", "total testosterone"],
    "estradiol": ["e2"],
    "progesterone": ["prog"],
    "dhea-s": ["dehydroepiandrosterone sulfate"],
    "folate": ["folic acid"],
    "hla-b27": ["human leukocyte antigen b27"],
    "ana": ["antinuclear antibody"],
    "rf": ["rheumatoid factor"],
    "tpo antibodies": ["thyroid peroxidase antibodies", "anti-tpo", "thyroid antibodies"],
}

def extract_biomarkers_with_claude(text: str, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract biomarkers from text using Claude API.
    
    Args:
        text (str): The text extracted from a PDF
        filename (str): The filename of the PDF for context
        
    Returns:
        Tuple containing:
        - List of biomarker data dictionaries
        - Dictionary of metadata about the lab report
    """
    logger.info(f"[BIOMARKER_EXTRACTION_START] Extracting biomarkers from {filename} (text length: {len(text)} chars)")
    start_time = datetime.now()
    
    # Check if API key is available
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    api_key = "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"

    if not api_key:
        logger.warning("[API_KEY_MISSING] ANTHROPIC_API_KEY environment variable not found. Using fallback parser.")
        fallback_results = parse_biomarkers_from_text(text)
        logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers")
        return fallback_results, {}
    
    # Preprocess the text to make it more Claude-friendly
    text = _preprocess_text_for_claude(text)
    
    # Log that we're using Claude API
    logger.info("[USING_CLAUDE_API] Using Claude API for biomarker extraction")
    
    # Enhanced system prompt for Claude with more specific instructions
    system_prompt = """
    You are a specialized medical data extraction API that outputs VALID JSON ONLY.

    Your task is to extract biomarker data from clinical lab reports and format them in a strict JSON format.
    
    EXTREMELY IMPORTANT: Your response MUST be a single, valid JSON object with no explanatory text before or after. Do not use markdown formatting.
    
    Extract ONLY legitimate clinical biomarkers. DO NOT extract page numbers, headers, section titles, or any text that is not an actual biomarker test result.
    
    For each biomarker, extract:
    1. The standardized biomarker name (e.g., "Glucose" not "GLU")
    2. The numeric value (convert to a number, e.g., 95.0)
    3. The unit of measurement (e.g., "mg/dL")
    4. The reference range

    Common legitimate biomarkers include:
    - Blood chemistry (glucose, BUN, creatinine, electrolytes, liver enzymes, etc.)
    - Complete blood count (CBC) components (WBC, RBC, hemoglobin, etc.)
    - Lipid panels (cholesterol, triglycerides, HDL, LDL)
    - Hormone tests (TSH, T3, T4, testosterone, etc.)
    - Vitamins and minerals (vitamin D, B12, ferritin, iron, etc.)
    
    Do NOT extract as biomarkers:
    - Page numbers (e.g., "Page 2/12")
    - Headers or titles
    - Lab methods or techniques
    - Patient information
    - Collection dates
    - Doctor names

    RESPONSE FORMAT - YOUR RESPONSE MUST BE ONLY THIS JSON OBJECT:

    {
      "biomarkers": [
        {
          "name": "Glucose",
          "original_name": "Glucose, Fasting",
          "value": 95.0,
          "original_value": "95",
          "unit": "mg/dL",
          "original_unit": "mg/dL",
          "reference_range": "70-99 mg/dL",
          "category": "Metabolic",
          "flag": null,
          "confidence": 0.95
        },
        {
          "name": "Hemoglobin A1C",
          "original_name": "HbA1c",
          "value": 5.4,
          "original_value": "5.4",
          "unit": "%",
          "original_unit": "%",
          "reference_range": "4.0-5.6",
          "category": "Metabolic",
          "flag": null,
          "confidence": 0.98
        }
      ],
      "metadata": {
        "lab_name": "LabCorp",
        "report_date": "03/15/2025",
        "patient_name": "John Smith",
        "patient_id": "12345678",
        "patient_age": 45,
        "patient_gender": "Male"
      }
    }
    
    CRITICAL JSON FORMATTING RULES:
    1. Use double quotes for all keys and string values
    2. Use null (not "null") for missing values
    3. Use numbers without quotes for numeric values
    4. Do not use trailing commas (e.g., [1, 2, ] is invalid)
    5. Your output MUST be valid JSON that can be parsed by standard JSON parsers
    6. Do not include ANY explanatory text, markdown formatting, or code blocks outside the JSON object
    7. Ensure all opening braces, brackets, and quotes are properly closed
    8. Do not include comments in the JSON

    Remember, you are acting as an API that returns ONLY JSON. No preamble, no explanations, just the JSON object.
    """
    
    # Create the prompt for Claude
    user_prompt = f"""
    Please extract all biomarker data from this lab report, following the format and rules I've specified.
    
    ===== LAB REPORT TEXT =====
    {text}
    ===== END LAB REPORT TEXT =====
    
    Extract ONLY the biomarker data in valid JSON format. Do not include any explanatory text outside the JSON structure.
    """
    
    # Save prompt to debug file
    debug_prompt_path = os.path.join(log_dir, f"claude_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    with open(debug_prompt_path, "w") as f:
        f.write(f"SYSTEM PROMPT:\n{system_prompt}\n\nUSER PROMPT:\n{user_prompt}")
    logger.debug(f"[CLAUDE_PROMPT_SAVED] Claude prompt saved to {debug_prompt_path}")
    
    # Prepare the API request
    request_body = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0
    }
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    logger.info(f"[CLAUDE_REQUEST] Sending request to Claude API for {filename}")
    logger.debug(f"[CLAUDE_REQUEST_DETAILS] Using model: {request_body['model']}, max_tokens: {request_body['max_tokens']}")
    
    try:
        # Make the API request
        request_start_time = datetime.now()
        with httpx.Client(timeout=90.0) as client:  # Increased timeout to 90 seconds
            try:
                response = client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=request_body,
                    headers=headers
                )
                request_duration = (datetime.now() - request_start_time).total_seconds()
                logger.info(f"[API_REQUEST_DURATION] Claude API request took {request_duration:.2f} seconds")
            except httpx.TimeoutException:
                logger.error(f"[API_TIMEOUT] Claude API request timed out after {(datetime.now() - request_start_time).total_seconds():.2f} seconds")
                fallback_results = parse_biomarkers_from_text(text)
                logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers after timeout")
                return fallback_results, {}
            except Exception as request_error:
                logger.error(f"[API_REQUEST_ERROR] Error during Claude API request: {str(request_error)}")
                fallback_results = parse_biomarkers_from_text(text)
                logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers after request error")
                return fallback_results, {}
        
        # Check if the request was successful
        if response.status_code == 200:
            logger.info(f"[API_SUCCESS] Successfully received response from Claude API for {filename}")
            response_data = response.json()
            
            # Save the raw response for debugging
            debug_response_path = os.path.join(log_dir, f"claude_response_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            with open(debug_response_path, "w") as f:
                json.dump(response_data, f, indent=2)
            logger.debug(f"[CLAUDE_RAW_RESPONSE_SAVED] Raw Claude response saved to {debug_response_path}")
            
            # Extract the content from the response
            content = response_data.get("content", [])
            text_content = ""
            for item in content:
                if item.get("type") == "text":
                    text_content = item.get("text", "")
                    break
            
            # Save the text content separately for easier debugging
            debug_text_path = os.path.join(log_dir, f"claude_text_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            try:
                with open(debug_text_path, "w") as f:
                    f.write(text_content)
                logger.debug(f"[CLAUDE_TEXT_RESPONSE_SAVED] Claude text response saved to {debug_text_path}")
            except Exception as e:
                logger.error(f"[FALLBACK_TEXT_SAVE_ERROR] Could not save fallback text: {str(e)}")
            
            # Log detailed information about the response content
            logger.debug(f"[API_RESPONSE_LENGTH] Total response length: {len(text_content)} characters")
            logger.debug(f"[API_RESPONSE_PREVIEW] First 1000 chars of response: {text_content[:1000]}...")
            logger.debug(f"[API_RESPONSE_PREVIEW_END] Last 1000 chars of response: {text_content[-1000:]}...")
            
            # Log the full response for debugging
            logger.info(f"[API_FULL_RESPONSE] FULL CLAUDE RESPONSE: {text_content}")
            
            # Check for JSON-like structure in the response
            if '{' not in text_content or '}' not in text_content:
                logger.error("[API_RESPONSE_ERROR] Response doesn't contain JSON structure (no braces found)")
                logger.error(f"[API_RESPONSE_FULL] Full response: {text_content}")
                logger.info("[FALLBACK_TO_TEXT_PARSER] Using fallback parser due to missing JSON structure")
                fallback_results = parse_biomarkers_from_text(text)
                logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers")
                return fallback_results, {}
            
            # Extract JSON using regex - Find everything between the first { and the last }
            json_pattern = r'(\{.*\})'
            json_match = re.search(json_pattern, text_content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                logger.debug(f"[JSON_EXTRACTION] Found JSON pattern in response with length {len(json_str)}")
                
                # Save the extracted JSON for debugging
                debug_extracted_json_path = os.path.join(log_dir, f"extracted_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(debug_extracted_json_path, "w") as f:
                    f.write(json_str)
                logger.debug(f"[EXTRACTED_JSON_SAVED] Extracted JSON saved to {debug_extracted_json_path}")
                
                # Try to repair the JSON if needed
                repaired_json = _repair_json(json_str)
                
                # Save the repaired JSON for comparison
                debug_repaired_json_path = os.path.join(log_dir, f"repaired_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                with open(debug_repaired_json_path, "w") as f:
                    f.write(repaired_json)
                logger.debug(f"[REPAIRED_JSON_SAVED] Repaired JSON saved to {debug_repaired_json_path}")
                
                try:
                    # First try parsing the repaired JSON
                    json_start_time = datetime.now()
                    extraction_data = json.loads(repaired_json)
                    json_duration = (datetime.now() - json_start_time).total_seconds()
                    logger.debug(f"[JSON_PARSING] JSON parsing took {json_duration:.2f} seconds")
                    
                    biomarkers = extraction_data.get("biomarkers", [])
                    metadata = extraction_data.get("metadata", {})
                    
                    logger.info(f"[BIOMARKERS_FOUND] Extracted {len(biomarkers)} biomarkers from {filename}")
                    
                    # Log full data for debugging
                    debug_json_path = os.path.join(log_dir, f"extracted_biomarkers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                    try:
                        with open(debug_json_path, "w") as f:
                            json.dump(extraction_data, f, indent=2)
                        logger.debug(f"[EXTRACTED_DATA_SAVED] Biomarker data saved to {debug_json_path}")
                    except Exception as e:
                        logger.error(f"[DATA_SAVE_ERROR] Could not save extracted data: {str(e)}")
                    
                    # Log metadata for debugging
                    logger.debug(f"[METADATA] Extracted metadata: {json.dumps(metadata)}")
                    
                    # If no biomarkers were found, log warning and continue with fallback
                    if not biomarkers:
                        logger.warning(f"[NO_BIOMARKERS] No biomarkers found in Claude API response")
                        logger.info("[FALLBACK_TO_TEXT_PARSER] Using fallback parser due to empty biomarkers list")
                        fallback_results = parse_biomarkers_from_text(text)
                        logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers")
                        return fallback_results, metadata
                    
                    # Filter out invalid biomarkers
                    filtered_biomarkers = []
                    for biomarker in biomarkers:
                        name = biomarker.get("name", "").strip()
                        # Skip biomarkers with suspicious names (page numbers, etc.)
                        if (not name or 
                            name.lower() in ["page", "volume", "calculated", "dual wavelength"] or
                            re.match(r'^page \d+$', name.lower())):
                            logger.warning(f"[INVALID_BIOMARKER] Skipping invalid biomarker: {name}")
                            continue
                        filtered_biomarkers.append(biomarker)
                    
                    logger.info(f"[FILTERED_BIOMARKERS] Filtered out {len(biomarkers) - len(filtered_biomarkers)} invalid biomarkers")
                    
                    # Process the biomarkers to standardize format
                    processing_start_time = datetime.now()
                    processed_biomarkers = []
                    for i, biomarker in enumerate(filtered_biomarkers):
                        try:
                            # Process and standardize the biomarker data
                            processed_biomarker = _process_biomarker(biomarker)
                            processed_biomarkers.append(processed_biomarker)
                        except Exception as e:
                            logger.error(f"[BIOMARKER_PROCESSING_ERROR] Error processing biomarker {i}: {str(e)}")
                            logger.error(f"[BIOMARKER_DATA] Problem biomarker data: {json.dumps(biomarker)}")
                    
                    processing_duration = (datetime.now() - processing_start_time).total_seconds()
                    logger.debug(f"[BIOMARKER_PROCESSING] Processing {len(filtered_biomarkers)} biomarkers took {processing_duration:.2f} seconds")
                    
                    total_duration = (datetime.now() - start_time).total_seconds()
                    logger.info(f"[BIOMARKER_EXTRACTION_COMPLETE] Total extraction took {total_duration:.2f} seconds")
                    
                    # If we have no valid biomarkers, try the fallback parser
                    if not processed_biomarkers:
                        logger.warning("[NO_VALID_BIOMARKERS] No valid biomarkers found in Claude response. Using fallback parser.")
                        fallback_results = parse_biomarkers_from_text(text)
                        logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers")
                        return fallback_results, {}
                    
                    return processed_biomarkers, metadata
                    
                except json.JSONDecodeError as e:
                    logger.error(f"[JSON_DECODE_ERROR] Error parsing JSON from Claude API response: {str(e)}")
                    logger.debug(f"[JSON_CONTENT_PREVIEW] Response content preview: {json_str[:500]}...")
                    
                    # Instead of immediately falling back to text parser, try the simplified Claude API approach
                    logger.info("[CLAUDE_FALLBACK_ATTEMPT] Trying fallback Claude API call with simpler prompt")
                    return _retry_claude_with_simpler_prompt(text, filename, api_key)
            else:
                logger.error("[JSON_MISSING] No JSON found in Claude API response")
                logger.debug(f"[RESPONSE_PREVIEW] Content preview: {text_content[:500]}...")
                
                # Try the fallback Claude API approach
                logger.info("[CLAUDE_FALLBACK_ATTEMPT] Trying fallback Claude API call with simpler prompt")
                return _retry_claude_with_simpler_prompt(text, filename, api_key)
        else:
            logger.error(f"[API_ERROR] Claude API request failed with status {response.status_code}: {response.text[:200]}")
            # Use fallback parsing if API call fails
            logger.info("[FALLBACK_TO_TEXT_PARSER] Using fallback parser due to API error")
            fallback_results = parse_biomarkers_from_text(text)
            logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers")
            return fallback_results, {}
            
    except Exception as e:
        logger.error(f"[API_EXCEPTION] Error calling Claude API: {str(e)}")
        # Use fallback parsing if there's an exception
        logger.info("[FALLBACK_TO_TEXT_PARSER] Using fallback parser due to exception")
        fallback_results = parse_biomarkers_from_text(text)
        logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers")
        return fallback_results, {}

def _process_biomarker(biomarker: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process and standardize a biomarker data dictionary.
    
    Args:
        biomarker: Dictionary containing biomarker data
        
    Returns:
        Processed biomarker dictionary
    """
    try:
        # Extract basic information
        name = biomarker.get("name", "")
        original_name = biomarker.get("original_name", name)
        
        logger.debug(f"[PROCESSING_BIOMARKER] Processing biomarker: {name} (original: {original_name})")
        
        # Original and standardized value
        original_value = biomarker.get("original_value", str(biomarker.get("value", "")))
        
        # Convert value to float if possible
        value_str = str(biomarker.get("value", original_value))
        try:
            # Handle empty values gracefully
            if not value_str or value_str.strip() == '':
                logger.warning(f"[EMPTY_VALUE] Empty value for biomarker '{name}', setting to 0.0")
                value = 0.0
            else:
                # Remove commas and other non-numeric characters
                value_str = re.sub(r'[^\d.\-]', '', value_str)
                value = float(value_str)
        except ValueError:
            # If conversion fails, default to 0.0 and log a warning
            logger.warning(f"[VALUE_CONVERSION_ERROR] Could not convert value '{value_str}' to float for biomarker '{name}'")
            value = 0.0
        
        # Original and standardized unit
        original_unit = biomarker.get("original_unit", biomarker.get("unit", ""))
        unit = standardize_unit(biomarker.get("unit", original_unit))
        
        logger.debug(f"[BIOMARKER_UNIT] '{name}' unit: {unit} (original: {original_unit})")
        
        # Parse reference range
        reference_range_text = biomarker.get("reference_range", "")
        reference_range_low, reference_range_high, reference_range_text = parse_reference_range(reference_range_text)
        
        logger.debug(f"[REFERENCE_RANGE] '{name}' reference range: low={reference_range_low}, high={reference_range_high}, text='{reference_range_text}'")
        
        # Category
        category = biomarker.get("category", "Other")
        if category == "Other":
            # Try to categorize based on name if not provided
            inferred_category = categorize_biomarker(name)
            if inferred_category != "Other":
                logger.debug(f"[CATEGORY_INFERENCE] Inferred category for '{name}': {inferred_category}")
                category = inferred_category
        
        # Abnormal flag
        flag = biomarker.get("flag", "")
        
        # Determine if the value is abnormal
        is_abnormal = False
        
        # Use flag if available
        if flag and flag.strip().upper() in ["H", "L", "A", "HIGH", "LOW", "ABNORMAL"]:
            is_abnormal = True
            logger.debug(f"[ABNORMAL_FLAG] '{name}' marked abnormal based on flag: {flag}")
        elif reference_range_low is not None or reference_range_high is not None:
            # Compare value to reference range
            if reference_range_low is not None and value < reference_range_low:
                is_abnormal = True
                logger.debug(f"[ABNORMAL_LOW] '{name}' value {value} is below reference range {reference_range_low}")
            elif reference_range_high is not None and value > reference_range_high:
                is_abnormal = True
                logger.debug(f"[ABNORMAL_HIGH] '{name}' value {value} is above reference range {reference_range_high}")
        
        # Construct and return the processed biomarker
        processed_biomarker = {
            "name": name,
            "original_name": original_name,
            "value": value,
            "original_value": original_value,
            "unit": unit,
            "original_unit": original_unit,
            "reference_range_low": reference_range_low,
            "reference_range_high": reference_range_high,
            "reference_range_text": reference_range_text,
            "category": category,
            "is_abnormal": is_abnormal,
            "confidence": biomarker.get("confidence", 0.8)  # Default to 0.8 if not provided
        }
        
        # Add any additional fields from the original biomarker
        for key, value in biomarker.items():
            if key not in processed_biomarker and key not in ["flag", "reference_range"]:
                processed_biomarker[key] = value
        
        return processed_biomarker
        
    except Exception as e:
        logger.error(f"[BIOMARKER_PROCESSING_ERROR] Error processing biomarker: {str(e)}")
        logger.error(f"[PROBLEMATIC_BIOMARKER] {json.dumps(biomarker)}")
        # Return a minimal valid biomarker to avoid breaking the flow
        return {
            "name": biomarker.get("name", "Unknown Biomarker"),
            "original_name": biomarker.get("original_name", biomarker.get("name", "Unknown Biomarker")),
            "value": 0.0,
            "original_value": str(biomarker.get("value", "")),
            "unit": standardize_unit(biomarker.get("unit", biomarker.get("original_unit", "-"))),
            "original_unit": biomarker.get("original_unit", biomarker.get("unit", "-")),
            "category": "Other",
            "is_abnormal": False,
            "reference_range_text": biomarker.get("reference_range", ""),
            "confidence": 0.1  # Very low confidence for error cases
        }

def parse_biomarkers_from_text(text: str) -> List[Dict[str, Any]]:
    """
    Fallback method to parse biomarkers from text using pattern matching.
    This is used when the Claude API is unavailable or returns an error.
    
    Args:
        text: The text to parse
        
    Returns:
        List of biomarker data dictionaries
    """
    logger.info("[FALLBACK_PARSER_START] Using fallback parser to extract biomarkers from text")
    start_time = datetime.now()
    
    biomarkers = []
    
    # List of known invalid biomarker names (typically section headers, page info, etc.)
    invalid_names = [
        "page", "volume", "test", "result", "date", "name", "patient", "doctor", "method",
        "calculated", "dual wavelength", "technique", "column", "row", "title", "header",
        "footer", "report", "lab", "laboratory", "collection", "time", "specimen", "sample",
        "id", "number", "visit", "date", "collected on", "received on", "reported on",
        "less than", "more than", "type", "age", "sex", "gender", "client"
    ]
    
    # Patterns for common lab test formats
    # Pattern 1: Name, Value, Unit, Reference Range (common format)
    # Example: Glucose: 95 mg/dL (70-99)
    pattern1 = r'([A-Za-z0-9, \-\(\)]+?)[\s:]+([0-9\.\,<>]+)[\s]*([A-Za-z\/%]+)[\s\(]*([0-9\.<>\-]+[^\)]*)?'
    
    # Pattern 2: Name followed by Value with Unit (no reference range)
    # Example: Glucose 95 mg/dL
    pattern2 = r'([A-Za-z0-9, \-\(\)]+?)[\s]+([0-9\.\,<>]+)[\s]*([A-Za-z\/%]+)'
    
    # Apply patterns to find matches
    logger.debug("[PATTERN_MATCHING] Applying pattern matching to extract biomarkers")
    
    # Track processed biomarkers to avoid duplicates
    processed_names = set()
    
    # Process by pattern 1 (most specific)
    matches1 = re.finditer(pattern1, text)
    match_count = 0
    for match in matches1:
        match_count += 1
        try:
            name, value_str, unit, ref_range = match.groups()
            name = name.strip()
            
            logger.debug(f"[PATTERN1_MATCH] Found potential match: '{name}': {value_str} {unit}, ref: {ref_range}")
            
            # Check against list of invalid names
            name_lower = name.lower()
            if any(invalid in name_lower for invalid in invalid_names):
                logger.debug(f"[INVALID_NAME] Skipping invalid biomarker name: {name}")
                continue
                
            # Skip if already processed or if name looks like a header
            if name_lower in processed_names or len(name) > 40 or len(name) < 2:
                continue
                
            processed_names.add(name_lower)
            
            # Clean and convert value
            value_str = re.sub(r'[^\d.\-]', '', value_str)
            try:
                value = float(value_str)
            except ValueError:
                logger.warning(f"Could not convert value '{value_str}' to float for biomarker '{name}'")
                continue
                
            # Parse reference range if available
            ref_low, ref_high, ref_text = parse_reference_range(ref_range) if ref_range else (None, None, "")
            
            # Categorize biomarker
            category = categorize_biomarker(name)
            
            # Build biomarker data
            biomarker = {
                "name": name,
                "original_name": name,
                "original_value": value_str,
                "value": value,
                "original_unit": unit,
                "unit": standardize_unit(unit),
                "reference_range_low": ref_low,
                "reference_range_high": ref_high,
                "reference_range_text": ref_text,
                "category": category,
                "is_abnormal": False,  # Can't determine from text easily
                "confidence": 0.7      # Lower confidence for the fallback parser
            }
            
            biomarkers.append(biomarker)
        except Exception as e:
            logger.error(f"[PATTERN1_ERROR] Error processing match in fallback parser: {str(e)}")
    
    logger.debug(f"[PATTERN1_RESULTS] Processed {match_count} matches from pattern 1, found {len(biomarkers)} valid biomarkers")
    
    # Apply pattern 2 if needed (less specific)
    if len(biomarkers) < 5:
        logger.debug("Applying secondary pattern to find more biomarkers")
        matches2 = re.finditer(pattern2, text)
        for match in matches2:
            try:
                name, value_str, unit = match.groups()
                name = name.strip()
                
                # Check against list of invalid names
                name_lower = name.lower()
                if any(invalid in name_lower for invalid in invalid_names):
                    logger.debug(f"[INVALID_NAME] Skipping invalid biomarker name: {name}")
                    continue
                    
                # Skip if already processed or name looks like a header
                if name_lower in processed_names or len(name) > 40 or len(name) < 2:
                    continue
                    
                processed_names.add(name_lower)
                
                # Clean and convert value
                value_str = re.sub(r'[^\d.\-]', '', value_str)
                try:
                    value = float(value_str)
                except ValueError:
                    continue
                    
                # Categorize biomarker
                category = categorize_biomarker(name)
                
                # Build biomarker data
                biomarker = {
                    "name": name,
                    "original_name": name,
                    "original_value": value_str,
                    "value": value,
                    "original_unit": unit,
                    "unit": standardize_unit(unit),
                    "category": category,
                    "is_abnormal": False,
                    "confidence": 0.5  # Lower confidence for less specific match
                }
                
                biomarkers.append(biomarker)
            except Exception as e:
                logger.error(f"Error processing secondary match in fallback parser: {str(e)}")
    
    logger.info(f"[FALLBACK_PARSER_COMPLETE] Fallback parser found {len(biomarkers)} biomarkers in {(datetime.now() - start_time).total_seconds():.2f} seconds")
    return biomarkers

def categorize_biomarker(name: str) -> str:
    """
    Categorize a biomarker based on its name.
    
    Args:
        name: Name of the biomarker
        
    Returns:
        Category string
    """
    name_lower = name.lower()
    
    # Lipid panel
    if any(term in name_lower for term in ["cholesterol", "ldl", "hdl", "triglyceride"]):
        return "Lipid"
        
    # Metabolic
    if any(term in name_lower for term in ["glucose", "a1c", "insulin", "hba1c"]):
        return "Metabolic"
        
    # Thyroid
    if any(term in name_lower for term in ["tsh", "t3", "t4", "thyroid"]):
        return "Hormone"
        
    # Vitamins
    if any(term in name_lower for term in ["vitamin", "folate", "b12"]):
        return "Vitamin"
        
    # Minerals
    if any(term in name_lower for term in ["iron", "ferritin", "magnesium", "calcium", "sodium", "potassium"]):
        return "Mineral"
        
    # Blood count
    if any(term in name_lower for term in ["hemoglobin", "hematocrit", "wbc", "rbc", "platelet"]):
        return "Blood"
        
    # Liver function
    if any(term in name_lower for term in ["alt", "ast", "alp", "bilirubin", "albumin"]):
        return "Liver"
        
    # Kidney function
    if any(term in name_lower for term in ["creatinine", "egfr", "bun"]):
        return "Kidney"
        
    # Default category
    return "Other"

def standardize_unit(unit: str) -> str:
    """
    Standardize the unit to a common format.
    
    Args:
        unit: The unit to standardize
        
    Returns:
        Standardized unit string
    """
    if not unit:
        return "-"  # Default placeholder for empty units
        
    # Remove extra spaces
    unit = unit.strip()
    
    # Standardize common variations
    unit_lower = unit.lower()
    
    # Standardize mg/dL
    if unit_lower in ["mg/dl", "mg / dl", "mg/deciliter", "mg per dl", "mg per deciliter"]:
        return "mg/dL"
        
    # Standardize g/dL
    if unit_lower in ["g/dl", "g / dl", "g/deciliter", "g per dl", "g per deciliter"]:
        return "g/dL"
        
    # Standardize percentage
    if unit_lower in ["percent", "percentage", "pct", "pct."]:
        return "%"
        
    # Standardize mmol/L
    if unit_lower in ["mmol/l", "mmol / l", "millimol/l", "millimoles/l"]:
        return "mmol/L"
        
    # Standardize U/L (units per liter)
    if unit_lower in ["u/l", "units/l", "u / l", "iu/l"]:
        return "U/L"
        
    # Standardize common microunit notation
    if unit_lower in ["mcg/ml", "mcg/dl", "mcg/l"]:
        unit = unit.replace("mcg", "μg")
        return unit.replace("mc", "μ").replace("/dl", "/dL").replace("/ml", "/mL").replace("/l", "/L")
        
    # Keep original but standardize common case
    return unit.replace("/dl", "/dL").replace("/ml", "/mL").replace("/l", "/L")

def parse_reference_range(range_text: str) -> Tuple[Optional[float], Optional[float], str]:
    """
    Parse a reference range string to extract low and high values.
    
    Args:
        range_text: The reference range text (e.g., "70-99", "< 200", "> 40")
        
    Returns:
        Tuple containing:
        - Low value (or None if not available)
        - High value (or None if not available)
        - Original reference range text
    """
    if not range_text:
        return None, None, ""
        
    # Clean the range text
    range_text = range_text.strip()
    
    # Handle different formats
    
    # Format: "X-Y" (range)
    if "-" in range_text and not ("<" in range_text or ">" in range_text):
        try:
            parts = range_text.split("-")
            low = float(parts[0].strip())
            high = float(parts[1].strip())
            return low, high, range_text
        except (ValueError, IndexError):
            pass
    
    # Format: "< X" or "≤ X" (less than)
    if "<" in range_text or "≤" in range_text:
        try:
            num_str = re.search(r'[<≤]\s*(\d+\.?\d*)', range_text)
            if num_str:
                high = float(num_str.group(1))
                return None, high, range_text
        except (ValueError, AttributeError):
            pass
    
    # Format: "> X" or "≥ X" (greater than)
    if ">" in range_text or "≥" in range_text:
        try:
            num_str = re.search(r'[>≥]\s*(\d+\.?\d*)', range_text)
            if num_str:
                low = float(num_str.group(1))
                return low, None, range_text
        except (ValueError, AttributeError):
            pass
    
    # Try to extract any numbers from the string
    numbers = re.findall(r'(\d+\.?\d*)', range_text)
    if len(numbers) == 1:
        try:
            # Assume the single number is a high value if string contains "normal <"
            # or any variation with "less than" concepts
            if any(term in range_text.lower() for term in ["<", "less than", "under", "below"]):
                return None, float(numbers[0]), range_text
            # Assume the single number is a low value if string contains "normal >"
            # or any variation with "greater than" concepts
            elif any(term in range_text.lower() for term in [">", "greater than", "above", "over"]):
                return float(numbers[0]), None, range_text
            else:
                # If unclear, use as high value (more common)
                return None, float(numbers[0]), range_text
        except ValueError:
            pass
    elif len(numbers) == 2:
        try:
            return float(numbers[0]), float(numbers[1]), range_text
        except ValueError:
            pass
    
    # If we can't parse it, return None for both values
    return None, None, range_text 

def _preprocess_text_for_claude(text: str) -> str:
    """
    Preprocess text before sending to Claude API to improve biomarker extraction.
    
    Args:
        text: The raw text extracted from PDF
        
    Returns:
        Preprocessed text
    """
    logger.debug("[TEXT_PREPROCESSING] Starting text preprocessing for Claude API")
    
    # Replace problematic characters that might cause parsing issues
    text = text.replace('\x00', '')  # Remove null bytes
    
    # Try to clean up awkward line breaks in potential biomarker data
    # Pattern: number followed by line break followed by unit
    text = re.sub(r'(\d+\.?\d*)\s*\n\s*([a-zA-Z/%]+)', r'\1 \2', text)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Format tables better
    # Replace sequences of spaces or tabs with a single tab
    text = re.sub(r' {2,}|\t+', '\t', text)
    
    # Fix potential reference range formatting
    # Pattern: (number - number) -> (number-number)
    text = re.sub(r'\((\d+\.?\d*)\s*-\s*(\d+\.?\d*)\)', r'(\1-\2)', text)
    
    logger.debug(f"[TEXT_PREPROCESSING] Completed preprocessing, new length: {len(text)} chars")
    return text 

def _repair_json(json_str: str) -> str:
    """
    Attempt to repair malformed JSON from Claude API response.
    
    Args:
        json_str: The potentially malformed JSON string
        
    Returns:
        Repaired JSON string (hopefully valid)
    """
    logger.debug(f"[JSON_REPAIR] Attempting to repair JSON of length {len(json_str)}")
    
    # Save original JSON for comparison
    original_json = json_str
    
    # Step 1: Remove any markdown code block markers
    json_str = re.sub(r'```json|```', '', json_str)
    
    # Step 2: Remove any explanatory text before or after the actual JSON
    # Find the first opening brace and last closing brace
    first_brace = json_str.find('{')
    last_brace = json_str.rfind('}')
    
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = json_str[first_brace:last_brace+1]
        logger.debug(f"[JSON_REPAIR] Trimmed to JSON boundaries: {first_brace} to {last_brace}")
    
    # Step 3: Fix common JSON syntax errors
    
    # Fix unquoted property names
    json_str = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)(\s*:)', r'\1"\2"\3', json_str)
    
    # Fix single-quoted strings to double-quoted strings (but avoid changing already valid double quotes)
    pattern = r"(?<!\\)'((?:\\.|[^\\'])*)'(?=\s*[,}\]]|$)"
    replacement = r'"\1"'
    json_str = re.sub(pattern, replacement, json_str)
    
    # Fix trailing commas in arrays and objects
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # Fix missing commas between objects in arrays
    json_str = re.sub(r'}\s*{', '},{', json_str)
    
    # Fix common JavaScript comment styles that are invalid in JSON
    json_str = re.sub(r'//.*?\n', '', json_str)
    json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)
    
    # Fix control characters
    for i in range(32):
        if i not in [9, 10, 13]:  # tab, LF, CR are allowed
            json_str = json_str.replace(chr(i), '')
    
    # Advanced fixes based on common Claude errors
    
    # Fix unclosed quotes (more aggressive approach)
    def fix_quotes(text):
        # Find strings that start with quotes but don't end with them
        lines = text.split('\n')
        for i, line in enumerate(lines):
            # Count quotes on this line
            quote_positions = [j for j, char in enumerate(line) if char == '"']
            if len(quote_positions) % 2 == 1:  # Odd number of quotes
                # Find the last quote and add another at the end if it's not followed by a comma or closing bracket
                last_quote = quote_positions[-1]
                rest_of_line = line[last_quote+1:].strip()
                if rest_of_line and rest_of_line[-1] not in [',', '}', ']']:
                    lines[i] = line + '"'
        return '\n'.join(lines)
    
    json_str = fix_quotes(json_str)
    
    # Fix missing colons in property names
    json_str = re.sub(r'("[^"]+")(?:\s+)("[^"]+"|[\d\.]+|true|false|null|{|\[)', r'\1: \2', json_str)
    
    # Ensure properties have values (if empty value, replace with null)
    json_str = re.sub(r'("[^"]+"):\s*(?=,|$)', r'\1: null', json_str)
    
    # Fix missing commas between properties
    json_str = re.sub(r'(true|false|null|"[^"]*"|\d+|\}|\])\s*("[\w\s]+"\s*:)', r'\1, \2', json_str)
    
    # Add closing brackets if needed (more advanced - count opening and closing brackets)
    def balance_brackets(text):
        opening_curly = text.count('{')
        closing_curly = text.count('}')
        opening_square = text.count('[')
        closing_square = text.count(']')
        
        # If imbalanced, try to fix
        if opening_curly > closing_curly:
            text += '}' * (opening_curly - closing_curly)
            logger.warning(f"[BRACKET_REPAIR] Added {opening_curly - closing_curly} missing closing curly braces")
        if opening_square > closing_square:
            text += ']' * (opening_square - closing_square)
            logger.warning(f"[BRACKET_REPAIR] Added {opening_square - closing_square} missing closing square brackets")
        
        return text
    
    json_str = balance_brackets(json_str)
    
    # New advanced repair: Fix objects inside arrays that are missing commas
    # Look for pattern like "}{"
    json_str = re.sub(r'\}\s*\{', '},{', json_str)
    
    # Fix specific missing commas between properties (issue seen in the logs)
    # This is to handle cases like "fidence": 0.99 } } with missing comma
    json_str = re.sub(r'(\d+|\btrue\b|\bfalse\b|\bnull\b|"[^"]*")\s*\}\s*\}', r'\1}}', json_str)
    json_str = re.sub(r'(\d+|\btrue\b|\bfalse\b|\bnull\b|"[^"]*")\s*\}\s*\]', r'\1}]', json_str)
    
    # Fix for double closing curly braces without comma (the issue in the logs)
    # This regex looks for patterns like: "confidence": 0.99 }} that should be "confidence": 0.99 }},
    json_str = re.sub(r'(\d+\s*)\}\}(\s*\])', r'\1}},\2', json_str)
    
    # Handle nested objects with missing commas (specific to the issue mentioned in logs)
    # This addresses issues like: "confidence": 0.99 }} [next object]
    json_str = re.sub(r'(\d+\s*)\}\}(\s*)(?!\s*[\],}])', r'\1}},\2', json_str)
    
    # Fix missing comma in the exact location mentioned in logs (line 386, column 6, position 10256)
    if "fidence\": 0.99" in json_str:
        # Search for the pattern and add comma if needed
        json_str = re.sub(r'(\"confidence\"\s*:\s*0\.99\s*)\}\s*\}(\s*\])', r'\1}},\2', json_str)
        logger.info("[JSON_SPECIFIC_FIX] Applied specific fix for 'confidence: 0.99' pattern")
    
    # Log changes if substantial
    if len(json_str) != len(original_json):
        logger.debug(f"[JSON_REPAIR] Length changed from {len(original_json)} to {len(json_str)} chars")
    
    # Try more desperate repair if all else fails
    try:
        json.loads(json_str)
        logger.debug("[JSON_REPAIR] Repairs successful, JSON is now valid")
    except json.JSONDecodeError as e:
        # One more desperate attempt for specific error cases
        try:
            # Get detailed information about the error
            error_msg = str(e)
            error_pos = e.pos
            error_line = e.lineno
            error_col = e.colno
            logger.warning(f"[JSON_ERROR_LOCATION] Error at line {error_line}, column {error_col}, position {error_pos}")
            
            # Get the context around the error (100 chars before and after)
            start_pos = max(0, error_pos - 100)
            end_pos = min(len(json_str), error_pos + 100)
            context = json_str[start_pos:end_pos]
            logger.warning(f"[JSON_ERROR_CONTEXT] Context: {context}")
            
            # Try to perform context-specific repairs
            if "Expecting ',' delimiter" in error_msg:
                # Insert a comma at the error position
                fixed_json = json_str[:error_pos] + ',' + json_str[error_pos:]
                logger.warning(f"[JSON_DESPERATE_FIX] Inserted comma at position {error_pos}")
                
                # Validate if fixed
                try:
                    json.loads(fixed_json)
                    logger.info("[JSON_REPAIR] Last-ditch comma fix successful!")
                    return fixed_json
                except json.JSONDecodeError as e2:
                    logger.warning(f"[JSON_DESPERATE_FIX_FAILED] Still invalid: {str(e2)}")
                    
            elif "Expecting value" in error_msg:
                # This often happens when there's a trailing comma - try removing it
                if error_pos > 0 and json_str[error_pos-1] == ',':
                    fixed_json = json_str[:error_pos-1] + json_str[error_pos:]
                    logger.warning(f"[JSON_DESPERATE_FIX] Removed trailing comma at position {error_pos-1}")
                    
                    # Validate if fixed
                    try:
                        json.loads(fixed_json)
                        logger.info("[JSON_REPAIR] Last-ditch trailing comma removal successful!")
                        return fixed_json
                    except json.JSONDecodeError as e2:
                        logger.warning(f"[JSON_DESPERATE_FIX_FAILED] Still invalid: {str(e2)}")
            
            # Last resort - use a JSON5 parser if available (more forgiving)
            try:
                import json5
                logger.warning("[JSON_REPAIR_JSON5] Attempting to parse with JSON5 (more forgiving parser)")
                parsed = json5.loads(json_str)
                # If successful, convert back to standard JSON
                fixed_json = json.dumps(parsed)
                logger.info("[JSON_REPAIR_JSON5] Successfully repaired using JSON5!")
                return fixed_json
            except ImportError:
                logger.warning("[JSON_REPAIR_JSON5] JSON5 module not available")
            except Exception as e:
                logger.warning(f"[JSON_REPAIR_JSON5_FAILED] JSON5 parsing failed: {str(e)}")
                
            # Last desperate approach - try to manually rebuild a minimal valid JSON
            # This is an extreme measure for when everything else fails
            try:
                logger.warning("[JSON_REBUILD_ATTEMPT] Attempting to rebuild a minimal valid JSON")
                
                # Find all biomarker-like structures
                biomarker_pattern = r'"name"\s*:\s*"([^"]*)".+?"value"\s*:\s*([^,}]+)'
                biomarker_matches = re.finditer(biomarker_pattern, json_str, re.DOTALL)
                
                # Rebuild a minimal valid JSON with just the essential parts
                minimal_json = '{"biomarkers": ['
                has_matches = False
                
                for i, match in enumerate(biomarker_matches):
                    if i > 0:
                        minimal_json += ','
                    has_matches = True
                    name = match.group(1)
                    value_str = match.group(2).strip()
                    # Try to extract other fields
                    unit_match = re.search(r'"unit"\s*:\s*"([^"]*)"', match.group(0))
                    unit = unit_match.group(1) if unit_match else ""
                    
                    # Create a minimal valid biomarker entry
                    minimal_json += f'{{"name": "{name}", "value": {value_str}, "unit": "{unit}"}}'
                
                minimal_json += '], "metadata": {}}'
                
                if has_matches:
                    try:
                        # Validate the minimal JSON
                        json.loads(minimal_json)
                        logger.info("[JSON_REBUILD_SUCCESS] Successfully rebuilt minimal valid JSON")
                        return minimal_json
                    except json.JSONDecodeError as e3:
                        logger.warning(f"[JSON_REBUILD_FAILED] Rebuilt JSON still invalid: {str(e3)}")
            except Exception as rebuild_error:
                logger.warning(f"[JSON_REBUILD_ERROR] Error during JSON rebuild: {str(rebuild_error)}")
        
        except Exception as desperate_error:
            logger.error(f"[JSON_DESPERATE_REPAIR_ERROR] Error during desperate JSON repair: {str(desperate_error)}")
        
        logger.warning(f"[JSON_REPAIR] Repairs attempted but JSON is still invalid: {str(e)}")
    
    # Save the repaired JSON for debugging
    try:
        debug_repaired_json_path = os.path.join(log_dir, f"repaired_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(debug_repaired_json_path, "w") as f:
            f.write(json_str)
        logger.debug(f"[REPAIRED_JSON_SAVED] Repaired JSON saved to {debug_repaired_json_path}")
    except Exception as save_error:
        logger.error(f"[SAVE_ERROR] Could not save repaired JSON: {str(save_error)}")
    
    return json_str 

def _retry_claude_with_simpler_prompt(text: str, filename: str, api_key: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Retry Claude API with a simpler prompt to extract biomarkers.
    This is a fallback approach when the main Claude API call fails to produce valid JSON.
    
    Args:
        text: The text to extract biomarkers from
        filename: The filename for context
        api_key: The Claude API key
        
    Returns:
        A tuple containing biomarkers and metadata
    """
    logger.info(f"[FALLBACK_API_CALL] Retrying Claude API with simpler prompt for {filename}")
    
    # Use a much simpler, more specific prompt to reduce the chance of parsing errors
    system_prompt = """
    You are a data extraction tool that outputs CLEAN, VALID JSON. Your entire output must be valid JSON with no other text.
    
    Extract all lab test biomarkers from the given text into this exact JSON format:
    
    {
      "biomarkers": [
        {
          "name": "Glucose",
          "value": 95,
          "unit": "mg/dL",
          "reference_range": "70-99"
        },
        {
          "name": "HbA1c",
          "value": 5.4,
          "unit": "%", 
          "reference_range": "4.0-5.6"
        }
      ]
    }
    
    Extract only valid lab test biomarkers. Exclude page numbers, headers, section titles, or non-biomarker text.
    
    IMPORTANT: Your ENTIRE response must be valid JSON with NO explanatory text, markdown formatting or codeblocks.
    ONLY the JSON object above should be returned, nothing else.
    """
    
    user_prompt = f"""
    Extract all biomarker tests from this lab report:
    
    {text}
    
    Remember: Return ONLY the JSON object with no other text or formatting.
    """
    
    # Save fallback prompt for debugging
    debug_fallback_prompt_path = os.path.join(log_dir, f"fallback_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    try:
        with open(debug_fallback_prompt_path, "w") as f:
            f.write(f"SYSTEM PROMPT:\n{system_prompt}\n\nUSER PROMPT:\n{user_prompt}")
        logger.debug(f"[FALLBACK_PROMPT_SAVED] Fallback prompt saved to {debug_fallback_prompt_path}")
    except Exception as e:
        logger.error(f"[FALLBACK_PROMPT_SAVE_ERROR] Could not save fallback prompt: {str(e)}")
    
    # Prepare the request
    request_body = {
        "model": "claude-3-sonnet-20240229",  # Use a simpler model for fallback
        "max_tokens": 4000,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": user_prompt
            }
        ],
        "temperature": 0  # Use temperature 0 for maximum determinism
    }
    
    headers = {
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "x-api-key": api_key
    }
    
    try:
        # Make the API request
        fallback_start_time = datetime.now()
        with httpx.Client(timeout=60.0) as client:
            try:
                response = client.post(
                    "https://api.anthropic.com/v1/messages",
                    json=request_body,
                    headers=headers
                )
                fallback_duration = (datetime.now() - fallback_start_time).total_seconds()
                logger.info(f"[FALLBACK_API_DURATION] Fallback Claude API request took {fallback_duration:.2f} seconds")
            except httpx.TimeoutException:
                logger.error(f"[FALLBACK_API_TIMEOUT] Fallback API request timed out after {(datetime.now() - fallback_start_time).total_seconds():.2f} seconds")
                logger.warning("[FALLBACK_TO_TEXT_PARSER] Using text parser due to timeout")
                fallback_results = parse_biomarkers_from_text(text)
                logger.info(f"[TEXT_PARSER] Text parser found {len(fallback_results)} biomarkers after timeout")
                return fallback_results, {}
            except Exception as request_error:
                logger.error(f"[FALLBACK_API_REQUEST_ERROR] Error during fallback API request: {str(request_error)}")
                logger.warning("[FALLBACK_TO_TEXT_PARSER] Using text parser due to request error")
                fallback_results = parse_biomarkers_from_text(text)
                logger.info(f"[TEXT_PARSER] Text parser found {len(fallback_results)} biomarkers after request error")
                return fallback_results, {}
        
        # Check if the request was successful
        if response.status_code == 200:
            logger.info("[FALLBACK_API_SUCCESS] Successfully received fallback response from Claude API")
            response_data = response.json()
            
            # Save the raw fallback response for debugging
            debug_fallback_response_path = os.path.join(log_dir, f"fallback_response_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            try:
                with open(debug_fallback_response_path, "w") as f:
                    json.dump(response_data, f, indent=2)
                logger.debug(f"[FALLBACK_RESPONSE_SAVED] Raw fallback response saved to {debug_fallback_response_path}")
            except Exception as e:
                logger.error(f"[FALLBACK_RESPONSE_SAVE_ERROR] Could not save fallback response: {str(e)}")
            
            # Extract the content from the response
            content = response_data.get("content", [])
            text_content = ""
            for item in content:
                if item.get("type") == "text":
                    text_content = item.get("text", "")
                    break
            
            # Save the text content for easier debugging
            debug_fallback_text_path = os.path.join(log_dir, f"fallback_text_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            try:
                with open(debug_fallback_text_path, "w") as f:
                    f.write(text_content)
                logger.debug(f"[FALLBACK_TEXT_SAVED] Fallback text response saved to {debug_fallback_text_path}")
            except Exception as e:
                logger.error(f"[FALLBACK_TEXT_SAVE_ERROR] Could not save fallback text: {str(e)}")
            
            # Log details about the response including the full response
            logger.debug(f"[FALLBACK_RESPONSE_LENGTH] Fallback response length: {len(text_content)} chars")
            logger.debug(f"[FALLBACK_RESPONSE_PREVIEW] First 500 chars: {text_content[:500]}...")
            logger.info(f"[FALLBACK_FULL_RESPONSE] FULL FALLBACK RESPONSE: {text_content}")
            
            # Extract JSON using regex
            json_pattern = r'(\{.*\})'
            json_match = re.search(json_pattern, text_content, re.DOTALL)
            
            if json_match:
                json_str = json_match.group(0)
                
                # Save the extracted JSON for debugging
                debug_fallback_json_path = os.path.join(log_dir, f"fallback_extracted_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                try:
                    with open(debug_fallback_json_path, "w") as f:
                        f.write(json_str)
                    logger.debug(f"[FALLBACK_JSON_SAVED] Extracted fallback JSON saved to {debug_fallback_json_path}")
                except Exception as e:
                    logger.error(f"[FALLBACK_JSON_SAVE_ERROR] Could not save fallback JSON: {str(e)}")
                
                # Try to repair and load the JSON
                try:
                    repaired_json = _repair_json(json_str)
                    
                    # Save the repaired JSON for debugging
                    debug_fallback_repaired_path = os.path.join(log_dir, f"fallback_repaired_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                    try:
                        with open(debug_fallback_repaired_path, "w") as f:
                            f.write(repaired_json)
                        logger.debug(f"[FALLBACK_REPAIRED_JSON_SAVED] Repaired fallback JSON saved to {debug_fallback_repaired_path}")
                    except Exception as e:
                        logger.error(f"[FALLBACK_REPAIRED_SAVE_ERROR] Could not save repaired fallback JSON: {str(e)}")
                    
                    extraction_data = json.loads(repaired_json)
                    
                    # Process the biomarkers
                    biomarkers_simple = extraction_data.get("biomarkers", [])
                    
                    # Convert to our standard format
                    processed_biomarkers = []
                    for biomarker in biomarkers_simple:
                        # Create a more complete biomarker entry
                        processed_biomarker = {
                            "name": biomarker.get("name", "Unknown"),
                            "original_name": biomarker.get("name", "Unknown"),
                            "value": float(biomarker.get("value", 0)),
                            "original_value": str(biomarker.get("value", "")),
                            "unit": biomarker.get("unit", ""),
                            "original_unit": biomarker.get("unit", ""),
                            "reference_range_text": biomarker.get("reference_range", ""),
                            "category": "Other",
                            "is_abnormal": False,
                            "confidence": 0.7  # Lower confidence for fallback method
                        }
                        
                        # Try to parse reference range
                        ref_range = biomarker.get("reference_range", "")
                        if ref_range:
                            ref_low, ref_high, _ = parse_reference_range(ref_range)
                            processed_biomarker["reference_range_low"] = ref_low
                            processed_biomarker["reference_range_high"] = ref_high
                        
                        processed_biomarkers.append(processed_biomarker)
                    
                    logger.info(f"[FALLBACK_API_EXTRACTION] Extracted {len(processed_biomarkers)} biomarkers with fallback method")
                    
                    # Save the processed biomarkers for debugging
                    debug_processed_biomarkers_path = os.path.join(log_dir, f"fallback_processed_biomarkers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                    try:
                        with open(debug_processed_biomarkers_path, "w") as f:
                            json.dump(processed_biomarkers, f, indent=2)
                        logger.debug(f"[FALLBACK_PROCESSED_SAVED] Processed biomarkers saved to {debug_processed_biomarkers_path}")
                    except Exception as e:
                        logger.error(f"[FALLBACK_PROCESSED_SAVE_ERROR] Could not save processed biomarkers: {str(e)}")
                    
                    return processed_biomarkers, extraction_data.get("metadata", {})
                    
                except json.JSONDecodeError as e:
                    logger.error(f"[FALLBACK_JSON_ERROR] Error parsing fallback JSON: {str(e)}")
                    logger.error(f"[FALLBACK_JSON_CONTENT] Fallback JSON content: {json_str[:500]}...")
            else:
                logger.error("[FALLBACK_JSON_MISSING] No JSON found in fallback response")
                logger.error(f"[FALLBACK_RESPONSE_FULL] Full fallback response: {text_content}")
        else:
            logger.error(f"[FALLBACK_API_ERROR] Fallback API request failed with status {response.status_code}")
    
    except Exception as e:
        logger.error(f"[FALLBACK_API_EXCEPTION] Exception during fallback API call: {str(e)}")
    
    # If all else fails, use the text-based parser
    logger.warning("[FALLBACK_TO_TEXT_PARSER] All Claude API methods failed. Using fallback text parser.")
    fallback_results = parse_biomarkers_from_text(text)
    logger.info(f"[TEXT_PARSER] Text parser found {len(fallback_results)} biomarkers")
    return fallback_results, {} 