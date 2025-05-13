"""
Context Management Utilities

This module provides utilities for managing extraction context
across API calls to reduce redundant instructions and token usage.
"""
from typing import Dict, List, Any, Optional
import logging
import json


def create_adaptive_prompt(
    chunk_text: str,
    page_num: int,
    extraction_context: Dict[str, Any],
    base_prompt_template: Optional[str] = None
) -> str:
    """
    Create an adaptive prompt for extraction based on context.
    
    Args:
        chunk_text: Text content to extract from
        page_num: Page number of the chunk
        extraction_context: Current extraction context
        base_prompt_template: Optional custom prompt template
        
    Returns:
        Optimized prompt string for Claude API
    """
    # Default base prompt template
    if base_prompt_template is None:
        base_prompt_template = """
I need to extract biomarker information from medical lab reports.
{context_instructions}

For each biomarker, extract:
- Name: The biomarker name
- Value: The numeric value
- Unit: The measurement unit (ng/ml, etc.)
- Reference Range: The normal/reference range if available
- Flag: Whether the value is marked as High, Low, or Normal

Extract ONLY biomarkers with numeric values. Return data as a JSON list of objects.
{known_biomarker_instructions}

TEXT FROM PAGE {page_num}:
{chunk_text}
"""
    
    # Generate context-specific instructions
    context_instructions = ""
    known_biomarker_instructions = ""
    
    # If this isn't the first call, we can optimize instructions
    if extraction_context["call_count"] > 0:
        context_instructions = "This is a continuation of the previous extraction."
        
        # Add information about patterns that have been successful
        if extraction_context["extraction_patterns"]:
            patterns = "; ".join(extraction_context["extraction_patterns"][:3])
            context_instructions += f" Use patterns like: {patterns}"
        
        # Add information about section context if available
        if extraction_context["section_context"]:
            section_info = "; ".join(
                f"{k}: {v}" for k, v in list(extraction_context["section_context"].items())[:2]
            )
            context_instructions += f" Context: {section_info}"
        
        # Add instructions about known biomarkers
        known_biomarkers = extraction_context["known_biomarkers"]
        if known_biomarkers:
            sample_biomarkers = list(known_biomarkers.keys())[:5]
            known_biomarker_instructions = f"I've already extracted these biomarkers: {', '.join(sample_biomarkers)}. Only extract new ones or ones with different values."
    
    # Fill the template
    prompt = base_prompt_template.format(
        context_instructions=context_instructions,
        known_biomarker_instructions=known_biomarker_instructions,
        page_num=page_num,
        chunk_text=chunk_text
    )
    
    return prompt


def update_extraction_context(
    extraction_context: Dict[str, Any],
    biomarkers: List[Dict[str, Any]],
    page_num: int,
    input_tokens: int = 0,
    output_tokens: int = 0
) -> Dict[str, Any]:
    """
    Update extraction context with new biomarkers and usage information.
    
    Args:
        extraction_context: Current extraction context
        biomarkers: New extracted biomarkers
        page_num: Page number for the extraction
        input_tokens: Input tokens used for this call
        output_tokens: Output tokens used for this call
        
    Returns:
        Updated extraction context
    """
    # Create a new context to avoid mutating the input
    updated_context = extraction_context.copy()
    
    # Update call count and token usage
    updated_context["call_count"] += 1
    updated_context["token_usage"]["input"] = updated_context["token_usage"].get("input", 0) + input_tokens
    updated_context["token_usage"]["output"] = updated_context["token_usage"].get("output", 0) + output_tokens
    
    # Update known biomarkers
    for biomarker in biomarkers:
        if "name" not in biomarker or not biomarker["name"]:
            continue
            
        name = biomarker["name"].lower()
        
        # If we already have this biomarker, update it only if page is higher
        # This assumes later pages have more recent information
        if name in updated_context["known_biomarkers"]:
            existing_page = updated_context["known_biomarkers"][name].get("page", 0)
            if page_num > existing_page:
                biomarker["page"] = page_num
                updated_context["known_biomarkers"][name] = biomarker
        else:
            # New biomarker
            biomarker["page"] = page_num
            updated_context["known_biomarkers"][name] = biomarker
    
    # Update extraction patterns based on successful extractions
    if biomarkers:
        # Example pattern: Add simple pattern based on first biomarker
        if biomarkers[0].get("name") and biomarkers[0].get("value"):
            pattern = f"{biomarkers[0]['name']}: {biomarkers[0]['value']} {biomarkers[0].get('unit', '')}"
            if pattern not in updated_context["extraction_patterns"]:
                updated_context["extraction_patterns"].append(pattern)
        
        # Update section context with page information
        updated_context["section_context"]["last_page"] = str(page_num)
        updated_context["section_context"]["biomarker_count"] = str(len(updated_context["known_biomarkers"]))
    
    return updated_context


def validate_biomarker_confidence(
    biomarker: Dict[str, Any],
    extraction_context: Dict[str, Any],
    document_structure: Optional[Dict[str, Any]] = None
) -> float:
    """
    Calculate confidence score for a biomarker extraction.
    
    Args:
        biomarker: Extracted biomarker
        extraction_context: Current extraction context
        document_structure: Optional document structure information
        
    Returns:
        Confidence score (0.0-1.0)
    """
    base_confidence = 0.7  # Start with reasonable confidence
    
    # Adjust confidence based on completeness
    # Check required fields
    required_fields = ["name", "value", "unit"]
    if all(field in biomarker and biomarker[field] for field in required_fields):
        base_confidence += 0.1
    else:
        base_confidence -= 0.2
    
    # Check for reference range
    if "reference_range" in biomarker and biomarker["reference_range"]:
        base_confidence += 0.05
    
    # Validate against known patterns
    name = biomarker.get("name", "").lower()
    value = biomarker.get("value", "")
    unit = biomarker.get("unit", "")
    
    # Handle structural validation if document structure is available
    if document_structure:
        # If we know this page has tables and biomarker is from a table, higher confidence
        page_num = biomarker.get("page", 0)
        has_tables = page_num in document_structure.get("tables", {}) and document_structure["tables"][page_num]
        
        if has_tables:
            base_confidence += 0.05
    
    # Handle duplicate detection
    if name in extraction_context["known_biomarkers"]:
        existing = extraction_context["known_biomarkers"][name]
        # If values match exactly, reduce confidence (likely duplicate)
        if existing.get("value") == value and existing.get("unit") == unit:
            base_confidence -= 0.1
        # If values differ significantly, reduce confidence (potential error)
        elif existing.get("value") and value:
            try:
                existing_val = float(existing["value"])
                current_val = float(value)
                # If values are very different, reduce confidence
                if abs(existing_val - current_val) / max(existing_val, current_val) > 0.5:
                    base_confidence -= 0.15
            except (ValueError, TypeError):
                # Can't compare numerically
                pass
    
    # Ensure confidence is in valid range
    return max(0.0, min(1.0, base_confidence))


def filter_biomarkers_by_confidence(
    biomarkers: List[Dict[str, Any]],
    extraction_context: Dict[str, Any],
    document_structure: Optional[Dict[str, Any]] = None,
    threshold: float = 0.6
) -> List[Dict[str, Any]]:
    """
    Filter biomarkers based on confidence scores.
    
    Args:
        biomarkers: List of extracted biomarkers
        extraction_context: Current extraction context
        document_structure: Optional document structure information
        threshold: Minimum confidence threshold
        
    Returns:
        Filtered list of biomarkers
    """
    filtered_biomarkers = []
    
    for biomarker in biomarkers:
        confidence = validate_biomarker_confidence(
            biomarker, extraction_context, document_structure
        )
        
        # Add confidence score to biomarker
        biomarker["confidence"] = confidence
        
        # Keep biomarkers above threshold
        if confidence >= threshold:
            filtered_biomarkers.append(biomarker)
    
    return filtered_biomarkers


def create_default_extraction_context() -> Dict[str, Any]:
    """
    Create a default extraction context for a new document.
    
    Args:
        None
        
    Returns:
        Default extraction context dictionary
    """
    return {
        "known_biomarkers": {},
        "extraction_patterns": [],
        "section_context": {},
        "call_count": 0,
        "token_usage": {"input": 0, "output": 0},
        "confidence_threshold": 0.7
    }


def merge_extraction_contexts(contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple extraction contexts into one.
    
    Args:
        contexts: List of extraction contexts to merge
        
    Returns:
        Merged extraction context
    """
    if not contexts:
        return create_default_extraction_context()
    
    # Start with a copy of the first context
    merged = contexts[0].copy()
    
    # Merge additional contexts
    for ctx in contexts[1:]:
        # Merge known biomarkers (take the higher page number if duplicates)
        for name, biomarker in ctx["known_biomarkers"].items():
            if name in merged["known_biomarkers"]:
                existing_page = merged["known_biomarkers"][name].get("page", 0)
                current_page = biomarker.get("page", 0)
                
                if current_page > existing_page:
                    merged["known_biomarkers"][name] = biomarker
            else:
                merged["known_biomarkers"][name] = biomarker
        
        # Merge extraction patterns (avoid duplicates)
        for pattern in ctx["extraction_patterns"]:
            if pattern not in merged["extraction_patterns"]:
                merged["extraction_patterns"].append(pattern)
        
        # Update section context with highest values
        for key, value in ctx["section_context"].items():
            if key not in merged["section_context"] or value > merged["section_context"][key]:
                merged["section_context"][key] = value
        
        # Add call counts
        merged["call_count"] += ctx["call_count"]
        
        # Add token usage
        merged["token_usage"]["input"] += ctx["token_usage"].get("input", 0)
        merged["token_usage"]["output"] += ctx["token_usage"].get("output", 0)
    
    return merged 