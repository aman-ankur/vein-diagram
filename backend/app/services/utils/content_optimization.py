"""
Content Optimization Utilities

This module provides utilities for optimizing content for extraction,
including chunking, token counting, and biomarker pattern recognition.
"""
from typing import Dict, List, Any, Optional, Tuple
import logging
import re
import math
import json
import os
from datetime import datetime

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
    CLAUDE_ENCODING = "cl100k_base"  # Claude uses the same tokenizer as GPT-4
except ImportError:
    logging.warning("tiktoken not installed. Token counting will use fallback method.")
    TIKTOKEN_AVAILABLE = False


def estimate_tokens(text: str, model: str = "claude-3-sonnet-20240229") -> int:
    """
    Estimate the number of tokens in a text string using tiktoken if available.
    
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
            encoding = tiktoken.get_encoding(CLAUDE_ENCODING)
            tokens = len(encoding.encode(text))
            return tokens
        except Exception as e:
            logging.warning(f"Error using tiktoken: {e}, falling back to approximation")
    
    # Fallback approximation: 1 token ~= 4 characters for English text
    return math.ceil(len(text) / 4)


def chunk_text(
    text: str, 
    max_tokens: int = 8000, 
    overlap_tokens: int = 200,
    smart_boundaries: bool = True
) -> List[str]:
    """
    Split text into chunks of approximately max_tokens with overlap,
    respecting natural text boundaries when possible.
    
    Args:
        text: Text to split
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Number of overlapping tokens between chunks
        smart_boundaries: Whether to use smart boundary detection for better chunking
        
    Returns:
        List of text chunks
    """
    # If text is small enough, return as single chunk
    if estimate_tokens(text) <= max_tokens:
        return [text]
    
    chunks = []
    
    if smart_boundaries:
        # Split on section boundaries first
        section_pattern = r'(?:\n\s*#+\s+[A-Z0-9]|\n\s*[A-Z][A-Z\s]+:|\n\s*[A-Z][A-Z\s]+\n)'
        sections = re.split(section_pattern, text)
        
        # If splitting by sections created reasonable chunks
        if sections and max(estimate_tokens(s) for s in sections) < max_tokens * 0.8:
            current_chunk = []
            current_tokens = 0
            
            for section in sections:
                if not section.strip():
                    continue
                
                section_tokens = estimate_tokens(section)
                
                # If adding section would exceed the max tokens
                if current_tokens + section_tokens > max_tokens and current_chunk:
                    chunks.append("\n".join(current_chunk))
                    
                    # Start new chunk
                    current_chunk = []
                    current_tokens = 0
                
                # Add section to current chunk
                current_chunk.append(section)
                current_tokens += section_tokens
            
            # Add the final chunk
            if current_chunk:
                chunks.append("\n".join(current_chunk))
            
            return chunks
    
    # Fall back to paragraph splitting if sections don't work well
    paragraphs = re.split(r'\n\s*\n', text)
    
    current_chunk = []
    current_tokens = 0
    
    for paragraph in paragraphs:
        if not paragraph.strip():
            continue
            
        para_tokens = estimate_tokens(paragraph)
        
        # If paragraph is too large by itself, split it further
        if para_tokens > max_tokens:
            if current_chunk:
                chunks.append("\n\n".join(current_chunk))
                current_chunk = []
                current_tokens = 0
            
            # Split large paragraph by sentences
            sentences = re.split(r'(?<=[.!?])\s+', paragraph)
            sentence_chunk = []
            sentence_tokens = 0
            
            for sentence in sentences:
                sent_tokens = estimate_tokens(sentence)
                
                if sentence_tokens + sent_tokens > max_tokens and sentence_chunk:
                    chunks.append(" ".join(sentence_chunk))
                    sentence_chunk = []
                    sentence_tokens = 0
                
                sentence_chunk.append(sentence)
                sentence_tokens += sent_tokens
            
            if sentence_chunk:
                chunks.append(" ".join(sentence_chunk))
            
            continue
        
        # If adding this paragraph would exceed the limit
        if current_tokens + para_tokens > max_tokens and current_chunk:
            # Join current chunk and add to results
            chunks.append("\n\n".join(current_chunk))
            
            # Start new chunk with overlap
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
        chunks.append("\n\n".join(current_chunk))
    
    return chunks


def compress_text_content(text: str) -> str:
    """
    Apply conservative compression techniques to reduce token usage
    while preserving biomarker information. Ensures token reduction.
    
    Args:
        text: Text to compress
        
    Returns:
        Compressed text with guaranteed token reduction or original text if compression fails
    """
    if not text:
        return ""
    
    # Store original for fallback
    original_text = text
    original_tokens = estimate_tokens(original_text)
    
    # Start with original text
    original_length = len(text)
    
    # Step 1: Remove redundant whitespace (safe operation)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n', text)
    
    # Step 2: Remove clearly non-biomarker content (conservative patterns)
    safe_removal_patterns = [
        r"Page \d+ of \d+",
        r"http[s]?://[^\s]+",
        r"www\.[^\s]+",
        r"Email\s*:\s*[^\s]+@[^\s]+",
        r"Tel\s*:\s*[\d\s\-\+\(\)]{10,}",
        r"Fax\s*:\s*[\d\s\-\+\(\)]{10,}",
        r"CIN\s*[-:]?\s*[A-Z0-9]{15,}",
        r"GSTIN\s*[-:]?\s*[A-Z0-9]{15,}",
        r"©\s*\d{4}[^.]*\.?",
    ]
    
    for pattern in safe_removal_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # Step 3: Remove excessive formatting (conservative)
    text = re.sub(r'[-_*=]{5,}', ' ', text)  # Only remove very long separators
    text = re.sub(r'\|{3,}', '|', text)  # Collapse excessive pipes
    
    # Step 4: Standardize numbers (safe operation)
    text = re.sub(r'(\d+),(\d{3})', r'\1\2', text)  # Remove thousands separators
    text = re.sub(r'(\d+)\.0+\b', r'\1', text)  # Remove trailing zeros
    
    # Step 5: Final cleanup
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Validation: Ensure we actually reduced tokens
    compressed_tokens = estimate_tokens(text)
    
    if compressed_tokens >= original_tokens:
        # If compression didn't help or made it worse, return original
        logging.debug(f"Compression failed to reduce tokens ({original_tokens} -> {compressed_tokens}), using original")
        return original_text
    
    # Log successful compression
    compression_ratio = (1 - compressed_tokens / original_tokens) * 100
    logging.debug(f"Text compression successful: {original_tokens} -> {compressed_tokens} tokens ({compression_ratio:.1f}% reduction)")
    
    return text


def extract_table_text(table: Dict[str, Any], page_text: str) -> str:
    """
    Extract text from a table region using table coordinates.
    
    Args:
        table: Table information including bbox 
        page_text: Full page text
        
    Returns:
        Table text
    """
    if "text" in table and table["text"]:
        return table["text"]
    
    # This is a simplified implementation
    # In a real implementation, you would use the table boundaries
    # to extract the relevant portion of text from the page
    # using more advanced text region extraction
    
    # For now, returning a section of the page text
    # that likely contains the table based on text cues
    
    # Look for tabular patterns in the text
    table_section_patterns = [
        r'(?:\+[-+]+\+[\s\S]*?\+[-+]+\+)',
        r'(?:\|[^|]*\|[^|]*\|[\s\S]*?\|[^|]*\|)',
        r'(?:(?:TEST|RESULT|REFERENCE|UNITS|VALUE)(?:\s*\|\s*|\s{2,})){2,}[\s\S]*?(?:\n\s*\n|\Z)'
    ]
    
    for pattern in table_section_patterns:
        match = re.search(pattern, page_text)
        if match:
            return match.group(0)
    
    # If no table pattern found, return a smaller portion of the page (first 1000 chars)
    # to avoid token duplication
    return page_text[:1000] if page_text else ""


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
        # Value with units
        r"\b\d+[\.,]?\d*\s*(?:mg/[dD][lL]|g/[dD][lL]|mmol/L|U/L|IU/L|ng/m[lL]|pg/m[lL]|μg/[dD][lL]|mcg/[dD][lL]|%|mEq/L)",
        
        # Name: Value Unit format
        r"\b[A-Za-z\s]+:\s*\d+[\.,]?\d*\s*[a-zA-Z/%]+",
        
        # Name Value Unit (Reference) format
        r"\b[A-Za-z\s]+\s+\d+[\.,]?\d*\s*[a-zA-Z/%]+\s*\(.*?\)",
        
        # Result indicators
        r"\b(?:high|low|normal|positive|negative|abnormal)\b",
        
        # Reference range indicators
        r"\b(?:reference\s*range|normal\s*range|ref[.]?\s*range)\b",
        
        # Numeric ranges
        r"(?:\d+\s*[\-–]\s*\d+)",
        
        # Common biomarker names with units
        r"\b(?:glucose|cholesterol|triglycerides|hdl|ldl|alt|ast|tsh|t4|hemoglobin|a1c|creatinine|sodium|potassium|calcium|vitamin\s+[a-d])\b.{0,30}?\d+[\.,]?\d*"
    ]
    
    # Count matches
    weighted_matches = 0
    for i, pattern in enumerate(patterns):
        pattern_weight = 1.0
        # Increase weight for more specific patterns
        if i < 3:  # Unit patterns are stronger indicators
            pattern_weight = 2.0
        
        matches = re.findall(pattern, text, re.IGNORECASE)
        weighted_matches += len(matches) * pattern_weight
    
    # Calculate confidence based on match density
    text_length = len(text)
    if text_length < 10:
        return 0.0
        
    # Normalize by text length to avoid bias for longer texts
    density = weighted_matches / (text_length / 100)  # Weighted matches per 100 chars
    
    # Map density to confidence score
    if density > 5:
        confidence = 0.95  # Very high density
    elif density > 2:
        confidence = 0.85  # High density
    elif density > 1:
        confidence = 0.75  # Medium density
    elif density > 0.5:
        confidence = 0.6   # Low density
    elif density > 0.2:
        confidence = 0.4   # Very low density
    else:
        confidence = 0.2   # Minimal indicators
    
    # Check for strong biomarker section headers
    section_headers = [
        r"\b(?:laboratory\s+results|lab\s+results|test\s+results)\b",
        r"\b(?:clinical\s+chemistry|chemistry\s+panel|chemistry\s+results)\b",
        r"\b(?:hematology\s+panel|hematology\s+results|blood\s+panel)\b",
        r"\b(?:lipid\s+panel|metabolic\s+panel|liver\s+panel|kidney\s+panel)\b"
    ]
    
    for header in section_headers:
        if re.search(header, text, re.IGNORECASE):
            confidence = min(0.99, confidence + 0.15)  # Boost confidence
    
    return confidence


def split_zone_by_biomarker_density(
    zone_data: Dict[str, Any], 
    page_text: str,
    max_tokens: int = 4000
) -> List[Dict[str, Any]]:
    """
    Split a document zone into chunks based on biomarker density.
    
    Args:
        zone_data: Zone information 
        page_text: Full page text
        max_tokens: Maximum tokens per chunk
        
    Returns:
        List of ContentChunk objects
    """
    zone_text = zone_data.get("text", "")
    page_num = zone_data.get("page_number", 0)
    zone_type = zone_data.get("zone_type", "content")
    
    if not zone_text and page_text:
        # Extract zone text from page_text if not provided
        # This is a simplified implementation
        zone_text = page_text
    
    if not zone_text.strip():
        return []
    
    # Split text into paragraphs
    paragraphs = re.split(r'\n\s*\n', zone_text)
    
    # Analyze biomarker density for each paragraph
    scored_paragraphs = []
    for para in paragraphs:
        if not para.strip():
            continue
        scored_paragraphs.append({
            "text": para,
            "biomarker_confidence": detect_biomarker_patterns(para),
            "tokens": estimate_tokens(para)
        })
    
    # Sort paragraphs by biomarker confidence (high to low)
    scored_paragraphs.sort(key=lambda x: x["biomarker_confidence"], reverse=True)
    
    # Create chunks optimized for biomarker extraction
    chunks = []
    current_chunk = []
    current_tokens = 0
    current_confidence = 0
    
    # First prioritize high-confidence paragraphs
    high_confidence_threshold = 0.7
    for para in [p for p in scored_paragraphs if p["biomarker_confidence"] >= high_confidence_threshold]:
        para_tokens = para["tokens"]
        
        # If this paragraph alone exceeds max tokens, split it
        if para_tokens > max_tokens:
            if current_chunk:
                # Save current chunk first
                chunk_text = "\n\n".join([p["text"] for p in current_chunk])
                chunk_confidence = sum(p["biomarker_confidence"] for p in current_chunk) / len(current_chunk)
                
                chunks.append({
                    "text": chunk_text,
                    "page_num": page_num,
                    "region_type": zone_type,
                    "estimated_tokens": current_tokens,
                    "biomarker_confidence": chunk_confidence,
                    "context": f"Page {page_num}, {zone_type.capitalize()}"
                })
                
                # Reset
                current_chunk = []
                current_tokens = 0
                current_confidence = 0
            
            # Split the large paragraph into smaller chunks
            for text_part in chunk_text(para["text"], max_tokens, overlap_tokens=100):
                chunks.append({
                    "text": text_part,
                    "page_num": page_num,
                    "region_type": zone_type,
                    "estimated_tokens": estimate_tokens(text_part),
                    "biomarker_confidence": para["biomarker_confidence"],
                    "context": f"Page {page_num}, {zone_type.capitalize()}"
                })
            
            continue
            
        # If adding this paragraph would exceed max tokens
        if current_tokens + para_tokens > max_tokens and current_chunk:
            # Save current chunk
            chunk_text = "\n\n".join([p["text"] for p in current_chunk])
            chunk_confidence = sum(p["biomarker_confidence"] for p in current_chunk) / len(current_chunk)
            
            chunks.append({
                "text": chunk_text,
                "page_num": page_num,
                "region_type": zone_type,
                "estimated_tokens": current_tokens,
                "biomarker_confidence": chunk_confidence,
                "context": f"Page {page_num}, {zone_type.capitalize()}"
            })
            
            # Reset
            current_chunk = []
            current_tokens = 0
            current_confidence = 0
        
        # Add paragraph to current chunk
        current_chunk.append(para)
        current_tokens += para_tokens
        current_confidence += para["biomarker_confidence"]
    
    # Process remaining lower-confidence paragraphs
    for para in [p for p in scored_paragraphs if p["biomarker_confidence"] < high_confidence_threshold]:
        para_tokens = para["tokens"]
        
        # Skip very low confidence paragraphs unless they're small
        if para["biomarker_confidence"] < 0.3 and para_tokens > 100:
            continue
            
        # If adding this paragraph would exceed max tokens
        if current_tokens + para_tokens > max_tokens and current_chunk:
            # Save current chunk
            chunk_text = "\n\n".join([p["text"] for p in current_chunk])
            chunk_confidence = sum(p["biomarker_confidence"] for p in current_chunk) / len(current_chunk)
            
            chunks.append({
                "text": chunk_text,
                "page_num": page_num,
                "region_type": zone_type,
                "estimated_tokens": current_tokens,
                "biomarker_confidence": chunk_confidence,
                "context": f"Page {page_num}, {zone_type.capitalize()}"
            })
            
            # Reset
            current_chunk = []
            current_tokens = 0
            current_confidence = 0
        
        # Add paragraph to current chunk
        current_chunk.append(para)
        current_tokens += para_tokens
        current_confidence += para["biomarker_confidence"]
    
    # Add final chunk if not empty
    if current_chunk:
        chunk_text = "\n\n".join([p["text"] for p in current_chunk])
        chunk_confidence = sum(p["biomarker_confidence"] for p in current_chunk) / len(current_chunk)
        
        chunks.append({
            "text": chunk_text,
            "page_num": page_num,
            "region_type": zone_type,
            "estimated_tokens": current_tokens,
            "biomarker_confidence": chunk_confidence,
            "context": f"Page {page_num}, {zone_type.capitalize()}"
        })
    
    return chunks


def split_text_by_biomarker_density(
    text: str,
    max_tokens: int = 4000,
    page_num: int = 0
) -> List[Dict[str, Any]]:
    """
    Split text into chunks based on biomarker density.
    Used when zone information is not available.
    
    Args:
        text: Text to split
        max_tokens: Maximum tokens per chunk
        page_num: Page number
        
    Returns:
        List of ContentChunk objects
    """
    if not text.strip():
        return []
    
    # If text is already small enough, check its biomarker confidence
    if estimate_tokens(text) <= max_tokens:
        confidence = detect_biomarker_patterns(text)
        return [{
            "text": text,
            "page_num": page_num,
            "region_type": "text",
            "estimated_tokens": estimate_tokens(text),
            "biomarker_confidence": confidence,
            "context": f"Page {page_num}, Full Text"
        }]
    
    # Create a fake zone_data to reuse split_zone_by_biomarker_density
    zone_data = {
        "text": text,
        "page_number": page_num,
        "zone_type": "text"
    }
    
    return split_zone_by_biomarker_density(zone_data, text, max_tokens)


def optimize_content_chunks(
    pages_text_dict: Dict[int, str],
    document_structure: Dict[str, Any],
    max_tokens_per_chunk: int = 4000
) -> List[Dict[str, Any]]:
    """
    Create optimized content chunks based on document structure.
    Simplified approach to avoid token increases.
    
    Args:
        pages_text_dict: Dictionary mapping page numbers to text
        document_structure: Structure information about the document
        max_tokens_per_chunk: Maximum tokens per chunk
        
    Returns:
        List of content chunks
    """
    chunks = []
    
    logging.info(f"Optimizing content from {len(pages_text_dict)} pages into chunks")
    
    # Track original tokens for validation
    original_total_tokens = 0
    optimized_total_tokens = 0
    
    # Process each page independently to avoid duplication
    for page_num, page_text in pages_text_dict.items():
        if not page_text.strip():
            continue
            
        original_page_tokens = estimate_tokens(page_text)
        original_total_tokens += original_page_tokens
        
        # Apply compression
        compressed_text = compress_text_content(page_text)
        compressed_tokens = estimate_tokens(compressed_text)
        
        # If compression didn't help, use original
        if compressed_tokens >= original_page_tokens:
            compressed_text = page_text
            compressed_tokens = original_page_tokens
        
        # Check if we need to split the page
        if compressed_tokens <= max_tokens_per_chunk:
            # Page fits in one chunk
            chunk = {
                "text": compressed_text,
                "page_num": page_num,
                "region_type": "optimized_page",
                "estimated_tokens": compressed_tokens,
                "biomarker_confidence": detect_biomarker_patterns(compressed_text),
                "context": f"Page {page_num}, Full Page"
            }
            chunks.append(chunk)
            optimized_total_tokens += compressed_tokens
        else:
            # Split large page into smaller chunks (no overlap to avoid duplication)
            text_chunks = chunk_text(compressed_text, max_tokens_per_chunk, overlap_tokens=0)
            for i, chunk_text in enumerate(text_chunks):
                chunk_tokens = estimate_tokens(chunk_text)
                chunk = {
                    "text": chunk_text,
                    "page_num": page_num,
                    "region_type": "optimized_chunk",
                    "estimated_tokens": chunk_tokens,
                    "biomarker_confidence": detect_biomarker_patterns(chunk_text),
                    "context": f"Page {page_num}, Chunk {i+1}/{len(text_chunks)}"
                }
                chunks.append(chunk)
                optimized_total_tokens += chunk_tokens
    
    # Sort chunks by page number and biomarker confidence
    chunks.sort(key=lambda x: (x["page_num"], -x["biomarker_confidence"]))
    
    # Calculate and log optimization results
    if original_total_tokens > 0:
        reduction_percentage = (1 - (optimized_total_tokens / original_total_tokens)) * 100
    else:
        reduction_percentage = 0
    
    logging.info(f"Content optimization complete: {len(chunks)} chunks created")
    logging.info(f"Token optimization: {original_total_tokens} -> {optimized_total_tokens} ({reduction_percentage:.2f}% reduction)")
    
    # Validation: Ensure we didn't increase tokens
    if optimized_total_tokens > original_total_tokens:
        logging.warning(f"Token optimization failed - increased tokens by {optimized_total_tokens - original_total_tokens}")
    
    # Save optimization stats for debugging
    if os.environ.get("DEBUG_CONTENT_OPTIMIZATION", "0") == "1":
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logs')
        os.makedirs(debug_dir, exist_ok=True)
        
        debug_file = os.path.join(debug_dir, f"content_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(debug_file, 'w') as f:
            json.dump({
                "original_tokens": original_total_tokens,
                "optimized_tokens": optimized_total_tokens,
                "reduction_percentage": reduction_percentage,
                "chunk_count": len(chunks),
                "validation_passed": optimized_total_tokens <= original_total_tokens,
                "chunk_summary": [
                    {
                        "page_num": c["page_num"],
                        "region_type": c["region_type"],
                        "tokens": c["estimated_tokens"],
                        "confidence": c["biomarker_confidence"]
                    } for c in chunks
                ]
            }, f, indent=2)
    
    return chunks


def enhance_chunk_confidence(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhance chunk confidence scores based on content analysis.
    
    Args:
        chunks: List of content chunks
        
    Returns:
        Enhanced chunks with improved confidence scores
    """
    # Get global stats for normalization
    confidences = [c["biomarker_confidence"] for c in chunks]
    max_conf = max(confidences) if confidences else 0.9
    min_conf = min(confidences) if confidences else 0.1
    
    # Create a copy to avoid modifying the input
    enhanced_chunks = []
    
    for chunk in chunks:
        enhanced_chunk = dict(chunk)
        
        # Additional confidence boosters
        boosters = 0
        
        # Boost confidence for chunks with known biomarker indicators
        text = chunk["text"]
        
        # Check for table-like structures (strong indicator)
        if re.search(r'(?:\|[^|]+\|[^|]+\|)|(?:[^\t]+\t[^\t]+\t[^\t]+)', text):
            boosters += 0.1
        
        # Check for result/test/reference range headers
        if re.search(r'\b(?:TEST|RESULT|REFERENCE RANGE)\b', text, re.IGNORECASE):
            boosters += 0.05
        
        # Check for result flags
        if re.search(r'\b(?:HIGH|LOW|ABNORMAL|NORMAL|H|L|A|N)\b', text, re.IGNORECASE):
            boosters += 0.05
        
        # Apply boosters (capped at 0.99)
        new_confidence = min(0.99, chunk["biomarker_confidence"] + boosters)
        enhanced_chunk["biomarker_confidence"] = new_confidence
        
        enhanced_chunks.append(enhanced_chunk)
    
    return enhanced_chunks 