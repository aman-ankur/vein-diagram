"""
Document Analyzer Module

This module provides functionality for analyzing PDF document structure,
optimizing content for extraction, and managing extraction context.
"""
from typing import Dict, List, Optional, Any, TypedDict, Union, Tuple
import logging
import re
from pathlib import Path

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
    enhance_chunk_confidence
)
from app.services.utils.context_management import (
    create_adaptive_prompt as utils_create_adaptive_prompt,
    update_extraction_context as utils_update_extraction_context,
    create_default_extraction_context as utils_create_default_extraction_context,
    filter_biomarkers_by_confidence
)

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
        
        return structure
        
    except Exception as e:
        logging.error(f"Error analyzing document structure: {e}", exc_info=True)
        return structure


def optimize_content_for_extraction(
    pages_text_dict: Dict[int, str], 
    document_structure: DocumentStructure
) -> List[ContentChunk]:
    """
    Creates optimized content chunks for extraction based on document structure.
    
    Args:
        pages_text_dict: Dictionary mapping page numbers to extracted text
        document_structure: Structure information about the document
        
    Returns:
        List of ContentChunk objects for optimized extraction
    """
    logging.info("Optimizing content for extraction")
    
    # Use utility to create optimized chunks
    chunks = optimize_content_chunks(
        pages_text_dict,
        document_structure,
        max_tokens_per_chunk=8000
    )
    
    # Enhance confidence scores based on biomarker patterns
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
    
    logging.info(f"Created {len(content_chunks)} optimized chunks for extraction")
    return content_chunks


def create_adaptive_prompt(
    chunk: ContentChunk, 
    extraction_context: ExtractionContext
) -> str:
    """
    Creates an adaptive prompt for extraction based on content and context.
    
    Args:
        chunk: The content chunk to extract from
        extraction_context: Current extraction context
        
    Returns:
        Optimized prompt string for Claude API
    """
    # Use utility function for adaptive prompt creation
    prompt = utils_create_adaptive_prompt(
        chunk_text=chunk["text"],
        page_num=chunk["page_num"],
        extraction_context=extraction_context
    )
    
    # Create different prompts based on call count
    if extraction_context["call_count"] == 0:
        # First call - use a more verbose, detailed prompt
        prompt = (
            f"Extract biomarkers from the following text from page {chunk['page_num']}:\n\n"
            f"{chunk['text']}\n\n"
            f"Look for lab results, measurements, and biomarker values with their units and reference ranges."
        )
    else:
        # Subsequent calls - more focused prompt using context from previous extractions
        known_biomarkers = ', '.join(extraction_context["known_biomarkers"].keys()) if extraction_context["known_biomarkers"] else "none yet"
        prompt = (
            f"Extract biomarkers from the following text from page {chunk['page_num']}:\n\n"
            f"{chunk['text']}"
        )
    
    return prompt


def update_extraction_context(
    extraction_context: ExtractionContext,
    chunk: ContentChunk,
    results: List[Dict[str, Any]]
) -> ExtractionContext:
    """
    Updates extraction context based on the latest extraction results.
    
    Args:
        extraction_context: Current extraction context
        chunk: The content chunk that was processed
        results: Extraction results from the API call
        
    Returns:
        Updated extraction context
    """
    # Use utility function but adapt parameters
    updated_context = utils_update_extraction_context(
        extraction_context=extraction_context,
        biomarkers=results,
        page_num=chunk["page_num"],
        input_tokens=chunk["estimated_tokens"],
        output_tokens=estimate_tokens(str(results))
    )
    
    # Add new biomarkers to known_biomarkers
    for result in results:
        if "name" in result and result["name"]:
            biomarker_key = result["name"].lower()
            updated_context["known_biomarkers"][biomarker_key] = {
                "name": result["name"],
                "value": result.get("value", ""),
                "unit": result.get("unit", ""),
                "reference_range": result.get("reference_range", ""),
                "page": chunk["page_num"]
            }
    
    return updated_context


def create_default_extraction_context() -> ExtractionContext:
    """
    Creates a default extraction context for a new document.
    
    Returns:
        Default ExtractionContext object
    """
    return utils_create_default_extraction_context() 