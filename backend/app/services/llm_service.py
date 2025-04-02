"""
Service for generating AI-powered explanations for biomarker results.
"""
import os
import json
import httpx
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Any
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Configuration for Claude API
CLAUDE_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Cache TTL (Time To Live)
GENERAL_EXPLANATION_TTL = 60 * 60 * 24 * 30  # 30 days for general explanations
SPECIFIC_EXPLANATION_TTL = 60 * 60 * 24 * 7   # 7 days for specific explanations

class ExplanationCache:
    """
    Simple in-memory cache for biomarker explanations.
    In a production environment, this would be replaced with Redis or similar.
    """
    def __init__(self):
        self.general_explanations: Dict[str, Dict[str, Any]] = {}
        self.specific_explanations: Dict[str, Dict[str, Any]] = {}
    
    def get_general_explanation(self, biomarker_name: str) -> Optional[str]:
        """Get general explanation for a biomarker if available and not expired."""
        entry = self.general_explanations.get(biomarker_name)
        if not entry:
            return None
        
        # Check if expired
        if datetime.utcnow().timestamp() - entry["timestamp"] > GENERAL_EXPLANATION_TTL:
            del self.general_explanations[biomarker_name]
            return None
        
        return entry["explanation"]
    
    def get_specific_explanation(self, cache_key: str) -> Optional[str]:
        """Get specific explanation for a biomarker value if available and not expired."""
        entry = self.specific_explanations.get(cache_key)
        if not entry:
            return None
        
        # Check if expired
        if datetime.utcnow().timestamp() - entry["timestamp"] > SPECIFIC_EXPLANATION_TTL:
            del self.specific_explanations[cache_key]
            return None
        
        return entry["explanation"]
    
    def add_explanation(
        self, 
        biomarker_name: str, 
        cache_key: str, 
        general_explanation: str, 
        specific_explanation: str
    ):
        """Add explanations to the cache."""
        timestamp = datetime.utcnow().timestamp()
        
        self.general_explanations[biomarker_name] = {
            "explanation": general_explanation,
            "timestamp": timestamp
        }
        
        self.specific_explanations[cache_key] = {
            "explanation": specific_explanation,
            "timestamp": timestamp
        }

async def explain_biomarker(
    biomarker_name: str,
    value: float,
    unit: str,
    reference_range: str,
    status: str
) -> Tuple[str, str]:
    """
    Generate explanations for a biomarker using Claude API.
    
    Args:
        biomarker_name: Name of the biomarker
        value: Current value of the biomarker
        unit: Unit of measurement
        reference_range: Reference range for normal values
        status: Status of the biomarker (normal or abnormal)
        
    Returns:
        Tuple containing (general_explanation, specific_explanation)
    """
    if not CLAUDE_API_KEY:
        logger.warning("CLAUDE_API_KEY is not set. Using mock responses for explanations.")
        return (
            f"The {biomarker_name} test measures the level of {biomarker_name.lower()} in your blood. "
            f"It is an important indicator of your health.",
            f"Your {biomarker_name} value is {value} {unit}, which is {status}. "
            f"The reference range is {reference_range}."
        )
    
    # Create the prompt for Claude
    prompt = f"""You are a helpful medical assistant who explains biomarker test results in plain language.

I need information about the biomarker: {biomarker_name}

Current value: {value} {unit}
Reference range: {reference_range}
Status: {status}

Please provide:
1. General explanation of what this biomarker is, what it measures, and why it's important (ABOUT_THIS_BIOMARKER section)
2. What this specific value might indicate, considering the reference range and status (YOUR_RESULTS section)
3. Any important context about when results might be concerning or when to discuss with a doctor

Format your answer with clear sections labeled:
ABOUT_THIS_BIOMARKER:
(your explanation here)

YOUR_RESULTS:
(your explanation here)

Use accessible language. Include a brief medical disclaimer at the end.
"""
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 1024,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = await client.post(
                CLAUDE_API_URL, 
                headers=headers, 
                json=payload
            )
            
            if response.status_code != 200:
                logger.error(f"Claude API error: {response.text}")
                return (
                    f"Information about {biomarker_name} is temporarily unavailable.",
                    f"Analysis of your result ({value} {unit}) is temporarily unavailable."
                )
            
            result = response.json()
            content = result.get("content", [])
            
            if not content or not isinstance(content, list) or not content[0].get("text"):
                logger.error(f"Unexpected Claude API response format: {result}")
                return (
                    f"Information about {biomarker_name} is temporarily unavailable.",
                    f"Analysis of your result ({value} {unit}) is temporarily unavailable."
                )
            
            response_text = content[0]["text"]
            
            # Parse the response to extract the sections
            try:
                general_section = "Information unavailable"
                specific_section = "Analysis unavailable"
                
                if "ABOUT_THIS_BIOMARKER:" in response_text and "YOUR_RESULTS:" in response_text:
                    parts = response_text.split("YOUR_RESULTS:")
                    general_part = parts[0].split("ABOUT_THIS_BIOMARKER:")[1].strip()
                    specific_part = parts[1].strip()
                    
                    general_section = general_part
                    specific_section = specific_part
                else:
                    # Fallback to a simple split if the expected format is not found
                    parts = response_text.split("\n\n", 1)
                    if len(parts) >= 2:
                        general_section = parts[0].strip()
                        specific_section = parts[1].strip()
                    else:
                        general_section = response_text[:min(300, len(response_text))]
                        specific_section = response_text[min(300, len(response_text)):]
                
                return (general_section, specific_section)
            except Exception as e:
                logger.error(f"Error parsing Claude response: {str(e)}")
                return (
                    response_text[:min(300, len(response_text))],
                    response_text[min(300, len(response_text)):]
                )
                
    except httpx.TimeoutException:
        logger.error("Timeout when calling Claude API")
    except httpx.RequestError as e:
        logger.error(f"HTTP error when calling Claude API: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error when calling Claude API: {str(e)}")
    
    # Fallback responses
    return (
        f"Information about {biomarker_name} is temporarily unavailable.",
        f"Analysis of your result ({value} {unit}) is temporarily unavailable."
    )

# --- New Generic LLM Function ---

async def get_llm_response(
    prompt: str, 
    model: str = "claude-3-haiku-20240307", 
    max_tokens: int = 1500 # Increased max_tokens for potentially longer summaries
) -> Optional[str]:
    """
    Sends a generic prompt to the Claude API and returns the text response.

    Args:
        prompt: The prompt string to send to the LLM.
        model: The Claude model to use.
        max_tokens: The maximum number of tokens to generate.

    Returns:
        The text content of the LLM's response, or None if an error occurs.
    """
    if not CLAUDE_API_KEY:
        logger.warning("CLAUDE_API_KEY is not set. Cannot call LLM.")
        # Optionally return a mock response for testing without API key
        # return f"Mock response for prompt starting with: {prompt[:50]}..."
        return None

    try:
        async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout for potentially longer generation
            headers = {
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            
            payload = {
                "model": model,
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            logger.info(f"Sending prompt to Claude model {model}...")
            response = await client.post(
                CLAUDE_API_URL, 
                headers=headers, 
                json=payload
            )
            
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
            
            result = response.json()
            content = result.get("content", [])
            
            if not content or not isinstance(content, list) or not content[0].get("text"):
                logger.error(f"Unexpected Claude API response format: {result}")
                return None
            
            response_text = content[0]["text"]
            logger.info(f"Received response from Claude model {model}.")
            return response_text.strip()
                
    except httpx.TimeoutException:
        logger.error(f"Timeout when calling Claude API for model {model}")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"Claude API HTTP error: {e.response.status_code} - {e.response.text}")
        return None
    except httpx.RequestError as e:
        logger.error(f"HTTP request error when calling Claude API: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error when calling Claude API: {str(e)}", exc_info=True)
        return None
