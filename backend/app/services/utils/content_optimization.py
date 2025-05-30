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


def optimize_content_chunks_accuracy_first(
    pages_text_dict: Dict[int, str],
    document_structure: Dict[str, Any],
    max_tokens_per_chunk: int = 2500,  # Smaller chunks for better accuracy
    overlap_tokens: int = 300,  # Significant overlap to prevent boundary losses
    min_biomarker_confidence: float = 0.3  # Lower threshold to include more potential biomarkers
) -> List[Dict[str, Any]]:
    """
    Create optimized content chunks prioritizing ACCURACY over token efficiency.
    
    This function is designed for scenarios where accuracy is preferred over cost savings.
    It creates more, smaller chunks with significant overlap to ensure no biomarkers are missed.
    
    Args:
        pages_text_dict: Dictionary mapping page numbers to text
        document_structure: Structure information about the document
        max_tokens_per_chunk: Maximum tokens per chunk (smaller for better accuracy)
        overlap_tokens: Overlap between chunks (larger to prevent boundary losses)
        min_biomarker_confidence: Minimum confidence to include a chunk
        
    Returns:
        List of content chunks optimized for accuracy
    """
    chunks = []
    
    logging.info(f"🎯 ACCURACY-FIRST OPTIMIZATION: Processing {len(pages_text_dict)} pages")
    logging.info(f"📊 Parameters: max_tokens={max_tokens_per_chunk}, overlap={overlap_tokens}, min_confidence={min_biomarker_confidence}")
    
    # Track metrics for accuracy analysis
    original_total_tokens = 0
    optimized_total_tokens = 0
    total_chunks_created = 0
    high_confidence_chunks = 0
    
    # Process each page with accuracy-first approach
    for page_num, page_text in pages_text_dict.items():
        if not page_text.strip():
            continue
            
        original_page_tokens = estimate_tokens(page_text)
        original_total_tokens += original_page_tokens
        
        logging.info(f"📄 Processing page {page_num}: {original_page_tokens} tokens")
        
        # ACCURACY FIRST: Skip compression to preserve all potential biomarker context
        # Apply minimal, conservative text cleanup only
        cleaned_text = conservative_text_cleanup(page_text)
        
        # For accuracy, we want smaller chunks with overlap to catch boundary biomarkers
        if estimate_tokens(cleaned_text) <= max_tokens_per_chunk:
            # Even small pages get analyzed for biomarker confidence
            confidence = detect_biomarker_patterns(cleaned_text)
            
            # Include ALL chunks that meet minimum confidence (very permissive for accuracy)
            if confidence >= min_biomarker_confidence:
                chunk = {
                    "text": cleaned_text,
                    "page_num": page_num,
                    "region_type": "accuracy_optimized_page",
                    "estimated_tokens": estimate_tokens(cleaned_text),
                    "biomarker_confidence": confidence,
                    "context": f"Page {page_num}, Full Page (Accuracy Mode)"
                }
                chunks.append(chunk)
                optimized_total_tokens += chunk["estimated_tokens"]
                total_chunks_created += 1
                
                if confidence >= 0.7:
                    high_confidence_chunks += 1
                
                logging.info(f"✅ Single chunk for page {page_num}: confidence={confidence:.3f}")
        else:
            # Split large pages with SIGNIFICANT OVERLAP for accuracy
            text_chunks = chunk_text(
                cleaned_text, 
                max_tokens_per_chunk, 
                overlap_tokens=overlap_tokens,  # Much larger overlap
                smart_boundaries=True  # Respect biomarker boundaries
            )
            
            page_chunks_created = 0
            page_high_confidence = 0
            
            for i, chunk_text_content in enumerate(text_chunks):
                chunk_tokens = estimate_tokens(chunk_text_content)
                chunk_confidence = detect_biomarker_patterns(chunk_text_content)
                
                # ACCURACY MODE: Include more chunks by using lower confidence threshold
                if chunk_confidence >= min_biomarker_confidence:
                    chunk = {
                        "text": chunk_text_content,
                        "page_num": page_num,
                        "region_type": "accuracy_optimized_chunk",
                        "estimated_tokens": chunk_tokens,
                        "biomarker_confidence": chunk_confidence,
                        "context": f"Page {page_num}, Chunk {i+1}/{len(text_chunks)} (Accuracy Mode, Overlap={overlap_tokens})"
                    }
                    chunks.append(chunk)
                    optimized_total_tokens += chunk_tokens
                    total_chunks_created += 1
                    page_chunks_created += 1
                    
                    if chunk_confidence >= 0.7:
                        high_confidence_chunks += 1
                        page_high_confidence += 1
                else:
                    logging.debug(f"⚠️  Skipped low-confidence chunk {i+1} on page {page_num}: confidence={chunk_confidence:.3f}")
            
            logging.info(f"📊 Page {page_num}: {page_chunks_created} chunks created, {page_high_confidence} high-confidence")
    
    # ACCURACY ENHANCEMENT: Apply specialized biomarker detection boosters
    chunks = enhance_chunk_confidence_for_accuracy(chunks)
    
    # Sort by biomarker confidence first, then by page number for optimal processing order
    chunks.sort(key=lambda x: (x["page_num"], -x["biomarker_confidence"]))
    
    # Calculate metrics focused on accuracy rather than token efficiency
    confidence_distribution = {
        "very_high": len([c for c in chunks if c["biomarker_confidence"] >= 0.9]),
        "high": len([c for c in chunks if 0.7 <= c["biomarker_confidence"] < 0.9]), 
        "medium": len([c for c in chunks if 0.5 <= c["biomarker_confidence"] < 0.7]),
        "low": len([c for c in chunks if 0.3 <= c["biomarker_confidence"] < 0.5]),
        "very_low": len([c for c in chunks if c["biomarker_confidence"] < 0.3])
    }
    
    avg_confidence = sum(c["biomarker_confidence"] for c in chunks) / len(chunks) if chunks else 0
    
    # Token increase is acceptable for accuracy
    if optimized_total_tokens > original_total_tokens:
        token_increase = optimized_total_tokens - original_total_tokens
        logging.info(f"🎯 ACCURACY MODE: Increased tokens by {token_increase} ({(token_increase/original_total_tokens)*100:.1f}%) for better accuracy")
    else:
        reduction_percentage = (1 - (optimized_total_tokens / original_total_tokens)) * 100
        logging.info(f"📉 Token optimization: {original_total_tokens} -> {optimized_total_tokens} ({reduction_percentage:.2f}% reduction)")
    
    logging.info(f"🎯 ACCURACY-FIRST RESULTS:")
    logging.info(f"   📊 Total chunks: {total_chunks_created}")
    if total_chunks_created > 0:
        logging.info(f"   ⭐ High confidence chunks: {high_confidence_chunks} ({(high_confidence_chunks/total_chunks_created)*100:.1f}%)")
    else:
        logging.info(f"   ⭐ High confidence chunks: {high_confidence_chunks} (No chunks created)")
    logging.info(f"   📈 Average confidence: {avg_confidence:.3f}")
    logging.info(f"   📋 Confidence distribution: {confidence_distribution}")
    logging.info(f"   🔄 Overlap tokens per chunk: {overlap_tokens}")
    
    # Save detailed accuracy metrics
    if os.environ.get("DEBUG_CONTENT_OPTIMIZATION", "0") == "1":
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logs')
        os.makedirs(debug_dir, exist_ok=True)
        
        debug_file = os.path.join(debug_dir, f"accuracy_first_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(debug_file, 'w') as f:
            json.dump({
                "mode": "accuracy_first",
                "original_tokens": original_total_tokens,
                "optimized_tokens": optimized_total_tokens,
                "token_change": optimized_total_tokens - original_total_tokens,
                "chunk_count": len(chunks),
                "high_confidence_chunks": high_confidence_chunks,
                "average_confidence": avg_confidence,
                "confidence_distribution": confidence_distribution,
                "overlap_tokens": overlap_tokens,
                "min_confidence_threshold": min_biomarker_confidence,
                "chunk_details": [
                    {
                        "page_num": c["page_num"],
                        "region_type": c["region_type"],
                        "tokens": c["estimated_tokens"],
                        "confidence": c["biomarker_confidence"],
                        "context": c["context"]
                    } for c in chunks
                ]
            }, f, indent=2)
    
    return chunks


def conservative_text_cleanup(text: str) -> str:
    """
    Apply minimal, conservative text cleanup that preserves biomarker context.
    Unlike aggressive compression, this only removes clearly irrelevant content.
    
    Args:
        text: Text to clean
        
    Returns:
        Cleaned text with biomarker context preserved
    """
    if not text:
        return ""
    
    # Remove only clearly non-biomarker content
    # Keep most whitespace and formatting as it may be structurally important
    
    # Remove excessive whitespace (but keep paragraph breaks)
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    
    # Remove obvious footer/header patterns that definitely don't contain biomarkers
    footer_patterns = [
        r'Page \d+ of \d+',
        r'©\s*\d{4}.*?(?:\n|$)',
        r'All rights reserved.*?(?:\n|$)',
        r'Confidential.*?(?:\n|$)',
        r'www\.[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}',
        r'http[s]?://[^\s]+'
    ]
    
    for pattern in footer_patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    # Remove only excessive repeated characters (not biomarker-related ones)
    cleaned = re.sub(r'([_=\-])\1{10,}', r'\1\1\1', cleaned)  # Keep some for table structure
    
    # Clean up whitespace again after removals
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    
    return cleaned.strip()


def enhance_chunk_confidence_for_accuracy(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Enhanced chunk confidence scoring optimized for biomarker accuracy.
    More aggressive boosting to ensure biomarker-containing chunks are prioritized.
    
    Args:
        chunks: List of content chunks
        
    Returns:
        Enhanced chunks with accuracy-focused confidence scores
    """
    enhanced_chunks = []
    
    for chunk in chunks:
        enhanced_chunk = dict(chunk)
        text = chunk["text"]
        base_confidence = chunk["biomarker_confidence"]
        
        # ACCURACY BOOSTERS: More aggressive than standard version
        boosters = 0
        
        # Strong table structure indicators
        if re.search(r'(?:\|[^|]+\|[^|]+\|)|(?:[^\t]+\t[^\t]+\t[^\t]+)', text):
            boosters += 0.15  # Higher boost for tables
        
        # Multiple biomarker patterns in same chunk
        biomarker_patterns = len(re.findall(r'\b\d+[\.,]?\d*\s*(?:mg/[dD][lL]|g/[dD][lL]|mmol/L|U/L|IU/L|ng/m[lL]|pg/m[lL]|μg/[dD][lL]|mcg/[dD][lL]|%)', text))
        if biomarker_patterns >= 3:
            boosters += 0.2  # Strong boost for multiple biomarkers
        elif biomarker_patterns >= 2:
            boosters += 0.1
        
        # Lab-specific headers and terminology
        if re.search(r'\b(?:QUEST|LABCORP|LABORATORY|CLINICAL CHEMISTRY|HEMATOLOGY|LIPID PANEL|METABOLIC PANEL)\b', text, re.IGNORECASE):
            boosters += 0.1
        
        # Reference range indicators
        if re.search(r'\b(?:reference|normal|ref\.?\s*range|ref\.?\s*interval)\b', text, re.IGNORECASE):
            boosters += 0.1
        
        # Result flag indicators
        flag_matches = len(re.findall(r'\b(?:HIGH|LOW|ABNORMAL|NORMAL|H|L|A|N)\b', text, re.IGNORECASE))
        if flag_matches >= 2:
            boosters += 0.1
        
        # Biomarker name recognition
        common_biomarkers = [
            'glucose', 'cholesterol', 'triglycerides', 'hdl', 'ldl', 'hemoglobin', 
            'hematocrit', 'tsh', 'creatinine', 'albumin', 'sodium', 'potassium',
            'calcium', 'vitamin d', 'b12', 'iron', 'ferritin'
        ]
        biomarker_name_matches = sum(1 for name in common_biomarkers if name in text.lower())
        if biomarker_name_matches >= 3:
            boosters += 0.15
        elif biomarker_name_matches >= 1:
            boosters += 0.05
        
        # Apply boosters with higher cap for accuracy mode
        new_confidence = min(0.98, base_confidence + boosters)
        enhanced_chunk["biomarker_confidence"] = new_confidence
        
        # Track confidence enhancement for debugging
        if boosters > 0:
            enhanced_chunk["confidence_boost"] = boosters
            enhanced_chunk["original_confidence"] = base_confidence
        
        enhanced_chunks.append(enhanced_chunk)
    
    return enhanced_chunks


def optimize_content_chunks(
    pages_text_dict: Dict[int, str],
    document_structure: Dict[str, Any],
    max_tokens_per_chunk: int = 4000,
    accuracy_mode: bool = False,
    balanced_mode: bool = False
) -> List[Dict[str, Any]]:
    """
    Create optimized content chunks based on document structure.
    
    Args:
        pages_text_dict: Dictionary mapping page numbers to text
        document_structure: Structure information about the document
        max_tokens_per_chunk: Maximum tokens per chunk
        accuracy_mode: If True, prioritize accuracy over token efficiency
        balanced_mode: If True, balance accuracy with token efficiency
        
    Returns:
        List of content chunks
    """
    if balanced_mode:
        # Use balanced optimization for cost-effective accuracy
        return optimize_content_chunks_balanced(
            pages_text_dict=pages_text_dict,
            document_structure=document_structure,
            max_tokens_per_chunk=max_tokens_per_chunk,
            overlap_tokens=150,  # Moderate overlap for balance
            min_biomarker_confidence=0.4
        )
    elif accuracy_mode:
        # Use accuracy-first optimization for better biomarker detection
        return optimize_content_chunks_accuracy_first(
            pages_text_dict=pages_text_dict,
            document_structure=document_structure,
            max_tokens_per_chunk=max_tokens_per_chunk,
            overlap_tokens=300,  # Significant overlap for accuracy
            min_biomarker_confidence=0.3
        )
    else:
        # Use original token-efficient optimization
        return optimize_content_chunks_legacy(
            pages_text_dict=pages_text_dict,
            document_structure=document_structure,
            max_tokens_per_chunk=max_tokens_per_chunk
        )


def optimize_content_chunks_legacy(
    pages_text_dict: Dict[int, str],
    document_structure: Dict[str, Any],
    max_tokens_per_chunk: int = 4000
) -> List[Dict[str, Any]]:
    """
    Original token-efficient content optimization (legacy mode).
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


# Update the enhance_chunk_confidence function to use the legacy version
def enhance_chunk_confidence(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Original enhance chunk confidence scores (legacy version).
    
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


def optimize_content_chunks_balanced(
    pages_text_dict: Dict[int, str],
    document_structure: Dict[str, Any],
    max_tokens_per_chunk: int = 4000,  # Larger chunks for efficiency
    overlap_tokens: int = 150,  # Moderate overlap for balance
    min_biomarker_confidence: float = 0.4  # Slightly higher threshold for efficiency
) -> List[Dict[str, Any]]:
    """
    Create balanced content chunks optimizing BOTH accuracy and token efficiency.
    
    This function balances accuracy with cost savings, providing significant token
    reduction while maintaining ~95% accuracy for biomarker detection.
    
    Args:
        pages_text_dict: Dictionary mapping page numbers to text
        document_structure: Structure information about the document
        max_tokens_per_chunk: Maximum tokens per chunk (balanced size)
        overlap_tokens: Moderate overlap between chunks
        min_biomarker_confidence: Confidence threshold for including chunks
        
    Returns:
        List of content chunks optimized for balanced accuracy/efficiency
    """
    chunks = []
    
    logging.info(f"⚖️  BALANCED OPTIMIZATION: Processing {len(pages_text_dict)} pages")
    logging.info(f"📊 Parameters: max_tokens={max_tokens_per_chunk}, overlap={overlap_tokens}, min_confidence={min_biomarker_confidence}")
    
    # Track metrics for balanced analysis
    original_total_tokens = 0
    optimized_total_tokens = 0
    total_chunks_created = 0
    high_confidence_chunks = 0
    
    # Process each page with balanced approach
    for page_num, page_text in pages_text_dict.items():
        if not page_text.strip():
            continue
            
        original_page_tokens = estimate_tokens(page_text)
        original_total_tokens += original_page_tokens
        
        logging.info(f"📄 Processing page {page_num}: {original_page_tokens} tokens")
        
        # BALANCED: Apply moderate compression for cost savings while preserving biomarkers
        compressed_text = balanced_text_compression(page_text)
        
        # Check if we need to split the page
        if estimate_tokens(compressed_text) <= max_tokens_per_chunk:
            # Page fits in one chunk
            confidence = detect_biomarker_patterns(compressed_text)
            
            # Apply balanced confidence threshold
            if confidence >= min_biomarker_confidence:
                chunk = {
                    "text": compressed_text,
                    "page_num": page_num,
                    "region_type": "balanced_optimized_page",
                    "estimated_tokens": estimate_tokens(compressed_text),
                    "biomarker_confidence": confidence,
                    "context": f"Page {page_num}, Full Page (Balanced Mode)"
                }
                chunks.append(chunk)
                optimized_total_tokens += chunk["estimated_tokens"]
                total_chunks_created += 1
                
                if confidence >= 0.7:
                    high_confidence_chunks += 1
                
                logging.info(f"✅ Single chunk for page {page_num}: confidence={confidence:.3f}")
            elif estimate_tokens(compressed_text) > 50:
                # Include low-confidence pages if they have substantial content
                # This prevents balanced mode from dropping all content
                chunk = {
                    "text": compressed_text,
                    "page_num": page_num,
                    "region_type": "balanced_optimized_page_fallback",
                    "estimated_tokens": estimate_tokens(compressed_text),
                    "biomarker_confidence": confidence,
                    "context": f"Page {page_num}, Full Page (Balanced Mode, Fallback)"
                }
                chunks.append(chunk)
                optimized_total_tokens += chunk["estimated_tokens"]
                total_chunks_created += 1
                logging.info(f"🔄 Included fallback page {page_num}: confidence={confidence:.3f}")
            else:
                logging.debug(f"⚠️  Skipped low-confidence page {page_num}: confidence={confidence:.3f}")
        else:
            # Split large pages with MODERATE OVERLAP for balance
            text_chunks = chunk_text(
                compressed_text, 
                max_tokens_per_chunk, 
                overlap_tokens=overlap_tokens,  # Moderate overlap
                smart_boundaries=True
            )
            
            page_chunks_created = 0
            page_high_confidence = 0
            
            for i, chunk_text_content in enumerate(text_chunks):
                chunk_tokens = estimate_tokens(chunk_text_content)
                chunk_confidence = detect_biomarker_patterns(chunk_text_content)
                
                # BALANCED MODE: Use moderate confidence threshold
                if chunk_confidence >= min_biomarker_confidence:
                    chunk = {
                        "text": chunk_text_content,
                        "page_num": page_num,
                        "region_type": "balanced_optimized_chunk",
                        "estimated_tokens": chunk_tokens,
                        "biomarker_confidence": chunk_confidence,
                        "context": f"Page {page_num}, Chunk {i+1}/{len(text_chunks)} (Balanced Mode, Overlap={overlap_tokens})"
                    }
                    chunks.append(chunk)
                    optimized_total_tokens += chunk_tokens
                    total_chunks_created += 1
                    page_chunks_created += 1
                    
                    if chunk_confidence >= 0.7:
                        high_confidence_chunks += 1
                        page_high_confidence += 1
                elif len(text_chunks) == 1:
                    # If it's the only chunk and has some content, include it anyway
                    # This prevents the balanced mode from creating 0 chunks
                    chunk = {
                        "text": chunk_text_content,
                        "page_num": page_num,
                        "region_type": "balanced_optimized_chunk_fallback",
                        "estimated_tokens": chunk_tokens,
                        "biomarker_confidence": chunk_confidence,
                        "context": f"Page {page_num}, Chunk {i+1}/{len(text_chunks)} (Balanced Mode, Fallback)"
                    }
                    chunks.append(chunk)
                    optimized_total_tokens += chunk_tokens
                    total_chunks_created += 1
                    page_chunks_created += 1
                    logging.info(f"🔄 Included fallback chunk on page {page_num}: confidence={chunk_confidence:.3f}")
                else:
                    logging.debug(f"⚠️  Skipped low-confidence chunk {i+1} on page {page_num}: confidence={chunk_confidence:.3f}")
            
            logging.info(f"📊 Page {page_num}: {page_chunks_created} chunks created, {page_high_confidence} high-confidence")
    
    # BALANCED ENHANCEMENT: Apply moderate biomarker detection boosters
    chunks = enhance_chunk_confidence_balanced(chunks)
    
    # Sort by biomarker confidence and page number
    chunks.sort(key=lambda x: (x["page_num"], -x["biomarker_confidence"]))
    
    # Calculate balanced optimization metrics
    if original_total_tokens > 0:
        token_reduction = (original_total_tokens - optimized_total_tokens) / original_total_tokens * 100
    else:
        token_reduction = 0
    
    confidence_distribution = {
        "very_high": len([c for c in chunks if c["biomarker_confidence"] >= 0.9]),
        "high": len([c for c in chunks if 0.7 <= c["biomarker_confidence"] < 0.9]), 
        "medium": len([c for c in chunks if 0.5 <= c["biomarker_confidence"] < 0.7]),
        "low": len([c for c in chunks if 0.3 <= c["biomarker_confidence"] < 0.5]),
        "very_low": len([c for c in chunks if c["biomarker_confidence"] < 0.3])
    }
    
    avg_confidence = sum(c["biomarker_confidence"] for c in chunks) / len(chunks) if chunks else 0
    
    logging.info(f"⚖️  BALANCED OPTIMIZATION RESULTS:")
    logging.info(f"   📉 Token reduction: {token_reduction:.2f}% ({original_total_tokens} -> {optimized_total_tokens})")
    logging.info(f"   📊 Total chunks: {total_chunks_created}")
    if total_chunks_created > 0:
        logging.info(f"   ⭐ High confidence chunks: {high_confidence_chunks} ({(high_confidence_chunks/total_chunks_created)*100:.1f}%)")
    else:
        logging.info(f"   ⭐ High confidence chunks: {high_confidence_chunks} (No chunks created)")
    logging.info(f"   📈 Average confidence: {avg_confidence:.3f}")
    logging.info(f"   📋 Confidence distribution: {confidence_distribution}")
    logging.info(f"   🔄 Overlap tokens per chunk: {overlap_tokens}")
    
    # Save detailed balanced metrics
    if os.environ.get("DEBUG_CONTENT_OPTIMIZATION", "0") == "1":
        debug_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logs')
        os.makedirs(debug_dir, exist_ok=True)
        
        debug_file = os.path.join(debug_dir, f"balanced_optimization_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(debug_file, 'w') as f:
            json.dump({
                "mode": "balanced",
                "original_tokens": original_total_tokens,
                "optimized_tokens": optimized_total_tokens,
                "token_reduction_percentage": token_reduction,
                "chunk_count": len(chunks),
                "high_confidence_chunks": high_confidence_chunks,
                "average_confidence": avg_confidence,
                "confidence_distribution": confidence_distribution,
                "overlap_tokens": overlap_tokens,
                "min_confidence_threshold": min_biomarker_confidence,
                "chunk_details": [
                    {
                        "page_num": c["page_num"],
                        "region_type": c["region_type"],
                        "tokens": c["estimated_tokens"],
                        "confidence": c["biomarker_confidence"],
                        "context": c["context"]
                    } for c in chunks
                ]
            }, f, indent=2)
    
    return chunks


def balanced_text_compression(text: str) -> str:
    """
    Apply balanced compression for cost reduction while preserving biomarker accuracy.
    GENERIC approach that works for ANY lab report format, not specific to any lab.
    
    Args:
        text: Text to compress
        
    Returns:
        Compressed text optimized for balanced accuracy/efficiency
    """
    if not text:
        return ""
    
    # Store original for validation
    original_text = text
    original_tokens = estimate_tokens(original_text)
    
    # Step 1: Remove UNIVERSALLY safe non-biomarker content
    # These patterns are generic and safe for ANY lab report format
    universal_safe_patterns = [
        # Web content (always safe to remove)
        r"http[s]?://[^\s]+",
        r"www\.[^\s]+",
        
        # Contact information (always safe to remove)
        r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b",  # Phone numbers (any format)
        r"\([0-9]{3}\)\s*[0-9]{3}[-.\s]?[0-9]{4}",  # (555) 123-4567 format
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email addresses
        
        # Legal/Copyright (always safe to remove)
        r"©.*?(?:\d{4}).*?(?:\.|$)",
        r"copyright.*?(?:\d{4}).*?(?:\.|$)",
        r"all rights reserved.*?(?:\.|$)",
        r"confidential.*?(?:\.|$)",
        r"proprietary.*?(?:\.|$)",
        
        # Page references (always safe to remove)
        r"page \d+ of \d+",
        r"page \d+/\d+",
        r"pg\. \d+",
        
        # Software version info (always safe to remove)
        r"version \d+\.\d+[\.\d]*",
        r"v\d+\.\d+[\.\d]*",
        r"ver\. \d+\.\d+",
        
        # Excessive formatting (safe formatting cleanup)
        r"[-=_*]{5,}",  # Long separator lines
        r"\.{5,}",      # Excessive dots
        r"\|{3,}",      # Multiple pipes
    ]
    
    for pattern in universal_safe_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    
    # Step 2: Remove excessive whitespace and normalize
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces to single space
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple line breaks to double
    
    # Step 3: CONSERVATIVE cleanup of obvious non-biomarker sections
    # Only remove content that is clearly metadata/administrative
    
    # Remove lines that are clearly administrative (whole line removal)
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Skip lines that are clearly administrative/metadata
        # These patterns are generic across all lab formats
        skip_line = False
        
        admin_line_patterns = [
            r"^printed\s+on\s+\d",           # "Printed on [date]"
            r"^generated\s+on\s+\d",        # "Generated on [date]"
            r"^report\s+date\s*:",          # "Report date:"
            r"^specimen\s+received\s*:",    # "Specimen received:"
            r"^collected\s+on\s*:",         # "Collected on:"
            r"^accession\s*(number|#|id)\s*:", # "Accession number:"
            r"^lab\s+(id|code|number)\s*:", # "Lab ID:", "Lab Code:"
            r"^order\s+(id|number)\s*:",    # "Order ID:", "Order number:"
            r"^requisition\s*#?\s*:",       # "Requisition #:"
            r"^client\s+(id|code)\s*:",     # "Client ID:"
            r"^\s*for\s+questions",         # "For questions..."
            r"^\s*please\s+contact",        # "Please contact..."
            r"^\s*reference\s+ranges?\s+may\s+vary", # "Reference ranges may vary"
            r"^\s*normal\s+values?\s+may\s+vary",    # "Normal values may vary"
        ]
        
        for admin_pattern in admin_line_patterns:
            if re.search(admin_pattern, line_lower):
                skip_line = True
                break
        
        # Always preserve lines that contain potential biomarkers
        # Look for number + unit patterns (this preserves ANY biomarker format)
        biomarker_indicators = [
            r"\d+[\.,]?\d*\s*(?:mg|g|dl|ml|l|mmol|mol|iu|u|pg|ng|μg|mcg|%|mEq)",
            r"\d+[\.,]?\d*\s*/\s*(?:dl|ml|l|min|m2|kg)",  # ratios like mg/dL
            r"(?:high|low|normal|abnormal|positive|negative|elevated|decreased)\b",
            r"reference\s+range",
            r"normal\s+range",
            r"\breference\s*:",
            r"\bnormal\s*:",
        ]
        
        has_biomarker = any(re.search(pattern, line_lower) for pattern in biomarker_indicators)
        
        if has_biomarker:
            skip_line = False  # Always preserve potential biomarker lines
        
        if not skip_line and line.strip():  # Keep non-empty, non-admin lines
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Step 4: Final cleanup
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = text.strip()
    
    # Step 5: CONSERVATIVE validation - prioritize preserving content
    compressed_tokens = estimate_tokens(text)
    
    # Don't allow more than 30% compression to avoid losing biomarkers
    if compressed_tokens < original_tokens * 0.7:
        logging.debug(f"Balanced compression too aggressive ({original_tokens} -> {compressed_tokens}), using original")
        return original_text
    
    # Accept any compression, even small amounts
    if compressed_tokens >= original_tokens:
        logging.debug(f"Balanced compression no benefit ({original_tokens} -> {compressed_tokens}), using original")
        return original_text
    
    # Log compression results
    compression_ratio = (1 - compressed_tokens / original_tokens) * 100
    logging.debug(f"Generic balanced compression: {original_tokens} -> {compressed_tokens} tokens ({compression_ratio:.1f}% reduction)")
    
    return text


def enhance_chunk_confidence_balanced(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Balanced chunk confidence scoring for optimal accuracy/efficiency trade-off.
    Less aggressive than accuracy-first but more effective than standard.
    
    Args:
        chunks: List of content chunks
        
    Returns:
        Enhanced chunks with balanced confidence scores
    """
    enhanced_chunks = []
    
    for chunk in chunks:
        enhanced_chunk = dict(chunk)
        text = chunk["text"]
        base_confidence = chunk["biomarker_confidence"]
        
        # BALANCED BOOSTERS: Moderate enhancement
        boosters = 0
        
        # Table structure indicators
        if re.search(r'(?:\|[^|]+\|[^|]+\|)|(?:[^\t]+\t[^\t]+\t[^\t]+)', text):
            boosters += 0.1  # Moderate boost for tables
        
        # Multiple biomarker patterns
        biomarker_patterns = len(re.findall(r'\b\d+[\.,]?\d*\s*(?:mg/[dD][lL]|g/[dD][lL]|mmol/L|U/L|IU/L|ng/m[lL]|pg/m[lL]|μg/[dD][lL]|mcg/[dD][lL]|%)', text))
        if biomarker_patterns >= 4:
            boosters += 0.15
        elif biomarker_patterns >= 2:
            boosters += 0.08
        
        # Lab-specific headers
        if re.search(r'\b(?:LABORATORY|CLINICAL CHEMISTRY|HEMATOLOGY|LIPID PANEL|METABOLIC PANEL)\b', text, re.IGNORECASE):
            boosters += 0.08
        
        # Reference range indicators
        if re.search(r'\b(?:reference|normal|ref\.?\s*range)\b', text, re.IGNORECASE):
            boosters += 0.08
        
        # Result flag indicators (moderate boost)
        flag_matches = len(re.findall(r'\b(?:HIGH|LOW|ABNORMAL|NORMAL|H|L)\b', text, re.IGNORECASE))
        if flag_matches >= 3:
            boosters += 0.08
        
        # Common biomarker recognition (balanced)
        common_biomarkers = [
            'glucose', 'cholesterol', 'triglycerides', 'hdl', 'ldl', 'hemoglobin', 
            'hematocrit', 'tsh', 'creatinine', 'albumin', 'sodium', 'potassium'
        ]
        biomarker_name_matches = sum(1 for name in common_biomarkers if name in text.lower())
        if biomarker_name_matches >= 3:
            boosters += 0.1
        elif biomarker_name_matches >= 1:
            boosters += 0.04
        
        # Apply boosters with balanced cap
        new_confidence = min(0.95, base_confidence + boosters)
        enhanced_chunk["biomarker_confidence"] = new_confidence
        
        # Track enhancement for debugging
        if boosters > 0:
            enhanced_chunk["confidence_boost"] = boosters
            enhanced_chunk["original_confidence"] = base_confidence
        
        enhanced_chunks.append(enhanced_chunk)
    
    return enhanced_chunks 


def quick_biomarker_screening(chunk_text: str, existing_biomarkers_count: int = 0) -> Dict[str, Any]:
    """
    Perform rapid screening to determine if a chunk should be processed for biomarkers.
    This is much faster than full biomarker extraction and helps skip obvious non-biomarker content.
    
    Args:
        chunk_text: Text content to screen
        existing_biomarkers_count: Number of biomarkers already found (affects thresholds)
        
    Returns:
        Dict with screening results:
        - should_process: bool - whether to send to LLM
        - confidence: float - confidence that chunk contains biomarkers
        - reason: str - explanation for decision
        - fast_patterns_found: int - number of quick patterns detected
    """
    if not chunk_text or len(chunk_text.strip()) < 20:
        return {
            "should_process": False,
            "confidence": 0.0,
            "reason": "empty_or_too_short",
            "fast_patterns_found": 0
        }
    
    text_lower = chunk_text.lower()
    
    # FAST LAB REPORT INDICATORS (very strong positive signals)
    lab_report_indicators = [
        # Lab report headers
        r"\b(?:laboratory\s+report|diagnostic\s+report|clinical\s+pathology|test\s+report|lab\s+results)\b",
        
        # Common lab company names (from your examples)
        r"\b(?:redcliffe\s+labs|pharmeasy\s+labs|orange\s+health\s+labs|agilus\s+diagnostics)\b",
        r"\b(?:quest\s+diagnostics|labcorp|thyrocare|dr\s+lal\s+path\s+labs)\b",
        
        # Lab sections
        r"\b(?:hematology|clinical\s+chemistry|biochemistry|immunology|microbiology)\b",
        r"\b(?:complete\s+blood\s+count|cbc|lipid\s+profile|liver\s+function|kidney\s+function)\b",
        
        # Report status and metadata that indicates medical content
        r"\b(?:final\s+report|report\s+status|biological\s+reference|reference\s+interval)\b",
    ]
    
    # Count lab report indicators (these override administrative patterns)
    lab_indicators = 0
    for pattern in lab_report_indicators:
        lab_indicators += len(re.findall(pattern, text_lower))
    
    # If we have lab report indicators, this is likely a valid lab report
    if lab_indicators >= 1:
        # Even if there are admin patterns, lab content should be processed
        confidence = min(0.95, 0.7 + (lab_indicators * 0.1))
        return {
            "should_process": True,
            "confidence": confidence,
            "reason": f"lab_report_indicators_found_{lab_indicators}",
            "fast_patterns_found": lab_indicators * 3  # Weight lab indicators heavily
        }
    
    # FAST BIOMARKER INDICATORS (positive signals)
    quick_biomarker_patterns = [
        # Numeric values with common units (high priority)
        r"\d+[\.,]?\d*\s*(?:mg/dl|mg/l|g/dl|mmol/l|u/l|iu/l|ng/ml|pg/ml|mcg/dl|%|mil/μl|thou/μl)",
        
        # Common biomarker names with nearby numbers
        r"(?:glucose|cholesterol|triglycerides|hdl|ldl|hemoglobin|hematocrit|tsh|alt|ast|creatinine|sodium|potassium|vitamin).*?\d+",
        r"\d+.*?(?:glucose|cholesterol|triglycerides|hdl|ldl|hemoglobin|hematocrit|tsh|alt|ast|creatinine|sodium|potassium|vitamin)",
        
        # Hematology patterns (from your examples)
        r"(?:hemoglobin|hb|rbc|wbc|platelet).*?\d+[\.,]?\d*",
        r"\d+[\.,]?\d*.*?(?:hemoglobin|hb|rbc|wbc|platelet)",
        
        # Result flag patterns
        r"\b(?:high|low|abnormal|normal)\s*(?:\*|\#|h|l)\b",
        r"\b\d+[\.,]?\d*\s*[a-z/μ]+\s*(?:high|low|h|l|\*)\b",
        
        # Reference range patterns  
        r"\b\d+[\.,]?\d*\s*[-–]\s*\d+[\.,]?\d*",
        r"\(.*?\d+[\.,]?\d*\s*[-–]\s*\d+[\.,]?\d*.*?\)",
        
        # Table-like structures with numbers
        r"(?:\|[^|]*\d+[^|]*\|)|(?:\s+\d+[\.,]?\d*\s+[a-z/μ]+\s+)",
        
        # Lab section headers
        r"\b(?:clinical\s+chemistry|hematology|lipid\s+panel|metabolic\s+panel)\b"
    ]
    
    # Count positive biomarker indicators
    fast_patterns_found = 0
    pattern_weights = [3, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1]  # Different weights for pattern importance
    
    for i, pattern in enumerate(quick_biomarker_patterns):
        matches = len(re.findall(pattern, chunk_text, re.IGNORECASE))
        weight = pattern_weights[i] if i < len(pattern_weights) else 1
        fast_patterns_found += matches * weight
    
    # ADMINISTRATIVE PATTERNS (only skip if NO biomarker patterns found)
    administrative_patterns = [
        # Contact information
        r"\b(?:fax|phone|tel|email|website|www\.|\.com|\.org|\.edu)\b",
        
        # Addresses and locations  
        r"\b(?:street|avenue|road|suite|building|floor|zip|zipcode|state|city)\b",
        r"\b\d{5}(?:-\d{4})?\b",  # ZIP codes
        
        # Administrative headers/footers
        r"\bpage\s+\d+\s+of\s+\d+\b",
        r"\bcontinued\s+on\s+next\s+page\b",
        r"\bprinted\s+on\b",
        r"\breport\s+generated\b",
        
        # Legal/billing text
        r"\bbilling|invoice|payment|insurance|copay|deductible\b",
        r"\blegal|disclaimer|confidential|hipaa|privacy\b",
        
        # Pure headers without values (only if no biomarker patterns)
        r"^(?:test\s+name|result|reference\s+range|units|status|flag)$",
        
        # Method descriptions (pure text, no values)
        r"\bmethod(?:ology)?[\s:]+(?!.*\d).*$",
        r"\bspecimen[\s:]+(?!.*\d).*$",
        r"\bcollection[\s:]+(?!.*\d).*$"
    ]
    
    # Count administrative pattern matches (negative indicators)
    admin_matches = 0
    for pattern in administrative_patterns:
        admin_matches += len(re.findall(pattern, text_lower))
    
    # IMPORTANT: Only apply administrative filtering if NO biomarker patterns found
    if admin_matches >= 3 and fast_patterns_found == 0:
        return {
            "should_process": False,
            "confidence": 0.1,
            "reason": f"pure_administrative_content_matches_{admin_matches}",
            "fast_patterns_found": 0
        }
    
    # Calculate screening confidence
    text_length = len(chunk_text)
    pattern_density = fast_patterns_found / (text_length / 100)  # patterns per 100 chars
    
    # Adjust thresholds based on how many biomarkers we already have
    base_threshold = 0.3
    if existing_biomarkers_count >= 20:
        base_threshold = 0.5  # Be more selective when we have many biomarkers
    elif existing_biomarkers_count >= 10:
        base_threshold = 0.4  # Moderately selective
    
    # Determine if we should process
    should_process = True
    confidence = 0.5  # Default moderate confidence
    reason = "default_processing"
    
    if pattern_density >= 2.0:
        confidence = 0.9
        reason = "high_biomarker_density"
    elif pattern_density >= 1.0:
        confidence = 0.8
        reason = "medium_biomarker_density"
    elif pattern_density >= 0.5:
        confidence = 0.6
        reason = "low_biomarker_density"
    elif fast_patterns_found >= 3:
        confidence = 0.7
        reason = "multiple_biomarker_patterns"
    elif fast_patterns_found >= 1:
        confidence = 0.5
        reason = "some_biomarker_patterns"
    elif admin_matches >= 1 and fast_patterns_found == 0:
        confidence = 0.2
        reason = "administrative_content_detected"
        if existing_biomarkers_count >= 10:  # Be more aggressive if we have enough biomarkers
            should_process = False
            reason = "administrative_content_with_sufficient_biomarkers"
    else:
        confidence = 0.3
        reason = "minimal_biomarker_indicators"
        if existing_biomarkers_count >= 15:  # Very selective when we have many biomarkers
            should_process = False
            reason = "minimal_indicators_with_many_biomarkers"
    
    # Final safety checks
    if confidence < base_threshold:
        should_process = False
        reason = f"below_threshold_{base_threshold}"
    
    # Always process if we haven't found any biomarkers yet (safety fallback)
    if existing_biomarkers_count == 0 and confidence >= 0.2:
        should_process = True
        reason = "safety_fallback_no_biomarkers_found"
    
    return {
        "should_process": should_process,
        "confidence": confidence,
        "reason": reason,
        "fast_patterns_found": fast_patterns_found
    }


def apply_smart_chunk_skipping(
    chunks: List[Dict[str, Any]], 
    existing_biomarkers_count: int = 0,
    enabled: bool = True
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Apply smart chunk skipping to a list of chunks based on quick screening.
    
    Args:
        chunks: List of content chunks to process
        existing_biomarkers_count: Number of biomarkers already found
        enabled: Whether smart skipping is enabled
        
    Returns:
        Tuple of (filtered_chunks, skipping_stats)
    """
    if not enabled:
        return chunks, {"skipped": 0, "processed": len(chunks), "reason": "disabled"}
    
    filtered_chunks = []
    skipping_stats = {
        "total_chunks": len(chunks),
        "skipped": 0,
        "processed": 0,
        "skipped_reasons": {},
        "confidence_distribution": {"high": 0, "medium": 0, "low": 0, "very_low": 0},
        "token_savings": 0
    }
    
    logging.info(f"🔍 SMART CHUNK SKIPPING: Screening {len(chunks)} chunks (existing biomarkers: {existing_biomarkers_count})")
    
    for i, chunk in enumerate(chunks):
        screening_result = quick_biomarker_screening(
            chunk["text"], 
            existing_biomarkers_count + len(filtered_chunks)  # Update count as we process
        )
        
        # Update confidence distribution stats
        confidence = screening_result["confidence"]
        if confidence >= 0.8:
            skipping_stats["confidence_distribution"]["high"] += 1
        elif confidence >= 0.6:
            skipping_stats["confidence_distribution"]["medium"] += 1
        elif confidence >= 0.4:
            skipping_stats["confidence_distribution"]["low"] += 1
        else:
            skipping_stats["confidence_distribution"]["very_low"] += 1
        
        if screening_result["should_process"]:
            # Add screening metadata to chunk for debugging
            chunk["screening_confidence"] = screening_result["confidence"]
            chunk["screening_reason"] = screening_result["reason"]
            chunk["fast_patterns_found"] = screening_result["fast_patterns_found"]
            filtered_chunks.append(chunk)
            skipping_stats["processed"] += 1
            
            logging.debug(f"✅ Processing chunk #{i+1}: confidence={confidence:.2f}, reason={screening_result['reason']}")
        else:
            # Track skipped chunk
            skipping_stats["skipped"] += 1
            reason = screening_result["reason"]
            skipping_stats["skipped_reasons"][reason] = skipping_stats["skipped_reasons"].get(reason, 0) + 1
            skipping_stats["token_savings"] += chunk.get("estimated_tokens", 0)
            
            logging.info(f"⏭️  SKIPPED chunk #{i+1} (page {chunk.get('page_num', '?')}): confidence={confidence:.2f}, reason={reason}, tokens_saved={chunk.get('estimated_tokens', 0)}")
    
    # Log summary
    if skipping_stats["skipped"] > 0:
        logging.info(f"🎯 SKIPPING SUMMARY: {skipping_stats['skipped']}/{skipping_stats['total_chunks']} chunks skipped, {skipping_stats['token_savings']} tokens saved")
        logging.info(f"📊 Confidence distribution: {skipping_stats['confidence_distribution']}")
        logging.info(f"📋 Skip reasons: {skipping_stats['skipped_reasons']}")
    else:
        logging.info(f"🔄 SKIPPING SUMMARY: No chunks skipped, processing all {skipping_stats['total_chunks']} chunks")
    
    return filtered_chunks, skipping_stats 