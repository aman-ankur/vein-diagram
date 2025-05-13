"""
Structure Detection Utilities

This module provides utilities for analyzing document structure, 
detecting tables, classifying zones, and identifying document types.
"""
from typing import Dict, List, Optional, Any, Tuple
import logging
import re

# Try to import dependencies, with graceful fallback
try:
    import pdfplumber
except ImportError:
    logging.warning("pdfplumber not installed. Document structure analysis will be limited.")
    pdfplumber = None


def detect_tables(pdf_page, page_number: int) -> List[Dict]:
    """
    Detect tables in a PDF page using pdfplumber.
    
    Args:
        pdf_page: A pdfplumber page object
        page_number: The page number (0-indexed)
        
    Returns:
        List of table information dictionaries
    """
    tables = []
    try:
        # Find tables with default settings
        detected_tables = pdf_page.find_tables()
        
        # If no tables found with default settings, try with more lenient settings
        if not detected_tables:
            detected_tables = pdf_page.find_tables({
                'vertical_strategy': 'text',
                'horizontal_strategy': 'text',
                'intersection_tolerance': 10,
                'join_tolerance': 5,
                'edge_min_length': 3,
                'min_cells': 4
            })
        
        # Convert to our information format
        for idx, table in enumerate(detected_tables):
            # Get table dimensions
            if hasattr(table, "cells") and table.cells:
                rows = max([cell[0] for cell in table.cells.keys()]) + 1 if table.cells else 0
                cols = max([cell[1] for cell in table.cells.keys()]) + 1 if table.cells else 0
            else:
                # Fallback if cells not available
                rows = len(table.rows) if hasattr(table, "rows") else 0
                cols = len(table.cols) if hasattr(table, "cols") else 0
            
            # Calculate confidence based on table structure
            # More rows/columns and more uniform cell sizes = higher confidence
            confidence = min(0.95, 0.5 + (rows * cols) / 100)
            
            # Extract table content if possible
            table_text = ""
            try:
                table_text = table.extract()
            except Exception as e:
                logging.warning(f"Could not extract table text: {e}")
            
            # Create table info dictionary
            table_info = {
                "bbox": [table.bbox[0], table.bbox[1], table.bbox[2], table.bbox[3]],
                "page_number": page_number,
                "rows": rows,
                "cols": cols,
                "confidence": confidence,
                "index": idx,
                "text": table_text
            }
            tables.append(table_info)
        
        logging.info(f"Detected {len(tables)} tables on page {page_number}")
    except Exception as e:
        logging.error(f"Error detecting tables on page {page_number}: {e}")
    
    return tables


def detect_document_zones(pdf_page, page_number: int) -> Dict[str, Dict]:
    """
    Detect and classify zones (header, footer, content) in a PDF page.
    
    Args:
        pdf_page: A pdfplumber page object
        page_number: The page number (0-indexed)
        
    Returns:
        Dictionary mapping zone types to zone information
    """
    zones = {}
    try:
        # Get page dimensions
        page_width = pdf_page.width
        page_height = pdf_page.height
        
        # Define standard zones (based on typical layouts)
        # Header: top 10-15% of the page
        header_height = page_height * 0.15
        header_zone = {
            "zone_type": "header",
            "bbox": [0, 0, page_width, header_height],
            "confidence": 0.8  # Default confidence
        }
        
        # Footer: bottom 10% of the page
        footer_top = page_height * 0.9
        footer_zone = {
            "zone_type": "footer",
            "bbox": [0, footer_top, page_width, page_height],
            "confidence": 0.8  # Default confidence
        }
        
        # Content: middle section
        content_zone = {
            "zone_type": "content",
            "bbox": [0, header_height, page_width, footer_top],
            "confidence": 0.9  # Default confidence
        }
        
        # Refine zones based on text distribution
        words = pdf_page.extract_words()
        if words:
            # Analyze the vertical distribution of text
            y_positions = [word["bottom"] for word in words]
            y_positions.sort()
            
            # Find gaps in vertical text distribution
            if len(y_positions) > 10:  # Need enough text to analyze
                gaps = []
                for i in range(1, len(y_positions)):
                    gap = y_positions[i] - y_positions[i-1]
                    if gap > 20:  # Significant gap threshold
                        gaps.append((y_positions[i-1], y_positions[i], gap))
                
                # Sort gaps by size (largest first)
                gaps.sort(key=lambda x: x[2], reverse=True)
                
                # Use largest gaps to refine zone boundaries if significant
                if gaps and gaps[0][2] > 30:  # Very significant gap
                    # If the gap is in the top portion, it might separate header
                    if gaps[0][0] < page_height * 0.3:
                        header_zone["bbox"][3] = gaps[0][0] + 5  # +5 for padding
                        content_zone["bbox"][1] = gaps[0][1] - 5
                        header_zone["confidence"] = 0.9  # Increased confidence
                
                # Check for footer gap
                footer_gaps = [g for g in gaps if g[0] > page_height * 0.7]
                if footer_gaps:
                    footer_zone["bbox"][1] = footer_gaps[0][1] - 5
                    content_zone["bbox"][3] = footer_gaps[0][0] + 5
                    footer_zone["confidence"] = 0.9  # Increased confidence
        
        # Add all zones
        zones["header"] = header_zone
        zones["content"] = content_zone
        zones["footer"] = footer_zone
        
        # Extract text for each zone
        for zone_name, zone_info in zones.items():
            bbox = zone_info["bbox"]
            try:
                # Extract text within the zone's bbox
                crop = pdf_page.crop(bbox)
                zone_text = crop.extract_text() if crop else ""
                zone_info["text"] = zone_text
            except Exception as e:
                logging.warning(f"Error extracting text for {zone_name} zone: {e}")
                zone_info["text"] = ""
        
        logging.info(f"Detected zones on page {page_number}: header, content, footer")
    except Exception as e:
        logging.error(f"Error detecting zones on page {page_number}: {e}")
        # Fallback to basic zones
        zones = {
            "content": {
                "zone_type": "content",
                "bbox": [0, 0, pdf_page.width, pdf_page.height],
                "confidence": 0.5,
                "text": ""
            }
        }
    
    return zones


def detect_document_type(pages_text_dict: Dict[int, str]) -> Tuple[str, float]:
    """
    Detect the lab report type based on text patterns.
    
    Args:
        pages_text_dict: Dictionary mapping page numbers to extracted text
        
    Returns:
        Tuple of (document_type, confidence)
    """
    # Common lab report identifiers
    lab_identifiers = {
        "quest_diagnostics": [
            r"quest\s*diagnostics", 
            r"questdiagnostics\.com",
            r"quest\s*diagnostics\s*incorporated"
        ],
        "labcorp": [
            r"lab(?:oratory\s*)?corp(?:oration)?", 
            r"labcorp\.com"
        ],
        "mayo_clinic": [
            r"mayo\s*clinic", 
            r"mayo\s*medical\s*laboratories"
        ],
        "cleveland_clinic": [
            r"cleveland\s*clinic",
            r"clevelandclinic\.org"
        ],
        "arup": [
            r"arup\s*laboratories",
            r"aruplab(?:s)?\.com"
        ]
    }
    
    # Count matches for each lab type
    lab_matches = {lab: 0 for lab in lab_identifiers}
    doc_text = "\n".join(pages_text_dict.values())
    
    for lab, patterns in lab_identifiers.items():
        for pattern in patterns:
            if re.search(pattern, doc_text, re.IGNORECASE):
                lab_matches[lab] += 1
    
    # Find the lab with most matches
    max_matches = max(lab_matches.values()) if lab_matches else 0
    if max_matches > 0:
        doc_type = max(lab_matches, key=lab_matches.get)
        # Calculate confidence (more matches = higher confidence)
        confidence = min(0.95, 0.6 + (max_matches * 0.1))
        logging.info(f"Detected document type: {doc_type} with confidence {confidence:.2f}")
        return doc_type, confidence
    
    return None, 0.0


def detect_biomarker_regions(
    pdf_path: str, 
    pages_text_dict: Dict[int, str], 
    tables: Dict[int, List[Dict]]
) -> List[Dict]:
    """
    Identify regions in the document likely to contain biomarkers.
    
    Args:
        pdf_path: Path to the PDF file
        pages_text_dict: Dictionary mapping page numbers to extracted text
        tables: Dictionary mapping page numbers to list of tables
        
    Returns:
        List of biomarker region dictionaries
    """
    # Biomarker patterns
    biomarker_patterns = [
        r"\b\w+\s*:\s*\d+[\.,]?\d*\s*[a-zA-Z/%]+",  # Pattern: Name: Value Unit
        r"\b\w+\s+\d+[\.,]?\d*\s*[a-zA-Z/%]+",      # Pattern: Name Value Unit
        r"\b\w+\s+\d+[\.,]?\d*\s*\(\s*\d+[\.,]?\d*\s*-\s*\d+[\.,]?\d*\s*\)" # Name Value (Range)
    ]
    
    biomarker_regions = []
    
    # Tables are high-confidence biomarker regions
    for page_num, page_tables in tables.items():
        for table in page_tables:
            biomarker_region = {
                "type": "table",
                "page_num": page_num,
                "bbox": table["bbox"],
                "confidence": table["confidence"],
                "index": table["index"]
            }
            biomarker_regions.append(biomarker_region)
    
    # Analyze text outside tables
    if pdfplumber:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page_text in pages_text_dict.items():
                    if page_num >= len(pdf.pages):
                        continue
                    
                    page = pdf.pages[page_num]
                    # Get table bboxes for this page
                    table_bboxes = [table["bbox"] for table in tables.get(page_num, [])]
                    
                    # Split text into paragraphs
                    paragraphs = page_text.split('\n\n')
                    for para_idx, paragraph in enumerate(paragraphs):
                        # Skip very short paragraphs
                        if len(paragraph) < 20:
                            continue
                        
                        # Check if paragraph contains biomarker patterns
                        biomarker_matches = 0
                        for pattern in biomarker_patterns:
                            matches = re.findall(pattern, paragraph)
                            biomarker_matches += len(matches)
                        
                        # If biomarkers found, add as a region
                        if biomarker_matches > 0:
                            # Calculate confidence based on number of matches
                            confidence = min(0.9, 0.5 + (biomarker_matches * 0.1))
                            
                            biomarker_region = {
                                "type": "text",
                                "page_num": page_num,
                                "text": paragraph,
                                "confidence": confidence,
                                "index": para_idx,
                                "matches": biomarker_matches
                            }
                            biomarker_regions.append(biomarker_region)
        except Exception as e:
            logging.error(f"Error detecting biomarker regions: {e}")
    
    return biomarker_regions 