"""
Document Analyzer Module

This module provides functionality for analyzing PDF document structure,
optimizing content for extraction, and managing extraction context.
"""
from typing import Dict, List, Optional, Any, TypedDict, Union, Tuple
import logging
import re
from pathlib import Path
import os

# Import utilities
from app.services.utils.structure_detection import (
    detect_tables,
    detect_document_zones,
    detect_document_type,
    detect_biomarker_regions
)
from app.services.utils.content_optimization import (
    estimate_tokens,
    optimize_content_chunks,
    detect_biomarker_patterns,
    enhance_chunk_confidence,
    enhance_chunk_confidence_for_accuracy,
    enhance_chunk_confidence_balanced
)
from app.services.utils.context_management import (
    create_adaptive_prompt as utils_create_adaptive_prompt,
    update_extraction_context as utils_update_extraction_context,
    create_default_extraction_context as utils_create_default_extraction_context,
    filter_biomarkers_by_confidence
)
from app.services.utils.smart_prompting import smart_prompt_engine

# Try to import dependencies, with graceful fallback
try:
    import pdfplumber
except ImportError:
    logging.warning("pdfplumber not installed. Document structure analysis will be limited.")
    pdfplumber = None

# Type definitions
class TableInfo(TypedDict):
    """Information about a detected table"""
    bbox: List[float]  # Bounding box coordinates [x0, y0, x1, y1]
    page_number: int
    rows: int
    cols: int
    confidence: float
    index: int  # Index of table on the page


class ZoneInfo(TypedDict):
    """Information about a document zone"""
    zone_type: str  # "header", "footer", "content", "address", etc.
    bbox: List[float]
    confidence: float


class DocumentStructure(TypedDict):
    """Complete document structure information"""
    document_type: Optional[str]  # E.g., "quest_diagnostics", "labcorp"
    page_zones: Dict[int, Dict[str, ZoneInfo]]  # Page number -> zone information
    tables: Dict[int, List[TableInfo]]  # Page number -> list of tables
    biomarker_regions: List[Dict[str, Any]]  # Identified biomarker-containing regions
    confidence: float  # Overall structure analysis confidence


class ContentChunk(TypedDict):
    """Optimized text chunk for extraction"""
    text: str
    page_num: int
    region_type: str  # E.g., "table", "list", "text"
    estimated_tokens: int
    biomarker_confidence: float
    context: str  # Surrounding context information


class ExtractionContext(TypedDict):
    """Context for managing extraction state"""
    known_biomarkers: Dict[str, Dict[str, Any]]
    extraction_patterns: List[str]
    section_context: Dict[str, str]
    call_count: int
    token_usage: Dict[str, int]
    confidence_threshold: float


def debug_document_structure(document_structure, output_file=None):
    """
    Print or save a detailed breakdown of the document structure analysis results.
    Useful for debugging and validating structure detection.
    
    Args:
        document_structure: The DocumentStructure object
        output_file: Optional file path to save results
    """
    debug_output = [
        "=== DOCUMENT STRUCTURE ANALYSIS RESULTS ===",
        f"Document Type: {document_structure.get('document_type', 'Unknown')}",
        f"Analysis Confidence: {document_structure.get('confidence', 0):.2f}",
        "\n--- DETECTED TABLES ---"
    ]
    
    tables = document_structure.get('tables', {})
    for page_num, page_tables in tables.items():
        debug_output.append(f"Page {page_num}: {len(page_tables)} tables detected")
        for i, table in enumerate(page_tables):
            debug_output.append(f"  Table {i+1}: Rows={len(table.get('cells', []))}, "
                               f"Confidence={table.get('confidence', 0):.2f}")
    
    debug_output.append("\n--- PAGE ZONES ---")
    page_zones = document_structure.get('page_zones', {})
    for page_num, zones in page_zones.items():
        zone_types = [f"{zone}: {data.get('confidence', 0):.2f}" 
                     for zone, data in zones.items()]
        debug_output.append(f"Page {page_num}: {', '.join(zone_types)}")
    
    debug_output.append("\n--- BIOMARKER REGIONS ---")
    regions = document_structure.get('biomarker_regions', [])
    for i, region in enumerate(regions):
        debug_output.append(f"Region {i+1}: Page {region.get('page_num')}, "
                           f"Type: {region.get('region_type')}, "
                           f"Confidence: {region.get('biomarker_confidence', 0):.2f}")
    
    debug_str = "\n".join(debug_output)
    
    if output_file:
        with open(output_file, 'w') as f:
            f.write(debug_str)
    else:
        print(debug_str)
    
    return debug_str


def analyze_document_structure(
    pdf_path: Union[str, Path], 
    pages_text_dict: Dict[int, str]
) -> DocumentStructure:
    """
    Analyzes a PDF document's structure including tables, zones, and document type.
    
    Args:
        pdf_path: Path to the PDF file
        pages_text_dict: Dictionary mapping page numbers to extracted text
        
    Returns:
        DocumentStructure object containing analysis results
    """
    logging.info(f"Analyzing document structure for {pdf_path}")
    
    # Initialize with default empty structure
    structure: DocumentStructure = {
        "document_type": None,
        "page_zones": {},
        "tables": {},
        "biomarker_regions": [],
        "confidence": 0.0
    }
    
    if pdfplumber is None:
        logging.warning("PDFPlumber not available, returning empty document structure")
        return structure
    
    try:
        # 1. Identify document type
        doc_type, doc_type_confidence = detect_document_type(pages_text_dict)
        structure["document_type"] = doc_type
        
        # 2. Extract detailed page structure using pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            overall_confidence = doc_type_confidence
            tables_total = 0
            
            for page_num, page in enumerate(pdf.pages):
                logging.info(f"Analyzing structure of page {page_num}")
                
                # 2a. Detect tables
                tables = detect_tables(page, page_num)
                if tables:
                    structure["tables"][page_num] = tables
                    tables_total += len(tables)
                
                # 2b. Detect zones
                zones = detect_document_zones(page, page_num)
                if zones:
                    structure["page_zones"][page_num] = zones
                
                # Add to overall confidence calculation
                page_confidence = 0.5  # Base page confidence
                if tables:
                    page_confidence += 0.2  # Bonus for finding tables
                if "content" in zones and zones["content"]["confidence"] > 0.7:
                    page_confidence += 0.1  # Bonus for confident content zone
                
                overall_confidence += page_confidence
            
            # Average confidence across all pages and doc type
            total_pages = len(pdf.pages)
            if total_pages > 0:
                overall_confidence = (overall_confidence + doc_type_confidence) / (total_pages + 1)
                
                # Bonus for finding multiple tables (likely a lab report)
                if tables_total > 0:
                    table_bonus = min(0.2, tables_total * 0.05)
                    overall_confidence += table_bonus
                
                # Cap confidence at 0.95
                overall_confidence = min(0.95, overall_confidence)
            
            # 3. Detect biomarker regions
            biomarker_regions = detect_biomarker_regions(pdf_path, pages_text_dict, structure["tables"])
            structure["biomarker_regions"] = biomarker_regions
            
            structure["confidence"] = overall_confidence
            logging.info(f"Document structure analysis complete with confidence {overall_confidence:.2f}")
            logging.info(f"Found {tables_total} tables across {total_pages} pages")
            logging.info(f"Detected {len(biomarker_regions)} potential biomarker regions")
        
        # Add debug output at the end
        if os.environ.get("DEBUG_DOCUMENT_STRUCTURE", "0") == "1":
            debug_file = f"debug_structure_{os.path.basename(pdf_path)}.txt"
            debug_document_structure(structure, output_file=debug_file)
        
        return structure
        
    except Exception as e:
        logging.error(f"Error analyzing document structure: {e}", exc_info=True)
        return structure


def optimize_content_for_extraction(
    pages_text_dict: Dict[int, str], 
    document_structure: DocumentStructure,
    accuracy_mode: bool = None,
    balanced_mode: bool = None
) -> List[ContentChunk]:
    """
    Creates optimized content chunks for extraction based on document structure.
    
    Args:
        pages_text_dict: Dictionary mapping page numbers to extracted text
        document_structure: Structure information about the document
        accuracy_mode: If True, prioritize accuracy over token efficiency. 
                      If None, checks ACCURACY_MODE environment variable
        balanced_mode: If True, balance accuracy with token efficiency.
                      If None, checks BALANCED_MODE environment variable
        
    Returns:
        List of ContentChunk objects for optimized extraction
    """
    logging.info("Optimizing content for extraction")
    
    # Determine optimization mode
    if balanced_mode is None:
        # Check environment variable for balanced mode
        balanced_mode = os.environ.get("BALANCED_MODE", "false").lower() == "true"
    
    if accuracy_mode is None:
        # Check environment variable for accuracy mode
        accuracy_mode = os.environ.get("ACCURACY_MODE", "false").lower() == "true"
    
    # Priority: balanced_mode > accuracy_mode > legacy
    if balanced_mode:
        logging.info("⚖️  BALANCED MODE ENABLED: Optimizing for cost-effective accuracy balance")
        
        # Use balanced optimization
        chunks = optimize_content_chunks(
            pages_text_dict,
            document_structure,
            max_tokens_per_chunk=4000,  # Larger chunks for efficiency
            accuracy_mode=False,
            balanced_mode=True
        )
        
        # Use balanced enhancement
        chunks = enhance_chunk_confidence_balanced(chunks)
        
    elif accuracy_mode:
        logging.info("🎯 ACCURACY MODE ENABLED: Prioritizing biomarker detection accuracy over token efficiency")
        
        # Use accuracy-first optimization
        chunks = optimize_content_chunks(
            pages_text_dict,
            document_structure,
            max_tokens_per_chunk=2500,  # Smaller chunks for better accuracy
            accuracy_mode=True,
            balanced_mode=False
        )
        
        # Use accuracy-focused enhancement
        chunks = enhance_chunk_confidence_for_accuracy(chunks)
    else:
        logging.info("📉 TOKEN EFFICIENCY MODE: Optimizing for cost reduction")
        
        # Use standard optimization (legacy mode)
        chunks = optimize_content_chunks(
            pages_text_dict,
            document_structure,
            max_tokens_per_chunk=8000,
            accuracy_mode=False,
            balanced_mode=False
        )
        
        # Use standard enhancement
        chunks = enhance_chunk_confidence(chunks)
    
    # Convert to ContentChunk type and return
    content_chunks: List[ContentChunk] = []
    for chunk in chunks:
        content_chunk: ContentChunk = {
            "text": chunk["text"],
            "page_num": chunk["page_num"],
            "region_type": chunk["region_type"],
            "estimated_tokens": chunk["estimated_tokens"],
            "biomarker_confidence": chunk["biomarker_confidence"],
            "context": chunk["context"],
        }
        content_chunks.append(content_chunk)
    
    mode_description = "BALANCED" if balanced_mode else ("ACCURACY-FIRST" if accuracy_mode else "TOKEN-EFFICIENT")
    logging.info(f"Created {len(content_chunks)} {mode_description} chunks for extraction")
    return content_chunks


def create_adaptive_prompt(
    chunk: ContentChunk, 
    extraction_context: ExtractionContext,
    document_structure: Optional[DocumentStructure] = None
) -> str:
    """
    Creates an adaptive prompt for extraction based on content and context using the smart prompting engine.
    
    Args:
        chunk: The content chunk to extract from
        extraction_context: Current extraction context
        document_structure: Document structure information for optimization
        
    Returns:
        Optimized prompt string for Claude API
    """
    # Determine optimization level based on context
    optimization_level = 1  # Default to low optimization
    
    # Increase optimization level based on call count and token usage
    call_count = extraction_context.get("call_count", 0)
    if call_count >= 3:
        optimization_level = 2  # Medium optimization after several calls
    if call_count >= 7:
        optimization_level = 3  # High optimization for many calls
    
    # Adjust based on token efficiency
    token_usage = extraction_context.get("token_usage", {})
    if token_usage:
        total_tokens = token_usage.get("input", 0) + token_usage.get("output", 0)
        biomarker_count = len(extraction_context.get("known_biomarkers", {}))
        
        if biomarker_count > 0:
            tokens_per_biomarker = total_tokens / biomarker_count
            if tokens_per_biomarker > 400:  # High token usage per biomarker
                optimization_level = min(3, optimization_level + 1)
    
    # Get document type from structure
    document_type = None
    if document_structure:
        document_type = document_structure.get("document_type")
    
    # Use smart prompting engine to create adaptive prompt
    prompt = smart_prompt_engine.create_adaptive_prompt(
        chunk_text=chunk["text"],
        page_num=chunk["page_num"],
        extraction_context=extraction_context,
        document_type=document_type,
        optimization_level=optimization_level
    )
    
    return prompt


def update_extraction_context(
    extraction_context: ExtractionContext,
    chunk: ContentChunk,
    results: List[Dict[str, Any]]
) -> ExtractionContext:
    """
    Updates extraction context based on the latest extraction results using smart pattern tracking.
    
    Args:
        extraction_context: Current extraction context
        chunk: The content chunk that was processed
        results: Extraction results from the API call
        
    Returns:
        Updated extraction context with enhanced pattern information
    """
    # Use utility function for basic updates
    updated_context = utils_update_extraction_context(
        extraction_context=extraction_context,
        biomarkers=results,
        page_num=chunk["page_num"],
        input_tokens=chunk["estimated_tokens"],
        output_tokens=estimate_tokens(str(results))
    )
    
    # Enhance with smart pattern tracking
    success = len(results) > 0 and any(
        result.get("confidence", 0) >= 0.7 for result in results
    )
    
    # Update patterns using smart prompting engine
    updated_context = smart_prompt_engine.update_patterns_from_results(
        extraction_context=updated_context,
        biomarkers=results,
        chunk_text=chunk["text"],
        success=success
    )
    
    # Add chunk-specific context enhancements
    section_context = updated_context.get("section_context", {})
    
    # Track chunk processing metrics
    chunks_processed = section_context.get("chunks_processed", 0) + 1
    section_context["chunks_processed"] = chunks_processed
    
    # Update biomarker discovery metrics
    current_biomarker_count = len(results)
    section_context["last_chunk_biomarkers"] = current_biomarker_count
    section_context["last_chunk_confidence"] = chunk.get("biomarker_confidence", 0.0)
    section_context["last_chunk_type"] = chunk.get("region_type", "text")
    
    # Calculate average biomarkers per chunk
    total_biomarkers = len(updated_context.get("known_biomarkers", {}))
    if chunks_processed > 0:
        section_context["avg_biomarkers_per_chunk"] = total_biomarkers / chunks_processed
    
    # Track discovery rate (for early termination logic)
    if chunks_processed >= 2:
        recent_chunks = min(3, chunks_processed)
        if "recent_discovery_rate" not in section_context:
            section_context["recent_discovery_rate"] = []
        
        section_context["recent_discovery_rate"].append(current_biomarker_count)
        if len(section_context["recent_discovery_rate"]) > recent_chunks:
            section_context["recent_discovery_rate"] = section_context["recent_discovery_rate"][-recent_chunks:]
        
        # Calculate recent discovery trend
        recent_discoveries = section_context["recent_discovery_rate"]
        if len(recent_discoveries) >= 2:
            trend = sum(recent_discoveries[-2:]) / 2
            section_context["recent_discovery_trend"] = trend
    
    updated_context["section_context"] = section_context
    
    # Add new biomarkers to known_biomarkers with enhanced metadata
    for result in results:
        if "name" in result and result["name"]:
            biomarker_key = result["name"].lower()
            biomarker_data = {
                "name": result["name"],
                "value": result.get("value", ""),
                "unit": result.get("unit", ""),
                "reference_range": result.get("reference_range", ""),
                "page": chunk["page_num"],
                "confidence": result.get("confidence", 0.0),
                "extraction_method": "smart_prompting",
                "chunk_type": chunk.get("region_type", "text"),
                "discovery_order": len(updated_context["known_biomarkers"]) + 1
            }
            updated_context["known_biomarkers"][biomarker_key] = biomarker_data
    
    return updated_context


def create_default_extraction_context() -> ExtractionContext:
    """
    Creates a default extraction context for a new document.
    
    Returns:
        Default ExtractionContext object
    """
    return utils_create_default_extraction_context() 