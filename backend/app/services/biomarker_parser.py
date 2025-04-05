"""
Biomarker Parser Service

This module provides services for parsing biomarker data from lab reports using
Claude API and standardizing the extracted data using the biomarker dictionary.
"""
import json
import re
import logging
import os
import threading
import time
from typing import Dict, List, Any, Optional, Tuple
import httpx
from datetime import datetime
import traceback

from app.services.biomarker_dictionary import (
    get_standardized_biomarker_name,
    convert_to_standard_unit,
    get_biomarker_category,
    get_reference_range,
    BIOMARKER_DICT
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Setup logs directory
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)

# Claude API URL
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Set this to True to save all Claude API requests and responses for debugging
SAVE_CLAUDE_RESPONSES = True

# Dictionary of common biomarker aliases for robust matching
# COMMENTED OUT - Aliases should be loaded from utils/biomarker_aliases.json
# BIOMARKER_ALIASES = {
#     "glucose": ["blood glucose", "fasting glucose", "plasma glucose", "gluc", "glu"],
#     "hemoglobin a1c": ["hba1c", "a1c", "glycated hemoglobin", "glycosylated hemoglobin", "hemoglobin a1c"],
#     "total cholesterol": ["cholesterol", "tc", "total chol", "chol, total"],
#     "hdl cholesterol": ["hdl", "hdl-c", "high density lipoprotein", "good cholesterol"],
#     "ldl cholesterol": ["ldl", "ldl-c", "low density lipoprotein", "bad cholesterol"],
#     "triglycerides": ["tg", "trigs", "triglyceride"],
#     "tsh": ["thyroid stimulating hormone", "thyrotropin", "thyroid function"],
#     "free t4": ["ft4", "thyroxine", "free thyroxine"],
#     "free t3": ["ft3", "triiodothyronine", "free triiodothyronine"],
#     "vitamin d": ["25-hydroxyvitamin d", "25-oh vitamin d", "vitamin d, 25-hydroxy", "vit d"],
#     "vitamin b12": ["b12", "cobalamin", "vit b12"],
#     "ferritin": ["ferr", "serum ferritin"],
#     "iron": ["fe", "serum iron"],
#     "transferrin": ["tf", "trf"],
#     "tibc": ["total iron binding capacity"],
#     "creatinine": ["creat", "cr", "serum creatinine"],
#     "bun": ["blood urea nitrogen", "urea nitrogen"],
#     "egfr": ["estimated glomerular filtration rate", "gfr"],
#     "alt": ["alanine aminotransferase", "sgpt"],
#     "ast": ["aspartate aminotransferase", "sgot"],
#     "alkaline phosphatase": ["alp", "alk phos"],
#     "total bilirubin": ["tbili", "bilirubin total"],
#     "albumin": ["alb", "serum albumin"],
#     "total protein": ["tp", "protein, total"],
#     "sodium": ["na", "na+", "serum sodium"],
#     "potassium": ["k", "k+", "serum potassium"],
#     "chloride": ["cl", "cl-", "serum chloride"],
#     "bicarbonate": ["hco3", "hco3-", "co2", "carbon dioxide"],
#     "calcium": ["ca", "ca2+", "serum calcium"],
#     "magnesium": ["mg", "mg2+", "serum magnesium"],
#     "phosphorus": ["p", "phos", "phosphate", "serum phosphorus"],
#     "uric acid": ["ua", "serum uric acid"],
#     "hemoglobin": ["hgb", "hb", "hg"],
#     "hematocrit": ["hct", "ht"],
#     "wbc": ["white blood cell count", "white blood cells", "leukocytes"],
#     "platelet count": ["plt", "platelets"],
#     "mch": ["mean corpuscular hemoglobin"],
#     "mchc": ["mean corpuscular hemoglobin concentration"],
#     "mcv": ["mean corpuscular volume"],
#     "rdw": ["red cell distribution width"],
#     "neutrophils": ["neut", "neutrophil count", "polys"],
#     "lymphocytes": ["lymphs", "lymphocyte count"],
#     "monocytes": ["mono", "monocyte count"],
#     "eosinophils": ["eos", "eosinophil count"],
#     "basophils": ["baso", "basophil count"],
#     "psa": ["prostate specific antigen"],
#     "c-reactive protein": ["crp", "c reactive protein"],
#     "esr": ["erythrocyte sedimentation rate", "sed rate"],
#     "homocysteine": ["hcy"],
#     "cortisol": ["cort", "serum cortisol"],
#     "testosterone": ["test", "total testosterone"],
#     "estradiol": ["e2"],
#     "progesterone": ["prog"],
#     "dhea-s": ["dehydroepiandrosterone sulfate"],
#     "folate": ["folic acid"],
#     "hla-b27": ["human leukocyte antigen b27"],
#     "ana": ["antinuclear antibody"],
#     "rf": ["rheumatoid factor"],
#     "tpo antibodies": ["thyroid peroxidase antibodies", "anti-tpo", "thyroid antibodies"]
# }

class TimeoutError(Exception):
    """Exception raised when a function call times out"""
    pass

def with_timeout(timeout_seconds, default_return=None):
    """Decorator to apply a timeout to a function"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            result = [default_return]
            exception = [None]
            
            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
            
            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)
            
            if thread.is_alive():
                logger.warning(f"[TIMEOUT] Function {func.__name__} timed out after {timeout_seconds} seconds")
                return default_return
            
            if exception[0]:
                logger.error(f"[FUNCTION_ERROR] Function {func.__name__} raised: {str(exception[0])}")
                raise exception[0]
                
            return result[0]
        return wrapper
    return decorator

def extract_biomarkers_with_claude(page_text: str, filename: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Extract biomarkers from a single page of PDF text using Claude API.

    Args:
        page_text: Text content from a single PDF page
        filename: Name of the original file for logging context

    Returns:
        Tuple containing a list of biomarkers found on the page and an empty metadata dict (metadata handled separately).
    """
    logger.info(f"[CLAUDE_EXTRACTION_START] Extracting biomarkers from {filename}")
    start_time = datetime.now()

    # Preprocess the page text
    processed_text = _preprocess_text_for_claude(page_text)
    logger.debug(f"[TEXT_PREPROCESSING] Preprocessed page text from {len(page_text)} to {len(processed_text)} characters for file {filename}")

    # Prepare the prompt for Claude - simplified for single page, no metadata request
    prompt = """
Extract ONLY legitimate clinical biomarkers from this single page of a medical lab report. Focus exclusively on measurements that have numeric values and units.

For each biomarker, provide:
- name: Standardized name
- original_name: Exact name as it appears
- value: Numerical result (convert ranges to midpoint)
- original_value: Result as shown in report
- unit: Standardized unit
- original_unit: Unit as shown
- reference_range: Normal range text
- reference_range_low: Lower bound as number
- reference_range_high: Upper bound as number
- category: One of: Lipid, Metabolic, Liver, Kidney, Electrolyte, Blood, Thyroid, Vitamin, Hormone, Immunology, Cardiovascular, Other
- is_abnormal: true if outside reference range
- confidence: 0.0-1.0 score of certainty

CRITICAL: DO NOT extract page numbers, headers, footers, patient info, dates, IDs, URLs, or explanatory text.

Return valid JSON matching exactly this structure (NO METADATA):
{
  "biomarkers": [
    {
      "name": "Glucose",
      "original_name": "Glucose, Fasting",
      "value": 95,
      "original_value": "95",
      "unit": "mg/dL",
      "original_unit": "mg/dL",
      "reference_range": "70-99 mg/dL",
      "reference_range_low": 70,
      "reference_range_high": 99,
      "category": "Metabolic",
      "is_abnormal": false,
      "confidence": 0.98
    }
  ]
}

Your response MUST be COMPLETE, VALID JSON with no truncation.

Lab report page text:
""" + processed_text

    try:
        logger.debug("[CLAUDE_API_CALL] Sending request to Claude API")
        api_start_time = datetime.now()
        
        # Get the configured Claude API key
        import os
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            logger.error("[API_KEY_ERROR] Claude API key not found in environment variables")
            raise ValueError("Claude API key not found. Set ANTHROPIC_API_KEY environment variable.")
        
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        # Use the timeout wrapper for the API call
        @with_timeout(timeout_seconds=600, default_return=None)  # 10 minute timeout
        def call_claude_api():
            # Make the API call with max tokens and timeout
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,  # Increased from 2000/4000 to handle larger responses
                temperature=0.0,
                system="You are a biomarker extraction expert specializing in parsing medical lab reports. Extract ONLY valid clinical biomarkers with measurements and reference ranges. Your output MUST be COMPLETE, VALID JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response
        
        # Call the API with timeout
        response = call_claude_api()
        
        # If the call timed out, return empty results and fall back to text-based parser for this page
        if response is None:
            logger.error(f"[CLAUDE_API_TIMEOUT] API call timed out for page processing of {filename}")
            logger.info(f"[FALLBACK_TO_TEXT_PARSER] Using fallback parser for this page due to timeout")
            fallback_results = parse_biomarkers_from_text(page_text) # Use page_text for fallback
            logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers on this page")
            return fallback_results, {} # Return empty metadata dict

        api_duration = (datetime.now() - api_start_time).total_seconds()
        logger.info(f"[CLAUDE_API_RESPONSE] Received response from Claude API for page processing of {filename} in {api_duration:.2f} seconds")
        
        # Get the response content
        response_content = response.content[0].text
        
        # Save the raw response for debugging
        debug_raw_response_path = os.path.join(log_dir, f"claude_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        try:
            with open(debug_raw_response_path, "w") as f:
                f.write(response_content)
            logger.debug(f"[RAW_RESPONSE_SAVED] Raw Claude response saved to {debug_raw_response_path}")
        except Exception as e:
            logger.error(f"[RAW_RESPONSE_SAVE_ERROR] Could not save raw response: {str(e)}")
        
        # Try to parse the JSON response
        try:
            # Extract the JSON part from the response using regex
            import re
            json_match = re.search(r'({[\s\S]*})', response_content)
            
            if json_match:
                json_str = json_match.group(1)
                logger.debug(f"[JSON_EXTRACTION] Extracted JSON string from Claude response: {len(json_str)} characters")
                
                # Save the raw JSON for debugging
                try:
                    if 'log_dir' in globals() or 'log_dir' in locals():
                        debug_raw_json_path = os.path.join(log_dir, f"raw_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                        with open(debug_raw_json_path, "w") as f:
                            f.write(json_str)
                        logger.debug(f"[RAW_JSON_SAVED] Raw JSON saved to {debug_raw_json_path}")
                except Exception as e:
                    logger.error(f"[RAW_JSON_SAVE_ERROR] Could not save raw JSON: {str(e)}")
                
                # Check if JSON is truncated and fix it
                fixed_json_str = _fix_truncated_json(json_str)
                
                # Parse the JSON
                try:
                    parsed_response = json.loads(fixed_json_str)
                except json.JSONDecodeError as decode_error:
                    # Try to repair the JSON
                    logger.warning(f"[JSON_DECODE_ERROR] Could not parse fixed JSON: {str(decode_error)}")
                    repaired_json = _repair_json(fixed_json_str)
                    parsed_response = json.loads(repaired_json)

                biomarkers = parsed_response.get("biomarkers", [])
                # metadata = parsed_response.get("metadata", {}) # Metadata is no longer requested here

                logger.info(f"[BIOMARKERS_EXTRACTED] Extracted {len(biomarkers)} biomarkers from Claude API response for page of {filename}")

                # Log metadata if available (should be empty now)
                # if metadata:
                #     logger.info(f"[METADATA_EXTRACTED] Extracted metadata: {json.dumps(metadata)}")

                # If no biomarkers were found, fall back to text-based parser for this page
                if not biomarkers:
                    logger.warning(f"[NO_BIOMARKERS_FOUND] No biomarkers found in Claude API response for page of {filename}")
                    logger.info("[FALLBACK_TO_TEXT_PARSER] Using fallback parser for this page due to empty biomarkers list")
                    fallback_results = parse_biomarkers_from_text(page_text) # Use page_text for fallback
                    logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers on this page")
                    return fallback_results, {} # Return empty metadata dict

                # Filter biomarkers based on confidence score - require at least 60% confidence
                filtered_biomarkers = []
                for biomarker in biomarkers:
                    name = biomarker.get("name", "").strip()
                    value = biomarker.get("value", 0)
                    unit = biomarker.get("unit", "")
                    confidence = float(biomarker.get("confidence", 0.0))
                    
                    if confidence < 0.6:  # Only apply minimal confidence check
                        logger.warning(f"[LOW_CONFIDENCE_BIOMARKER] Skipping low confidence biomarker: {name} (confidence: {confidence})")
                        continue
                    
                    filtered_biomarkers.append(biomarker)
                
                logger.info(f"[FILTERED_BIOMARKERS] Filtered out {len(biomarkers) - len(filtered_biomarkers)} biomarkers based on confidence score")
                
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
                        logger.error(f"[BIOMARKER_PROCESSING_STACK_TRACE] {traceback.format_exc()}")
                        logger.error(f"[BIOMARKER_DATA] Problem biomarker data: {json.dumps(biomarker)}")

                processing_duration = (datetime.now() - processing_start_time).total_seconds()
                logger.debug(f"[BIOMARKER_PROCESSING] Processing {len(filtered_biomarkers)} biomarkers for page of {filename} took {processing_duration:.2f} seconds")

                total_duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"[BIOMARKER_EXTRACTION_COMPLETE] Total extraction for page of {filename} took {total_duration:.2f} seconds")

                # If we have no valid biomarkers, try the fallback parser for this page
                if not processed_biomarkers:
                    logger.warning(f"[NO_VALID_BIOMARKERS] No valid biomarkers found in Claude response for page of {filename}. Using fallback parser.")
                    fallback_results = parse_biomarkers_from_text(page_text) # Use page_text for fallback
                    logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers on this page")
                    return fallback_results, {} # Return empty metadata dict

                return processed_biomarkers, {} # Return empty metadata dict
            else:
                logger.error(f"[JSON_PARSING_ERROR] Could not extract JSON from Claude API response for page of {filename}")
                # Fall back to text-based parser for this page
                logger.info("[FALLBACK_TO_TEXT_PARSER] Using fallback parser for this page due to JSON extraction error")
                fallback_results = parse_biomarkers_from_text(page_text) # Use page_text for fallback
                logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers on this page")
                return fallback_results, {} # Return empty metadata dict
        except json.JSONDecodeError as json_error:
            try:
                if 'log_dir' in globals() or 'log_dir' in locals():
                    debug_json_path = os.path.join(log_dir, f"invalid_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                    with open(debug_json_path, "w") as f:
                        f.write(json_str if 'json_str' in locals() else response_content)
            except Exception as e:
                logger.error(f"[DEBUG_JSON_SAVE_ERROR] Could not save invalid JSON for debugging: {str(e)}")
                
            logger.error(f"[JSON_PARSING_ERROR] Could not parse Claude API response as JSON: {str(json_error)}")
            logger.debug(f"[CLAUDE_RESPONSE] Raw response for page of {filename}: {response_content[:100]}...")

            # Fall back to text-based parser for this page
            logger.info("[FALLBACK_TO_TEXT_PARSER] Using fallback parser for this page due to JSON parsing error")
            fallback_results = parse_biomarkers_from_text(page_text) # Use page_text for fallback
            logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers on this page")
            return fallback_results, {} # Return empty metadata dict
    except Exception as e:
        logger.error(f"[CLAUDE_API_ERROR] Error calling Claude API for page of {filename}: {str(e)}")

        # Fall back to text-based parser for this page
        logger.info("[FALLBACK_TO_TEXT_PARSER] Using fallback parser for this page due to Claude API error")
        fallback_results = parse_biomarkers_from_text(page_text) # Use page_text for fallback
        logger.info(f"[FALLBACK_PARSER] Found {len(fallback_results)} biomarkers on this page")
        return fallback_results, {} # Return empty metadata dict

def _fix_truncated_json(json_str: str) -> str:
    """
    Fix truncated JSON strings by detecting incomplete structures and closing them.
    
    Args:
        json_str: Potentially truncated JSON string
        
    Returns:
        Fixed JSON string with proper structure
    """
    logger.debug(f"[JSON_TRUNCATION_CHECK] Checking if JSON is truncated, length: {len(json_str)}")
    
    # Count opening and closing brackets
    open_braces = json_str.count('{')
    close_braces = json_str.count('}')
    open_brackets = json_str.count('[')
    close_brackets = json_str.count(']')
    
    # If truncated, fix it
    if open_braces > close_braces or open_brackets > close_brackets:
        logger.warning(f"[JSON_TRUNCATED] Detected truncated JSON: {open_braces} open braces vs {close_braces} close braces, {open_brackets} open brackets vs {close_brackets} close brackets")
        
        # Extract complete biomarkers from truncated JSON
        biomarker_pattern = r'{\s*"name"\s*:.*?"confidence"\s*:\s*[\d\.]+\s*}'
        biomarkers = re.findall(biomarker_pattern, json_str, re.DOTALL)
        
        # If no complete biomarkers found with the strict pattern, try a more lenient one
        if not biomarkers:
            logger.warning("[JSON_RECOVERY_ATTEMPT] No complete biomarkers found with strict pattern, trying lenient pattern")
            biomarker_pattern = r'{\s*"name"\s*:.*?}'
            biomarkers = re.findall(biomarker_pattern, json_str, re.DOTALL)
            
            # Filter to only include biomarkers that are valid JSON
            valid_biomarkers = []
            for bm in biomarkers:
                try:
                    json.loads(bm)
                    valid_biomarkers.append(bm)
                except json.JSONDecodeError:
                    continue
            
            biomarkers = valid_biomarkers
        
        # If we have complete biomarkers, rebuild the JSON
        if biomarkers:
            logger.info(f"[JSON_RECOVERY] Found {len(biomarkers)} complete biomarkers in truncated response")
            
            # Rebuild a complete JSON structure
            fixed_json = '{"biomarkers": ['
            for i, bm in enumerate(biomarkers):
                if i > 0:
                    fixed_json += ','
                fixed_json += bm
            fixed_json += '], "metadata": {}}'
            
            # Verify the fixed JSON is valid
            try:
                json.loads(fixed_json)
                logger.info(f"[JSON_FIXED] Successfully reconstructed JSON with {len(biomarkers)} biomarkers")
                return fixed_json
            except json.JSONDecodeError as e:
                logger.error(f"[JSON_FIX_FAILED] Fixed JSON is still invalid: {str(e)}")
        else:
            logger.warning("[JSON_RECOVERY_FAILED] Could not find complete biomarkers in truncated JSON")
    
    return json_str

def validate_biomarker_with_claude(biomarker: Dict[str, Any]) -> float:
    """
    Use Claude to validate a biomarker with uncertain legitimacy.
    
    Args:
        biomarker: The biomarker data to validate
        
    Returns:
        confidence score between 0.0 and 1.0
    """
    try:
        # Extract key biomarker details for validation
        name = biomarker.get("name", "")
        value = biomarker.get("value", "")
        unit = biomarker.get("unit", "")
        reference_range = biomarker.get("reference_range", "")
        
        logger.info(f"[BIOMARKER_VALIDATION] Validating biomarker: {name} = {value} {unit}")
        
        # Construct a prompt for Claude to evaluate
        prompt = f"""
Is the following a legitimate clinical biomarker? 

Name: {name}
Value: {value}
Unit: {unit}
Reference Range: {reference_range}

A legitimate biomarker should:
1. Have a recognizable name for a substance or parameter measured in medical testing
2. Have an appropriate unit of measurement for that substance
3. Have a plausible value for a human biomarker
4. Have a reference range that makes sense for the biomarker

Please evaluate if this is a real biomarker and respond with a confidence score between 0.0 and 1.0, where:
- 0.0 means definitely NOT a legitimate biomarker
- 1.0 means definitely a legitimate biomarker
- Values in between represent your degree of confidence

Respond with ONLY the numeric confidence score.
"""
        
        # Get the configured Claude API key
        import os
        import anthropic
        
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            logger.error("[API_KEY_ERROR] Claude API key not found in environment variables")
            return 0.5  # Neutral confidence if we can't validate
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Use the timeout wrapper for the API call
        @with_timeout(timeout_seconds=30, default_return=None)  # 30 second timeout
        def call_claude_api():
            # Make a lightweight API call just for validation
            response = client.messages.create(
                model="claude-3-haiku-20240307",  # Use a smaller, faster model for validation
                max_tokens=10,
                temperature=0.0,
                system="You are evaluating whether something is a legitimate clinical biomarker.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response
        
        # Call the API with timeout
        response = call_claude_api()
        
        # If the call timed out, return neutral confidence
        if response is None:
            logger.error("[CLAUDE_API_TIMEOUT_VALIDATION] API call timed out")
            return 0.5  # Neutral confidence if the API times out
        
        # Get the response content
        response_content = response.content[0].text.strip()
        
        # Try to extract a confidence score
        try:
            # Clean up the response to extract just the number
            clean_response = response_content.replace("Confidence score:", "").strip()
            confidence = float(clean_response)
            
            # Ensure the confidence is between 0 and 1
            confidence = max(0.0, min(1.0, confidence))
            
            logger.info(f"[VALIDATION_RESULT] Biomarker '{name}' validation confidence: {confidence}")
            return confidence
        except ValueError:
            logger.warning(f"[VALIDATION_PARSING_ERROR] Could not parse validation response: {response_content}")
            return 0.5  # Default to neutral confidence
    except Exception as e:
        logger.error(f"[VALIDATION_ERROR] Error during biomarker validation: {str(e)}")
        return 0.5  # Default to neutral confidence

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
        flag = biomarker.get("is_abnormal", False)
        logger.debug(f"[FLAG_TYPE] '{name}' abnormal flag type: {type(flag).__name__}, value: {flag}")
        
        # Determine if the value is abnormal
        is_abnormal = False
        
        # Use flag if available
        if isinstance(flag, bool):
            # If flag is explicitly set as a boolean
            is_abnormal = flag
            if flag:
                logger.debug(f"[ABNORMAL_FLAG] '{name}' marked abnormal based on boolean flag")
        elif flag and isinstance(flag, str) and flag.strip().upper() in ["H", "L", "A", "HIGH", "LOW", "ABNORMAL", "TRUE"]:
            is_abnormal = True
            logger.debug(f"[ABNORMAL_FLAG] '{name}' marked abnormal based on string flag: {flag}")
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
        logger.error(f"[BIOMARKER_PROCESSING_STACK_TRACE] {traceback.format_exc()}")
        logger.error(f"[PROBLEMATIC_BIOMARKER] {json.dumps(biomarker)}")
        
        # Try to get the original value if possible
        try:
            value = float(biomarker.get("value", 0.0))
        except (ValueError, TypeError):
            try:
                value_str = str(biomarker.get("original_value", "0"))
                value = float(re.sub(r'[^\d.\-]', '', value_str)) if value_str else 0.0
            except (ValueError, TypeError):
                value = 0.0
                logger.warning(f"[VALUE_RECOVERY_FAILED] Could not recover value for {biomarker.get('name', 'unknown biomarker')}")
        
        # Return a minimal valid biomarker to avoid breaking the flow
        return {
            "name": biomarker.get("name", "Unknown Biomarker"),
            "original_name": biomarker.get("original_name", biomarker.get("name", "Unknown Biomarker")),
            "value": value,  # Use the recovered value
            "original_value": str(biomarker.get("original_value", biomarker.get("value", ""))),
            "unit": standardize_unit(biomarker.get("unit", biomarker.get("original_unit", "-"))),
            "original_unit": biomarker.get("original_unit", biomarker.get("unit", "-")),
            "category": biomarker.get("category", "Other"),
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
        "less than", "more than", "type", "age", "sex", "gender", "client", "between", 
        "am", "pm", "references", "factors", "influencing", "minimum", "maximum", "example",
        "above", "below", "high", "low", "indian", "journal", "nd", "rd", "st", "th", "table",
        "evening", "morning", "afternoon", "night"
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
            if (any(invalid in name_lower for invalid in invalid_names) or
                # Skip numeric-only names
                re.match(r'^\d+$', name) or
                # Skip names that are likely time references
                re.match(r'^\d+\s*(am|pm)$', name.lower()) or
                # Skip references to "nd" and "rd" ordinals
                re.match(r'^\d+(st|nd|rd|th)\s*$', name) or
                # Skip method descriptions
                name.startswith(")")):
                logger.debug(f"[INVALID_NAME] Skipping invalid biomarker name: {name}")
                continue
            
            # Check if name contains method description after closing parenthesis
            if ")" in name:
                # Only fix if it matches the pattern of a method description
                if re.search(r'\)\s+[\w\s]+(Kinetic|Substrate|Photometry|Buffer)', name):
                    name_parts = name.split(")")
                    if len(name_parts) > 1:
                        # Use the part before the method description plus the closing parenthesis
                        name = name_parts[0].strip() + ")"
                        logger.info(f"[BIOMARKER_NAME_FIXED] Fixed method description in name: '{name}'")
                
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
    
    # Escape % characters to prevent string formatting issues
    # text = text.replace('%', '%%')
    
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
    
    # Clean up test method descriptions in parentheses 
    # This helps prevent extraction of method descriptions as biomarkers
    text = re.sub(r'\)\s+([\w\s]+Kinetic)', r') [METHOD: \1]', text)
    text = re.sub(r'\)\s+([\w\s]+Substrate)', r') [METHOD: \1]', text)
    text = re.sub(r'\)\s+([\w\s]+Photometry)', r') [METHOD: \1]', text)
    
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
    
    # Add closing brackets if needed (improved stack-based approach)
    def balance_brackets(text):
        stack = []
        for char in text:
            if char == '{':
                stack.append('}')
            elif char == '[':
                stack.append(']')
            elif char in '}]' and stack and stack[-1] == char:
                stack.pop()
        # Add missing closing brackets in the correct order
        while stack:
            closing_bracket = stack.pop()
            text += closing_bracket
            logger.warning(f"[BRACKET_REPAIR] Added missing {closing_bracket} to balance structure")
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
    
    # Fix missing comma in the exact location mentioned in logs
    # More aggressive pattern matching for missing commas after number values
    json_str = re.sub(r'([\d\.]+)\s*\}\s*\}(\s*,?\s*\{)', r'\1}},\2', json_str)
    json_str = re.sub(r'([\d\.]+)\s*\}\s*\}(\s*\])', r'\1}},\2', json_str)
    
    # Specifically target the confidence pattern that's causing issues
    if "confidence" in json_str:
        # Look for confidence values that might be missing commas
        json_str = re.sub(r'("confidence"\s*:\s*[\d\.]+)\s*\}\s*\}', r'\1}}', json_str)
        json_str = re.sub(r'("confidence"\s*:\s*[\d\.]+)\s*\}\s*\}(\s*,?\s*\{)', r'\1}},\2', json_str)
        json_str = re.sub(r'("confidence"\s*:\s*[\d\.]+)\s*\}\s*\}(\s*\])', r'\1}},\2', json_str)
        
        # Special fix for the specific error we're seeing
        json_str = re.sub(r'("confidence"\s*:\s*0\.99)\s*\}\s*\}', r'\1}}', json_str)
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
            
            # If we have an 'expecting comma' error, let's insert one at the error position
            if "Expecting ',' delimiter" in error_msg:
                # Try to be even more specific with the fix - insert a comma directly at the error position
                fixed_json = json_str[:error_pos] + ',' + json_str[error_pos:]
                logger.warning(f"[JSON_SPECIFIC_COMMA_FIX] Inserted comma at position {error_pos}")
                
                # Try to parse the fixed JSON
                try:
                    json.loads(fixed_json)
                    logger.info("[JSON_REPAIR] Direct comma insertion fix was successful!")
                    return fixed_json
                except json.JSONDecodeError as e2:
                    logger.warning(f"[JSON_DIRECT_FIX_FAILED] Still invalid after direct fix: {str(e2)}")
            
            # Last resort - try to create a minimal valid JSON structure
            try:
                # Find all the biomarkers that parse correctly
                biomarker_pattern = r'{\s*"name"\s*:\s*"[^"]+".+?}(?=\s*,|\s*\])'
                potential_biomarkers = re.findall(biomarker_pattern, json_str, re.DOTALL)
                valid_biomarkers = []
                
                # Validate each biomarker object individually
                for bm in potential_biomarkers:
                    try:
                        json.loads(bm)
                        valid_biomarkers.append(bm)
                    except json.JSONDecodeError:
                        logger.debug(f"[BIOMARKER_INVALID] Skipping invalid biomarker: {bm[:50]}...")
                
                if valid_biomarkers:
                    # Reconstruct the JSON with only valid biomarkers
                    minimal_json = '{"biomarkers": [' + ','.join(valid_biomarkers) + '], "metadata": {}}'
                    logger.info(f"[JSON_RECONSTRUCTION] Reconstructed JSON with {len(valid_biomarkers)} valid biomarkers out of {len(potential_biomarkers)} potential")
                    
                    # Validate the reconstructed JSON
                    json.loads(minimal_json)
                    logger.info("[JSON_MINIMAL_RECONSTRUCTION] Successfully created minimal valid JSON structure")
                    return minimal_json
                else:
                    logger.warning("[JSON_RECONSTRUCTION] No valid biomarkers found")
            
            except Exception as rec_error:
                logger.error(f"[JSON_RECONSTRUCTION_ERROR] Error during minimal reconstruction: {str(rec_error)}")
            
            # As a last resort, create an empty but valid JSON response
            empty_response = '{"biomarkers": [], "metadata": {}}'
            logger.warning("[JSON_EMPTY_FALLBACK] Returning empty valid JSON as last resort")
            return empty_response
                
        except Exception as desperate_error:
            logger.error(f"[JSON_DESPERATE_REPAIR_ERROR] Error during desperate JSON repair: {str(desperate_error)}")
        
        logger.warning(f"[JSON_REPAIR] Repairs attempted but JSON is still invalid: {str(e)}")
    
    # Save the repaired JSON for debugging
    try:
        # Check if log_dir is defined in the scope
        if 'log_dir' in globals() or 'log_dir' in locals():
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
            try:
                if 'log_dir' in globals() or 'log_dir' in locals():
                    debug_fallback_response_path = os.path.join(log_dir, f"fallback_response_raw_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
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
            try:
                if 'log_dir' in globals() or 'log_dir' in locals():
                    debug_fallback_text_path = os.path.join(log_dir, f"fallback_text_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
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
                try:
                    if 'log_dir' in globals() or 'log_dir' in locals():
                        debug_fallback_json_path = os.path.join(log_dir, f"fallback_extracted_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
                        with open(debug_fallback_json_path, "w") as f:
                            f.write(json_str)
                        logger.debug(f"[FALLBACK_JSON_SAVED] Extracted fallback JSON saved to {debug_fallback_json_path}")
                except Exception as e:
                    logger.error(f"[FALLBACK_JSON_SAVE_ERROR] Could not save fallback JSON: {str(e)}")
                
                # Try to repair and load the JSON
                try:
                    repaired_json = _repair_json(json_str)
                    
                    # Save the repaired JSON for debugging
                    try:
                        if 'log_dir' in globals() or 'log_dir' in locals():
                            debug_fallback_repaired_path = os.path.join(log_dir, f"fallback_repaired_json_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
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
                    try:
                        if 'log_dir' in globals() or 'log_dir' in locals():
                            debug_processed_biomarkers_path = os.path.join(log_dir, f"fallback_processed_biomarkers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
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
