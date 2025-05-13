"""
Content Optimization Utilities

This module provides utilities for optimizing content for extraction,
including chunking, token counting, and biomarker pattern recognition.
"""
from typing import Dict, List, Any, Optional
import logging
import re
import math

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    logging.warning("tiktoken not installed. Token counting will use fallback method.")
    TIKTOKEN_AVAILABLE = False


def estimate_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
    """
    Estimate the number of tokens in a text string.
    
    Args:
        text: The text to estimate tokens for
        model: The model to use for token counting
        
    Returns:
        Estimated token count
    """
    if not text:
        return 0
        
    if TIKTOKEN_AVAILABLE:
        try:
            # Use tiktoken for accurate counting
            encoding = tiktoken.encoding_for_model(model)
            tokens = len(encoding.encode(text))
            return tokens
        except Exception as e:
            logging.warning(f"Error using tiktoken: {e}, falling back to approximation")
    
    # Fallback approximation: 1 token ~= 4 characters for English text
    return math.ceil(len(text) / 4)


def chunk_text(
    text: str, 
    max_tokens: int = 8000, 
    overlap_tokens: int = 200
) -> List[str]:
    """
    Split text into chunks of approximately max_tokens with overlap.
    
    Args:
        text: Text to split
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Number of overlapping tokens between chunks
        
    Returns:
        List of text chunks
    """
    # If text is small enough, return as single chunk
    if estimate_tokens(text) <= max_tokens:
        return [text]
    
    chunks = []
    paragraphs = text.split('\n\n')
    
    current_chunk = []
    current_tokens = 0
    
    for paragraph in paragraphs:
        para_tokens = estimate_tokens(paragraph)
        
        # If adding this paragraph would exceed the limit
        if current_tokens + para_tokens > max_tokens and current_chunk:
            # Join current chunk and add to results
            chunks.append('\n\n'.join(current_chunk))
            
            # Start new chunk with overlap
            # Find paragraphs to include for overlap
            overlap_paragraphs = []
            overlap_tokens_count = 0
            for p in reversed(current_chunk):
                p_tokens = estimate_tokens(p)
                if overlap_tokens_count + p_tokens <= overlap_tokens:
                    overlap_paragraphs.insert(0, p)
                    overlap_tokens_count += p_tokens
                else:
                    break
            
            # Reset with overlap
            current_chunk = overlap_paragraphs.copy()
            current_tokens = overlap_tokens_count
        
        # Add paragraph to current chunk
        current_chunk.append(paragraph)
        current_tokens += para_tokens
    
    # Add final chunk if not empty
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def optimize_content_chunks(
    pages_text_dict: Dict[int, str],
    document_structure: Dict[str, Any],
    max_tokens_per_chunk: int = 8000
) -> List[Dict[str, Any]]:
    """
    Create optimized content chunks based on document structure.
    
    Args:
        pages_text_dict: Dictionary mapping page numbers to text
        document_structure: Structure information about the document
        max_tokens_per_chunk: Maximum tokens per chunk
        
    Returns:
        List of content chunks
    """
    chunks = []
    
    # Extract tables as separate chunks (high priority for biomarkers)
    tables = document_structure.get("tables", {})
    for page_num, page_tables in tables.items():
        for table in page_tables:
            if "text" in table and table["text"]:
                # Table has its own text
                table_text = table["text"]
            else:
                # Extract table from page text (approximate)
                # In real implementation, use zone coordinates for better extraction
                page_text = pages_text_dict.get(page_num, "")
                table_text = page_text  # Simplified - would need coordinates to extract
            
            chunk = {
                "text": table_text,
                "page_num": page_num,
                "region_type": "table",
                "estimated_tokens": estimate_tokens(table_text),
                "biomarker_confidence": 0.9,  # Tables likely have biomarkers
                "context": f"Page {page_num}, Table {table.get('index', 0)}"
            }
            chunks.append(chunk)
    
    # Process remaining content by zones
    for page_num, page_text in pages_text_dict.items():
        # Skip pages that don't have text
        if not page_text.strip():
            continue
            
        # Skip pages already fully processed as tables
        if page_num in tables:
            # TODO: This is simplified - actual implementation should check
            # if any text remains outside the tables
            continue
        
        # Check for zones
        zones = document_structure.get("page_zones", {}).get(page_num, {})
        
        if zones and "content" in zones:
            # Process content zone (most important for biomarkers)
            content_zone = zones["content"]
            zone_text = content_zone.get("text", "")
            
            if not zone_text and "content" in page_text.lower():
                # Fallback if zone text not extracted
                zone_text = page_text
            
            # Skip if no text
            if not zone_text.strip():
                continue
                
            # Split content into chunks if needed
            content_chunks = chunk_text(zone_text, max_tokens_per_chunk)
            
            for i, chunk_text in enumerate(content_chunks):
                chunk = {
                    "text": chunk_text,
                    "page_num": page_num,
                    "region_type": "content",
                    "estimated_tokens": estimate_tokens(chunk_text),
                    "biomarker_confidence": 0.7,  # Content likely has biomarkers
                    "context": f"Page {page_num}, Content {i+1}/{len(content_chunks)}"
                }
                chunks.append(chunk)
        else:
            # Process whole page if no zones
            page_chunks = chunk_text(page_text, max_tokens_per_chunk)
            
            for i, chunk_text in enumerate(page_chunks):
                chunk = {
                    "text": chunk_text,
                    "page_num": page_num,
                    "region_type": "text",
                    "estimated_tokens": estimate_tokens(chunk_text),
                    "biomarker_confidence": 0.5,  # Unknown if has biomarkers
                    "context": f"Page {page_num}, Chunk {i+1}/{len(page_chunks)}"
                }
                chunks.append(chunk)
    
    # Sort chunks by page_num and then biomarker_confidence
    chunks.sort(key=lambda x: (x["page_num"], -x["biomarker_confidence"]))
    
    return chunks


def detect_biomarker_patterns(text: str) -> float:
    """
    Detect biomarker patterns in text and return confidence.
    
    Args:
        text: Text to analyze
        
    Returns:
        Confidence score (0.0-1.0) that text contains biomarkers
    """
    # Common biomarker patterns
    patterns = [
        r"\b[A-Za-z\s]+:\s*\d+[\.,]?\d*\s*[a-zA-Z/%]+",  # Name: Value Unit
        r"\b[A-Za-z\s]+\s+\d+[\.,]?\d*\s*[a-zA-Z/%]+\s*\(.*?\)",  # Name Value Unit (Ref)
        r"\b[A-Za-z\s]+\s+\d+[\.,]?\d*\s*[a-zA-Z/%]+",  # Name Value Unit
        r"\b(?:high|low|normal|positive|negative)\b",  # Result indicators
        r"\b(?:reference\s*range|normal\s*range)\b",  # Reference range indicators
        r"(?:\d+\s*[\-–]\s*\d+)",  # Numeric ranges
    ]
    
    # Count matches
    match_count = 0
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        match_count += len(matches)
    
    # Calculate confidence based on match density
    text_length = len(text)
    if text_length < 10:
        return 0.0
        
    # Normalize by text length to avoid bias for longer texts
    density = match_count / (text_length / 100)  # Matches per 100 chars
    
    # Map density to confidence score
    if density > 5:
        confidence = 0.9  # Very high density
    elif density > 2:
        confidence = 0.8  # High density
    elif density > 1:
        confidence = 0.7  # Moderate density
    elif density > 0.5:
        confidence = 0.6  # Some matches
    elif density > 0.1:
        confidence = 0.4  # Few matches
    else:
        confidence = 0.2  # Very few matches
    
    return confidence


def enhance_chunk_confidence(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhance confidence scores of chunks based on biomarker patterns.
    
    Args:
        chunks: List of content chunks
        
    Returns:
        Updated list of content chunks with enhanced confidence scores
    """
    for chunk in chunks:
        # Skip chunks that already have high confidence
        if chunk["biomarker_confidence"] >= 0.8:
            continue
            
        # Analyze text for biomarker patterns
        pattern_confidence = detect_biomarker_patterns(chunk["text"])
        
        # Update confidence if pattern detection is higher
        if pattern_confidence > chunk["biomarker_confidence"]:
            chunk["biomarker_confidence"] = pattern_confidence
    
    return chunks 