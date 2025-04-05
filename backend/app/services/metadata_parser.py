"""
Metadata Parser Service

This module provides services for parsing metadata (patient info, report details)
from lab reports using the Claude API.
"""
import json
import re
import logging
import os
import signal
from typing import Dict, Any, Optional
import httpx
from datetime import datetime
import anthropic
import threading
import time
from app.services.biomarker_parser import _preprocess_text_for_claude, _repair_json # Re-use preprocessing and repair

# Get logger for this module
logger = logging.getLogger(__name__)

# Set up a file handler
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'metadata_parser.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

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

def extract_metadata_with_claude(text: str, filename: str) -> Dict[str, Any]:
    """
    Extract metadata from PDF text using Claude API.
    
    Args:
        text: Text content from a PDF page
        filename: Name of the file/page for logging
        
    Returns:
        Dictionary containing extracted metadata, or empty dict if none found/error.
    """
    # Add input validation to prevent type errors
    if not isinstance(text, str):
        logger.error(f"[TYPE_ERROR] extract_metadata_with_claude expected text as string, got {type(text)}")
        return {}
        
    if not text:
        logger.warning(f"[EMPTY_TEXT] extract_metadata_with_claude received empty text for {filename}")
        return {}
        
    logger.info(f"[CLAUDE_METADATA_EXTRACTION_START] Extracting metadata from {filename}")
    start_time = datetime.now()
    
    # Preprocess the text (reuse from biomarker_parser)
    processed_text = _preprocess_text_for_claude(text)
    logger.debug(f"[TEXT_PREPROCESSING] Preprocessed text from {len(text)} to {len(processed_text)} characters for metadata extraction")
    
    # Prepare the prompt specifically for metadata
    prompt = f"""
You are a medical laboratory data extraction specialist. Your task is to extract ONLY the following specific metadata fields from the lab report text below:

- lab_name: The name of the laboratory (e.g., Quest Diagnostics, LabCorp)
- report_date: The date the report was generated or finalized (YYYY-MM-DD format preferred)
- patient_name: The full name of the patient
- patient_dob: The patient's date of birth (YYYY-MM-DD format preferred)
- patient_gender: The patient's gender (e.g., Male, Female, F, M)
- patient_id: Any patient identifier number found (e.g., MRN, Patient #)
- patient_age: The patient's age if explicitly stated

IMPORTANT:
- Focus ONLY on extracting these specific metadata fields.
- IGNORE all biomarker results, units, reference ranges, and clinical notes.
- If a field is not found, omit it from the JSON or set its value to null.
- Provide the result in this exact JSON format, with NO other text or explanations:

{{
  "metadata": {{
    "lab_name": "Example Lab Name | null",
    "report_date": "YYYY-MM-DD | null",
    "patient_name": "Patient Full Name | null",
    "patient_dob": "YYYY-MM-DD | null",
    "patient_gender": "Male | Female | Other | null",
    "patient_id": "Identifier String | null",
    "patient_age": "Number | null"
  }}
}}

Here is the lab report text fragment to extract metadata from:

{processed_text}
"""

    try:
        logger.debug("[CLAUDE_API_CALL_METADATA] Sending request to Claude API for metadata")
        api_start_time = datetime.now()
        
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
        if not api_key:
            logger.error("[API_KEY_ERROR_METADATA] Claude API key not found")
            return {}
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Use the timeout wrapper for the API call
        @with_timeout(timeout_seconds=45, default_return=None)  # 45 second timeout
        def call_claude_api():
            # Use a faster model
            response = client.messages.create(
                model="claude-3-sonnet-20240229", 
                max_tokens=1000,
                temperature=0.1,
                system="You are a metadata extraction expert focused on lab reports. Extract only patient and report details as specified. Output ONLY valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response
        
        # Call the API with timeout
        response = call_claude_api()
        
        # If the call timed out, return an empty dict
        if response is None:
            logger.error("[CLAUDE_API_TIMEOUT_METADATA] API call timed out")
            return {}
            
        api_duration = (datetime.now() - api_start_time).total_seconds()
        logger.info(f"[CLAUDE_API_RESPONSE_METADATA] Received metadata response from Claude API in {api_duration:.2f} seconds")
        
        response_content = response.content[0].text
        
        # Try to parse the JSON response
        try:
            json_match = re.search(r'({[\s\S]*})', response_content)
            if json_match:
                json_str = json_match.group(1)
                # Attempt to repair if necessary (reuse from biomarker_parser)
                repaired_json_str = _repair_json(json_str) 
                
                parsed_response = json.loads(repaired_json_str)
                metadata = parsed_response.get("metadata", {})
                
                # Filter out null/empty values
                filtered_metadata = {k: v for k, v in metadata.items() if v is not None and v != ""}
                
                if filtered_metadata:
                    logger.info(f"[METADATA_EXTRACTED] Successfully extracted metadata: {json.dumps(filtered_metadata)}")
                    return filtered_metadata
                else:
                    logger.info(f"[METADATA_NOT_FOUND] No metadata found by Claude in {filename}")
                    return {}
            else:
                logger.error(f"[JSON_PARSE_ERROR_METADATA] Could not extract JSON object from Claude response for {filename}")
                logger.debug(f"[RAW_RESPONSE_METADATA]: {response_content[:500]}...")
                return {}
        except json.JSONDecodeError as json_error:
            logger.error(f"[JSON_PARSE_ERROR_METADATA] Could not parse metadata JSON: {str(json_error)} for {filename}")
            logger.debug(f"[RAW_RESPONSE_METADATA]: {response_content[:500]}...")
             # Attempt repair one more time
            try:
                logger.warning(f"[JSON_REPAIR_ATTEMPT_METADATA] Attempting repair again for {filename}")
                json_match = re.search(r'({[\s\S]*})', response_content)
                if json_match:
                     repaired_json_str = _repair_json(json_match.group(1))
                     parsed_response = json.loads(repaired_json_str)
                     metadata = parsed_response.get("metadata", {})
                     filtered_metadata = {k: v for k, v in metadata.items() if v is not None and v != ""}
                     if filtered_metadata:
                         logger.info(f"[METADATA_EXTRACTED_REPAIR] Successfully extracted metadata after repair: {json.dumps(filtered_metadata)}")
                         return filtered_metadata
            except Exception as repair_e:
                 logger.error(f"[JSON_REPAIR_FAILED_METADATA] Repair failed: {str(repair_e)}")
            return {}
            
    except Exception as e:
        logger.error(f"[CLAUDE_API_ERROR_METADATA] Error calling Claude API for metadata: {str(e)}")
        return {}

# Example usage (for testing)
if __name__ == '__main__':
    # Requires ANTHROPIC_API_KEY in environment
    sample_text = """
    LabCorp Patient Report
    Patient Name: Doe, Jane
    DOB: 05/15/1980 Gender: F
    MRN: 123456789
    Report Date: 2023-10-26
    Collected: 2023-10-25
    Physician: Dr. Emily Carter
    
    Test Results:
    Glucose 95 mg/dL (70-99)
    Cholesterol 180 mg/dL (<200)
    """
    
    metadata = extract_metadata_with_claude(sample_text, "test_report.pdf - page 1")
    print("Extracted Metadata:")
    print(json.dumps(metadata, indent=2)) 