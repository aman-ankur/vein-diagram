import os
from typing import List, Dict, Any, Optional, Tuple
import PyPDF2
from PIL import Image
import pytesseract
import logging
import tempfile
import pdf2image
import io
import json
from datetime import datetime
from sqlalchemy.orm import Session
import pdfplumber
import pandas as pd
import re
import dateutil.parser
import asyncio
import time

from app.services.biomarker_parser import (
    extract_biomarkers_with_claude,
    parse_biomarkers_from_text,
    standardize_unit,
    _preprocess_text_for_claude
)
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF  # Import the PDF model class
from app.db.database import SessionLocal  # Import SessionLocal for error handling
from app.services.health_summary_service import generate_and_update_health_summary # Import the new service function
from app.services.document_analyzer import (
    analyze_document_structure,
    optimize_content_for_extraction,
    create_adaptive_prompt,
    update_extraction_context,
    create_default_extraction_context,
    DocumentStructure
)
from app.core.config import DOCUMENT_ANALYZER_CONFIG
from app.services.utils.metrics import TokenUsageMetrics
from app.services.utils.content_optimization import (
    apply_smart_chunk_skipping,
    quick_biomarker_screening
)
from app.services.utils.biomarker_cache import (
    get_biomarker_cache,
    extract_cached_biomarkers
)

# Get logger for this module
logger = logging.getLogger(__name__)

# --- Helper Functions for Page Filtering (Phase 2) ---

def _load_biomarker_aliases() -> List[str]:
    """Loads biomarker names and aliases from the JSON file."""
    aliases = []
    try:
        # Construct the path relative to the current file's directory
        current_dir = os.path.dirname(__file__)
        aliases_path = os.path.join(current_dir, '..', 'utils', 'biomarker_aliases.json')
        
        with open(aliases_path, 'r') as f:
            data = json.load(f)
            for biomarker_info in data.get("biomarkers", []):
                # Add the main name
                if name := biomarker_info.get("name"):
                    aliases.append(name.lower())
                # Add all aliases
                for alias in biomarker_info.get("aliases", []):
                    aliases.append(alias.lower())
        logger.info(f"Loaded {len(aliases)} biomarker names and aliases.")
    except FileNotFoundError:
        logger.error(f"Biomarker aliases file not found at {aliases_path}")
    except json.JSONDecodeError:
        logger.error(f"Error decoding JSON from biomarker aliases file at {aliases_path}")
    except Exception as e:
        logger.error(f"Error loading biomarker aliases: {str(e)}")
    return list(set(aliases)) # Return unique list

def score_page_relevance(page_text: str, all_aliases: List[str]) -> int:
    """Scores a page based on the presence of biomarker keywords, units, and table patterns."""
    score = 0
    if not page_text:
        return 0

    # 1. Check for biomarker names/aliases (case-insensitive)
    # Create a regex pattern for aliases (ensure proper escaping)
    # Limit alias length to avoid overly broad matches
    valid_aliases = [re.escape(alias) for alias in all_aliases if 2 < len(alias) < 50]
    if valid_aliases:
        alias_pattern = r'\b(' + '|'.join(valid_aliases) + r')\b'
        try:
            # Use finditer to count occurrences efficiently
            matches = list(re.finditer(alias_pattern, page_text, re.IGNORECASE))
            if matches:
                score += 10 * len(matches) # Score per alias found
                logger.debug(f"Found {len(matches)} alias matches on page.")
        except re.error as re_err:
             logger.error(f"Regex error checking aliases: {re_err}")


    # 2. Check for common units associated with numeric values
    # Pattern: number (optional decimal) followed by common units
    unit_pattern = r'\b\d+(\.\d+)?\s*(mg/dL|g/dL|%|mmol/L|U/L|IU/L|ng/mL|pg/mL|mIU/L|μIU/mL|μg/dL|ug/dL|mEq/L|meq/L|K/μL|K/uL|M/μL|M/uL|fL|pg|mm/hr)\b'
    try:
        unit_matches = list(re.finditer(unit_pattern, page_text, re.IGNORECASE))
        if unit_matches:
            score += 1 * len(unit_matches) # Lower score for units
            logger.debug(f"Found {len(unit_matches)} unit matches on page.")
    except re.error as re_err:
        logger.error(f"Regex error checking units: {re_err}")

    # 3. Check for potential table structures (heuristic)
    # Look for multiple lines with similar indentation and potential delimiters (spaces, tabs)
    lines = page_text.strip().split('\n')
    table_like_lines = 0
    if len(lines) > 3: # Need at least a few lines to suggest a table
        potential_table_pattern = r'^\s*[\w\s\(\)\-\+,/]+(\s{2,}|\t)[\d\.<>\-\s]+' # Line starts with text, then space/tab, then numbers/symbols
        for line in lines:
            if re.search(potential_table_pattern, line):
                table_like_lines += 1
        if table_like_lines > 2: # If more than 2 lines look like table rows
            score += 5
            logger.debug(f"Found {table_like_lines} table-like lines.")

    logger.debug(f"Page scored with relevance: {score}")
    return score

def filter_relevant_pages(
    pages_text_dict,
    document_structure=None
) -> Dict[int, str]:
    """Filter pages with relevant content for biomarker extraction, now with structure awareness."""
    relevant_pages = []
    # Initialize filtered_pages here to prevent reference before assignment
    filtered_pages = {}
    
    all_aliases = _load_biomarker_aliases()
    if not all_aliases:
        logger.warning("No aliases loaded, cannot perform relevance scoring. Returning all pages.")
        # Fallback: return all pages if aliases couldn't be loaded
        return sorted(pages_text_dict.items())

    min_relevance_score = 1 # Minimum score to be considered relevant (at least one unit match or part of a table)

    for page_num, page_text in pages_text_dict.items():
        score = score_page_relevance(page_text, all_aliases)
        if score >= min_relevance_score:
            relevant_pages.append((page_num, page_text))
            logger.info(f"Page {page_num} deemed relevant with score {score}.")
        else:
             logger.info(f"Page {page_num} deemed irrelevant with score {score}.")

    # Sort by page number
    relevant_pages.sort(key=lambda x: x[0])
    logger.info(f"Filtered down to {len(relevant_pages)} relevant pages out of {len(pages_text_dict)} total.")

    # Enhanced version with structure awareness
    if document_structure is not None:
        logging.info("Using document structure to filter relevant pages")
        filtered_pages = {}
        
        for page_num, text in pages_text_dict.items():
            # Higher relevance if page has tables (likely to contain biomarkers)
            has_tables = page_num in document_structure.get("tables", {}) and document_structure["tables"][page_num]
            
            if has_tables:
                logging.info(f"Page {page_num} contains tables, including for biomarker extraction")
                filtered_pages[page_num] = text
                continue
            
            # Check if this is a content page (not just header/footer)
            page_zones = document_structure.get("page_zones", {}).get(page_num, {})
            content_zone = page_zones.get("content", {})
            
            # If we have a content zone with high confidence
            if content_zone and content_zone.get("confidence", 0) > 0.7:
                # Use the existing biomarker pattern matching logic
                if contain_biomarker_patterns(text):
                    logging.info(f"Page {page_num} contains biomarker patterns in content zone")
                    filtered_pages[page_num] = text
            else:
                # Fallback to original pattern matching
                if contain_biomarker_patterns(text):
                    logging.info(f"Page {page_num} contains biomarker patterns (fallback method)")
                    filtered_pages[page_num] = text
        
        if filtered_pages:
            return filtered_pages
        
        # If we filtered out all pages, fall back to original method
        logging.warning("Structure-based filtering removed all pages, falling back to original method")
    
    # Fall back to original method if structure not available or no pages found
    # Convert relevant_pages list to dictionary for consistent return type
    if not filtered_pages:
        filtered_pages = {page_num: text for page_num, text in relevant_pages}
    
    return filtered_pages

async def process_pages_sequentially(
    relevant_pages,
    document_structure=None
) -> List[Dict]:
    """
    Process content to extract biomarkers, optimizing for token efficiency.
    
    Args:
        relevant_pages: Dictionary of page number -> text or List of (page_num, text) tuples
        document_structure: Optional document structure information
        
    Returns:
        List of extracted biomarkers
    """
    from app.services.utils.metrics import TokenUsageMetrics
    from app.services.document_analyzer import (
        optimize_content_for_extraction, 
        create_adaptive_prompt,
        create_default_extraction_context,
        update_extraction_context
    )
    import time
    import os
    
    # Create metrics tracker
    debug_metrics = os.environ.get("DEBUG_TOKEN_METRICS", "0") == "1"
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    metrics = TokenUsageMetrics(save_debug=debug_metrics, debug_dir=logs_dir)
    
    # Prepare all_biomarkers list and extraction context
    all_biomarkers = []
    extraction_context = create_default_extraction_context()
    
    # Ensure relevant_pages is a dictionary
    if isinstance(relevant_pages, list):
        relevant_pages = {page_num: text for page_num, text in relevant_pages}
    
    # Record original token metrics
    for page_num, page_text in relevant_pages.items():
        metrics.record_original_text(page_text, page_num)
    
    # Enable enhanced processing with validation
    if (document_structure is not None and 
        DOCUMENT_ANALYZER_CONFIG["enabled"] and 
        DOCUMENT_ANALYZER_CONFIG["content_optimization"]["enabled"]):
        
        logger.info("Using enhanced content optimization for biomarker extraction")
        
        # Start timing optimization
        optimization_start = time.time()
        
        # Optimize content into chunks based on structure
        content_chunks = optimize_content_for_extraction(relevant_pages, document_structure)
        
        # Record optimization time
        optimization_time = time.time() - optimization_start
        metrics.record_optimization_complete(optimization_time, len(content_chunks))
        
        # Validation: Check if optimization actually helped
        original_total_tokens = sum(metrics.record_original_text(text, page_num) for page_num, text in relevant_pages.items())
        optimized_total_tokens = sum(chunk["estimated_tokens"] for chunk in content_chunks)
        
        if optimized_total_tokens >= original_total_tokens:
            logger.warning(f"Content optimization failed to reduce tokens ({original_total_tokens} -> {optimized_total_tokens}), falling back to original processing")
            # Fall back to original processing
            logger.info(f"Using original sequential processing for {len(relevant_pages)} relevant pages")
            
            for page_num, page_text in relevant_pages.items():
                logger.info(f"Processing page {page_num} sequentially")
                try:
                    page_biomarkers, _ = await extract_biomarkers_with_claude(page_text)
                    
                    if page_biomarkers:
                        logger.info(f"Extracted {len(page_biomarkers)} biomarkers from page {page_num}")
                        for bm in page_biomarkers:
                            bm['page'] = page_num
                        all_biomarkers.extend(page_biomarkers)
                    else:
                        logger.info(f"No biomarkers found on page {page_num}")
                except Exception as e:
                    logger.error(f"Error processing page {page_num} sequentially: {str(e)}")
            
            all_biomarkers = _deduplicate_biomarkers(all_biomarkers)
            return all_biomarkers
        
        logger.info(f"Created {len(content_chunks)} optimized chunks for processing (token reduction: {((original_total_tokens - optimized_total_tokens) / original_total_tokens * 100):.1f}%)")
        
        # PHASE 1: Apply Smart Chunk Skipping
        if DOCUMENT_ANALYZER_CONFIG.get("smart_chunk_skipping", {}).get("enabled", False):
            logger.info("🔍 Applying smart chunk skipping to optimize processing")
            
            # Apply smart chunk skipping with current biomarker count
            filtered_chunks, skipping_stats = apply_smart_chunk_skipping(
                chunks=content_chunks,
                existing_biomarkers_count=len(all_biomarkers),
                enabled=True
            )
            
            # Safety check: ensure we don't skip too many chunks
            max_skip_percentage = DOCUMENT_ANALYZER_CONFIG["smart_chunk_skipping"].get("max_skipped_chunks", 0.5)
            skip_percentage = skipping_stats["skipped"] / skipping_stats["total_chunks"] if skipping_stats["total_chunks"] > 0 else 0
            
            if skip_percentage > max_skip_percentage:
                logger.warning(f"⚠️  Smart skipping would skip {skip_percentage:.1%} of chunks (>{max_skip_percentage:.1%} limit)")
                logger.info("🔄 Applying conservative skipping to stay within safety limits")
                
                # Apply more conservative skipping (only skip very obvious non-biomarker content)
                conservative_chunks = []
                tokens_saved = 0
                for chunk in content_chunks:
                    screening = quick_biomarker_screening(chunk["text"], len(all_biomarkers))
                    if screening["confidence"] >= 0.5 or screening["fast_patterns_found"] >= 2:
                        conservative_chunks.append(chunk)
                    else:
                        tokens_saved += chunk.get("estimated_tokens", 0)
                        logger.debug(f"⏭️  Conservative skip: {screening['reason']}")
                
                filtered_chunks = conservative_chunks
                logger.info(f"🛡️  Conservative skipping: {len(content_chunks) - len(filtered_chunks)} chunks skipped, {tokens_saved} tokens saved")
            else:
                logger.info(f"✅ Smart skipping applied successfully: {skipping_stats['skipped']} chunks skipped, {skipping_stats['token_savings']} tokens saved")
            
            # Record skipping metrics
            metrics.record_smart_skipping_stats(skipping_stats)
            logger.info(f"📊 Smart chunk skipping results: {skipping_stats}")
            logger.info(f"🔍 Processing {len(filtered_chunks)} filtered chunks (skipped {skipping_stats['skipped']})")
            content_chunks = filtered_chunks
        
        # PHASE 2: Apply Biomarker Caching for Fast Extraction
        cache_config = DOCUMENT_ANALYZER_CONFIG.get("biomarker_caching", {})
        biomarker_cache = None
        cached_biomarkers = []
        remaining_chunks = content_chunks.copy()
        
        if cache_config.get("enabled", False):
            logger.info("🧠 Applying biomarker caching for fast extraction")
            
            try:
                biomarker_cache = get_biomarker_cache()
                
                # Try to extract biomarkers from all chunks using cache
                cache_results = []
                for chunk in content_chunks:
                    chunk_cached_biomarkers = extract_cached_biomarkers(chunk)
                    if chunk_cached_biomarkers:
                        cached_biomarkers.extend(chunk_cached_biomarkers)
                        cache_results.append({
                            "chunk": chunk,
                            "cached_biomarkers": chunk_cached_biomarkers,
                            "biomarker_count": len(chunk_cached_biomarkers)
                        })
                
                # Determine which chunks still need LLM processing
                if cached_biomarkers:
                    # If we found cached biomarkers, only process chunks that had no cache hits
                    # or had low-confidence cache hits that need LLM verification
                    cache_hit_chunks = {result["chunk"] for result in cache_results 
                                      if result["biomarker_count"] > 0}
                    
                    # Keep chunks that had no cache hits for LLM processing
                    remaining_chunks = [chunk for chunk in content_chunks 
                                      if chunk not in cache_hit_chunks]
                    
                    logger.info(f"✅ Cache found {len(cached_biomarkers)} biomarkers in {len(cache_hit_chunks)} chunks")
                    logger.info(f"🔄 {len(remaining_chunks)} chunks still need LLM processing")
                    
                    # Add cached biomarkers to the main collection
                    all_biomarkers.extend(cached_biomarkers)
                    
                    # Record cache statistics
                    cache_stats = biomarker_cache.get_cache_statistics()
                    metrics.record_api_call(
                        prompt_tokens=0,  # No tokens used for cache
                        completion_tokens=0,
                        total_tokens=0,
                        model="cache",
                        chunk_index=f"cache_extraction_{len(cached_biomarkers)}_biomarkers"
                    )
                    
                    # Record caching metrics
                    metrics.record_biomarker_caching_stats(
                        cache_stats=cache_stats,
                        cached_biomarkers_count=len(cached_biomarkers)
                    )
                else:
                    logger.info("📋 Cache found no biomarkers, proceeding with full LLM processing")
                    
            except Exception as e:
                logger.error(f"❌ Error in biomarker caching: {e}")
                logger.info("🔄 Falling back to full LLM processing")
                remaining_chunks = content_chunks
        else:
            logger.info("⚙️ Biomarker caching disabled, using full LLM processing")
        
        # Update chunk processing to use remaining chunks after caching
        content_chunks = remaining_chunks
        
        # Process chunks sequentially
        for i, chunk in enumerate(content_chunks):
            # Record optimized text metrics
            metrics.record_optimized_text(chunk["text"], chunk)
            
            # Skip chunks with very low biomarker confidence
            if (chunk["biomarker_confidence"] < 0.3 and 
                len(all_biomarkers) > 0):  # Skip only if we already have some biomarkers
                logger.info(f"Skipping low-confidence chunk #{i} from page {chunk['page_num']}")
                continue
            
            logger.info(f"Processing chunk #{i+1}/{len(content_chunks)} (page {chunk['page_num']}, confidence: {chunk['biomarker_confidence']:.2f})")
            
            try:
                # Create adaptive prompt if enabled
                if DOCUMENT_ANALYZER_CONFIG["adaptive_context"]["enabled"]:
                    prompt = create_adaptive_prompt(chunk, extraction_context, document_structure)
                    
                    # Extract biomarkers with context
                    chunk_biomarkers, updated_context = await extract_biomarkers_with_claude(
                        chunk["text"],
                        extraction_context=extraction_context,
                        adaptive_prompt=prompt
                    )
                    
                    # ENHANCED: Update extraction context with additional chunk information
                    if updated_context:
                        extraction_context = updated_context
                        # Add chunk-specific context for better tracking
                        extraction_context["section_context"]["last_chunk_confidence"] = chunk["biomarker_confidence"]
                        extraction_context["section_context"]["last_chunk_type"] = chunk["region_type"]
                        extraction_context["section_context"]["chunks_processed"] = extraction_context.get("chunks_processed", 0) + 1
                        
                        # Track biomarker discovery rate for early termination decisions
                        biomarkers_found_this_chunk = len(chunk_biomarkers) if chunk_biomarkers else 0
                        extraction_context["section_context"]["last_chunk_biomarkers"] = biomarkers_found_this_chunk
                        
                        # Calculate running average of biomarker discovery
                        total_chunks = extraction_context["section_context"]["chunks_processed"]
                        current_avg = extraction_context["section_context"].get("avg_biomarkers_per_chunk", 0)
                        new_avg = ((current_avg * (total_chunks - 1)) + biomarkers_found_this_chunk) / total_chunks
                        extraction_context["section_context"]["avg_biomarkers_per_chunk"] = new_avg
                    
                    logger.debug(f"[CONTEXT_UPDATE] Updated context: {len(extraction_context.get('known_biomarkers', {}))} known biomarkers, call count: {extraction_context.get('call_count', 0)}, chunks processed: {extraction_context.get('section_context', {}).get('chunks_processed', 0)}")
                else:
                    # Use standard extraction without context
                    chunk_biomarkers, _ = await extract_biomarkers_with_claude(
                        chunk["text"],
                        extraction_context=None,
                        adaptive_prompt=None
                    )
                
                # Record API call metrics
                if "token_usage" in extraction_context:
                    last_call = extraction_context["call_count"] - 1
                    prompt_tokens = extraction_context["token_usage"]["prompt"]
                    completion_tokens = extraction_context["token_usage"]["completion"]
                    
                    # If we have multiple calls, calculate just the last one
                    if last_call > 0:
                        prompt_tokens = prompt_tokens / last_call
                        completion_tokens = completion_tokens / last_call
                    
                    metrics.record_api_call(
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        chunk_info=chunk,
                        biomarkers_found=len(chunk_biomarkers)
                    )
                
                # Add page number to biomarkers
                for bm in chunk_biomarkers:
                    bm['page'] = chunk["page_num"]
                
                # Add to all biomarkers
                if chunk_biomarkers:
                    logger.info(f"✅ Extracted {len(chunk_biomarkers)} biomarkers from chunk {i+1}")
                    all_biomarkers.extend(chunk_biomarkers)
                    
                    # PHASE 2: Learn from successful LLM extractions to improve cache
                    if (biomarker_cache and 
                        cache_config.get("learn_from_extractions", True) and 
                        chunk_biomarkers):
                        try:
                            biomarker_cache.learn_from_extraction(
                                extracted_biomarkers=chunk_biomarkers,
                                text=chunk["text"],
                                method="llm"
                            )
                        except Exception as e:
                            logger.debug(f"Cache learning error: {e}")
                else:
                    logger.info(f"No biomarkers found in chunk #{i+1}")
                
                # ENHANCED: Early termination based on context and biomarker saturation
                if len(all_biomarkers) >= 30:  # Reasonable upper limit for lab reports
                    # Get context metrics for intelligent termination decision
                    context_confidence = extraction_context.get("confidence_threshold", 0.7)
                    chunks_processed = extraction_context.get("section_context", {}).get("chunks_processed", 0)
                    avg_biomarkers_per_chunk = extraction_context.get("section_context", {}).get("avg_biomarkers_per_chunk", 0)
                    last_chunk_biomarkers = extraction_context.get("section_context", {}).get("last_chunk_biomarkers", 0)
                    
                    # Intelligent termination conditions
                    should_terminate = False
                    termination_reason = ""
                    
                    if chunks_processed >= 3:  # We've processed several chunks
                        if last_chunk_biomarkers == 0 and avg_biomarkers_per_chunk < 1.0:
                            # Recent chunks aren't finding biomarkers and average is low
                            should_terminate = True
                            termination_reason = "low_recent_discovery_rate"
                        elif context_confidence > 0.8 and avg_biomarkers_per_chunk < 0.5:
                            # High confidence in what we've found, but discovery rate is very low
                            should_terminate = True
                            termination_reason = "high_confidence_low_discovery"
                    
                    # Check remaining chunks for high confidence potential
                    if should_terminate:
                        remaining_high_conf = any(c["biomarker_confidence"] > 0.9 for c in content_chunks[i+1:])
                        if remaining_high_conf:
                            should_terminate = False
                            termination_reason = "high_confidence_chunks_remaining"
                            logger.info(f"[EARLY_TERMINATION_OVERRIDE] Not terminating due to high-confidence chunks remaining")
                    
                    if should_terminate:
                        logger.info(f"[CONTEXT_EARLY_TERMINATION] Found {len(all_biomarkers)} biomarkers, terminating early due to: {termination_reason}")
                        logger.info(f"[TERMINATION_METRICS] Chunks processed: {chunks_processed}, Avg biomarkers/chunk: {avg_biomarkers_per_chunk:.2f}, Last chunk found: {last_chunk_biomarkers}")
                        break
                elif len(all_biomarkers) >= 50:  # Hard limit for very large reports
                    remaining_high_conf = any(c["biomarker_confidence"] > 0.8 for c in content_chunks[i+1:])
                    if not remaining_high_conf:
                        logger.info(f"[HARD_LIMIT_TERMINATION] Found {len(all_biomarkers)} biomarkers, hard limit reached")
                        break
            
            except Exception as e:
                logger.error(f"Error processing chunk #{i+1}: {str(e)}")
                # Continue with next chunk
        
        # Log metrics
        metrics.record_extraction_complete(
            extraction_time=time.time() - optimization_start - optimization_time,
            pages_processed=len(relevant_pages),
            biomarkers_extracted=len(all_biomarkers)
        )
        metrics.log_summary()
        
        if debug_metrics:
            metrics.save_detailed_report()
        
        # De-duplicate biomarkers
        all_biomarkers = _deduplicate_biomarkers(all_biomarkers)
        
        return all_biomarkers
    
    # Fall back to original method - process page by page
    logger.info(f"Using original sequential processing for {len(relevant_pages)} relevant pages")
    
    # Initialize cache for fallback processing if enabled
    cache_config = DOCUMENT_ANALYZER_CONFIG.get("biomarker_caching", {})
    biomarker_cache = None
    if cache_config.get("enabled", False):
        try:
            biomarker_cache = get_biomarker_cache()
            logger.info("🧠 Biomarker cache initialized for sequential processing")
        except Exception as e:
            logger.error(f"❌ Error initializing cache for sequential processing: {e}")
    
    for page_num, page_text in relevant_pages.items():
        logger.info(f"Processing page {page_num} sequentially")
        try:
            # Call the biomarker extractor
            page_biomarkers, _ = await extract_biomarkers_with_claude(page_text)
            
            if page_biomarkers:
                logger.info(f"Extracted {len(page_biomarkers)} biomarkers from page {page_num}")
                # Add page number info
                for bm in page_biomarkers:
                    bm['page'] = page_num
                all_biomarkers.extend(page_biomarkers)
                
                # Learn from successful LLM extractions in fallback mode
                if (biomarker_cache and 
                    cache_config.get("learn_from_extractions", True) and 
                    page_biomarkers):
                    try:
                        biomarker_cache.learn_from_extraction(
                            extracted_biomarkers=page_biomarkers,
                            text=page_text,
                            method="llm"
                        )
                    except Exception as e:
                        logger.debug(f"Cache learning error in fallback mode: {e}")
            else:
                logger.info(f"No biomarkers found on page {page_num}")
        except Exception as e:
            logger.error(f"Error processing page {page_num} sequentially: {str(e)}")
    
    # De-duplicate biomarkers
    all_biomarkers = _deduplicate_biomarkers(all_biomarkers)
    
    return all_biomarkers

def _deduplicate_biomarkers(biomarkers: List[Dict]) -> List[Dict]:
    """
    Deduplicate biomarkers based on standardized name.
    Keeps the first occurrence of each biomarker.
    
    Args:
        biomarkers: List of biomarker dictionaries
        
    Returns:
        Deduplicated list of biomarkers
    """
    seen_names = set()
    deduplicated = []
    
    for biomarker in biomarkers:
        name = biomarker.get('name', '').lower().strip()
        if name and name not in seen_names:
            seen_names.add(name)
            deduplicated.append(biomarker)
    
    return deduplicated

def contain_biomarker_patterns(text):
    """
    Check if text contains potential biomarker patterns.
    
    Args:
        text: The text to check
        
    Returns:
        bool: True if the text contains potential biomarker patterns
    """
    if not text:
        return False
        
    # Common biomarker indicators
    indicators = [
        r'\b\d+\.?\d*\s*(?:mg/dL|g/dL|mmol/L|mol/L|U/L|IU/L|ng/mL|pg/mL|mIU/L|μIU/mL|μg/dL|mcg/dL|%|mEq/L)',  # Values with units
        r'\bnormal\s*range',
        r'\breference\s*range',
        r'\brange',
        r'\bvalue',
        r'\bresult',
        r'\blow\b|\bhigh\b',
        r'\bpositive\b|\bnegative\b',
        r'\bchemistry\b',
        r'\bhematology\b',
        r'\btest\b|\btests\b'
    ]
    
    for pattern in indicators:
        if re.search(pattern, text, re.IGNORECASE):
            return True
            
    return False

# --- End Helper Functions ---


def extract_text_from_pdf(file_path: str) -> Dict[int, str]:
    """
    Extract text from all pages of a PDF file using PyPDF2 or Tesseract OCR for image-based PDFs.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dict[int, str]: Dictionary mapping page number (0-indexed) to extracted text.
    """
    logger.info(f"[PDF_TEXT_EXTRACTION_START] Extracting text from PDF: {file_path}")
    start_time = datetime.utcnow()

    try:
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        # Open the PDF file
        with open(file_path, 'rb') as file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(file)
            
            # Log PDF metadata
            total_pages = len(pdf_reader.pages)
            logger.debug(f"[PDF_METADATA] Number of pages: {total_pages}")
            if pdf_reader.metadata:
                logger.debug(f"[PDF_METADATA] Author: {pdf_reader.metadata.get('/Author', 'None')}")
            logger.debug(f"[PDF_METADATA] Creation date: {pdf_reader.metadata.get('/CreationDate', 'None')}")

            # Initialize a dictionary to store text per page
            pages_text_dict: Dict[int, str] = {}

            # Loop through each page and extract text
            logger.info(f"[PAGE_EXTRACTION] Extracting text from all {total_pages} pages.")
            for page_num in range(total_pages):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    pages_text_dict[page_num] = page_text if page_text else ""
                    logger.debug(f"[PAGE_EXTRACTION] Page {page_num}: Extracted {len(page_text) if page_text else 0} characters")
                except Exception as page_error:
                    logger.error(f"[PAGE_EXTRACTION_ERROR] Error extracting text from page {page_num}: {str(page_error)}")
                    pages_text_dict[page_num] = "" # Store empty string on error

            # Log extracted text for debugging (save as JSON)
            debug_text_path = os.path.join(log_dir, f"pdf_extracted_text_{os.path.basename(file_path)}.json")
            try:
                with open(debug_text_path, "w") as f:
                    json.dump(pages_text_dict, f, indent=2)
                logger.debug(f"[EXTRACTED_TEXT_SAVED] PDF text per page saved to {debug_text_path}")
            except Exception as e:
                logger.error(f"[TEXT_SAVE_ERROR] Could not save extracted text dictionary: {str(e)}")

            # If no text was extracted from any page, the PDF might be image-based
            if not any(pages_text_dict.values()):
                logger.info("[OCR_FALLBACK] No text extracted with PyPDF2 from any page, PDF might be image-based. Attempting OCR...")
                pages_text_dict = _extract_text_with_ocr(file_path)

                # Save OCR text for debugging (save as JSON)
                debug_ocr_path = os.path.join(log_dir, f"pdf_ocr_text_{os.path.basename(file_path)}.json")
                try:
                    with open(debug_ocr_path, "w") as f:
                        json.dump(pages_text_dict, f, indent=2)
                    logger.debug(f"[OCR_TEXT_SAVED] OCR text per page saved to {debug_ocr_path}")
                except Exception as e:
                    logger.error(f"[OCR_TEXT_SAVE_ERROR] Could not save OCR text dictionary: {str(e)}")

            extraction_time = (datetime.utcnow() - start_time).total_seconds()
            total_chars = sum(len(txt) for txt in pages_text_dict.values())
            logger.info(f"[PDF_TEXT_EXTRACTION_COMPLETE] Extracted {total_chars} characters across {len(pages_text_dict)} pages in {extraction_time:.2f} seconds")

            return pages_text_dict
    except Exception as e:
        logger.error(f"[PDF_EXTRACTION_ERROR] Error extracting text from PDF: {str(e)}")
        raise

def _extract_text_with_ocr(file_path: str) -> Dict[int, str]:
    """
    Extract text from all pages of an image-based PDF using Tesseract OCR.

    Args:
        file_path: Path to the PDF file

    Returns:
        Dict[int, str]: Dictionary mapping page number (0-indexed) to extracted text.
    """
    try:
        logger.info(f"[OCR_START] Extracting text from image-based PDF using OCR: {file_path}")
        ocr_start_time = datetime.utcnow()

        # Create debug directory for OCR images
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
        debug_img_dir = os.path.join(log_dir, f"ocr_images_{os.path.basename(file_path).replace('.pdf', '')}")
        os.makedirs(debug_img_dir, exist_ok=True)
        
        # Check if Tesseract is installed
        try:
            tesseract_path = os.environ.get('TESSERACT_PATH', '/usr/local/bin/tesseract')
            if not os.path.exists(tesseract_path):
                logger.error(f"[OCR_ERROR] Tesseract not found at path: {tesseract_path}")
                return "OCR processing failed: Tesseract not found."
            
            # Set Tesseract path
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            logger.debug(f"[OCR_CONFIG] Using Tesseract at: {tesseract_path}")
            
            # Get Tesseract version for debugging
            try:
                import subprocess
                tesseract_version = subprocess.check_output([tesseract_path, '--version']).decode('utf-8').strip()
                logger.debug(f"[OCR_CONFIG] Tesseract version: {tesseract_version}")
            except Exception as e:
                logger.warning(f"[OCR_CONFIG] Could not get Tesseract version: {str(e)}")
        except Exception as e:
            logger.error(f"[OCR_CONFIG_ERROR] Error configuring Tesseract: {str(e)}")
        
        # Convert PDF to images
        logger.debug("[OCR_PROCESS] Converting PDF to images")
        # Process all pages
        pages = pdf2image.convert_from_path(file_path, dpi=300) # Removed page limits
        total_pages_converted = len(pages)
        logger.debug(f"[OCR_PROCESS] Converted {total_pages_converted} pages to images")

        # Extract text from each page
        pages_text_dict: Dict[int, str] = {}
        for i, page in enumerate(pages):
            logger.debug(f"[OCR_PAGE_PROCESSING] Processing page {i} of {total_pages_converted-1}")
            page_start_time = datetime.utcnow()

            # Save the page image for debugging
            img_path = os.path.join(debug_img_dir, f"page_{i}.png")
            try:
                page.save(img_path)
                logger.debug(f"[OCR_IMAGE_SAVED] Saved page {i} image to {img_path}")
            except Exception as e:
                logger.error(f"[OCR_IMAGE_SAVE_ERROR] Could not save page image: {str(e)}")

            # Use pytesseract to get text from the image
            try:
                # Try different OCR configurations for better results
                page_text = pytesseract.image_to_string(page, config='--psm 6')  # Assume a single uniform block of text

                # If no text was extracted, try another mode
                if not page_text.strip():
                    logger.debug(f"[OCR_RETRY] No text found with default settings, trying alternative OCR mode")
                    page_text = pytesseract.image_to_string(page, config='--psm 3')  # Fully automatic page segmentation

                page_time = (datetime.utcnow() - page_start_time).total_seconds()

                # Save individual page OCR results
                page_text_path = os.path.join(debug_img_dir, f"page_{i}_text.txt")
                try:
                    with open(page_text_path, "w") as f:
                        f.write(page_text)
                    logger.debug(f"[OCR_PAGE_TEXT_SAVED] OCR text for page {i} saved to {page_text_path}")
                except Exception as e:
                    logger.error(f"[OCR_PAGE_TEXT_SAVE_ERROR] Could not save page OCR text: {str(e)}")

                logger.debug(f"[OCR_PAGE_COMPLETE] Page {i} processed in {page_time:.2f} seconds, extracted {len(page_text)} characters")
                pages_text_dict[i] = page_text
            except Exception as e:
                logger.error(f"[OCR_PAGE_ERROR] Error performing OCR on page {i}: {str(e)}")
                pages_text_dict[i] = "" # Store empty string on error

        if not any(pages_text_dict.values()):
            logger.warning("[OCR_NO_TEXT] OCR could not extract any text from the PDF")
            # Return empty dict, but log the issue
            return {}

        ocr_time = (datetime.utcnow() - ocr_start_time).total_seconds()
        logger.info(f"[OCR_COMPLETE] OCR processing completed in {ocr_time:.2f} seconds")
        return pages_text_dict

    except Exception as e:
        logger.error(f"[OCR_ERROR] Error during OCR processing: {str(e)}")
        # Return empty dict on major error
        return {}

async def process_pdf_background(pdf_id: int, db_session=None):
    """
    Process PDF in the background.
    
    Args:
        pdf_id: PDF ID from database
        db_session: SQLAlchemy session
    """
    # Create new session if not provided
    if db_session is None:
        db_session = SessionLocal()
    
    # Get PDF from database
    try:
        pdf = db_session.query(PDF).filter(PDF.id == pdf_id).first()
        if not pdf:
            logger.error(f"PDF {pdf_id} not found in database")
            return
        
        # Update status and record when processing started
        logger.info(f"Starting to process PDF {pdf_id}")
        pdf.status = "processing"
        pdf.processing_started_at = datetime.utcnow()
        db_session.commit()
        
        # Extract text from all pages
        logger.info(f"Extracting text from PDF {pdf_id}")
        pages_text_dict = extract_text_from_pdf(pdf.file_path)

        # Combine text for saving (or consider saving page-wise if needed later)
        full_extracted_text = "\n--- Page Break ---\n".join(pages_text_dict.values())
        pdf.extracted_text = full_extracted_text # Store combined text for now
        db_session.commit()

        # After text extraction, analyze document structure
        document_structure = None
        if DOCUMENT_ANALYZER_CONFIG["enabled"] and DOCUMENT_ANALYZER_CONFIG["structure_analysis"]["enabled"]:
            logging.info(f"Analyzing document structure for {pdf_id}")
            document_structure = analyze_document_structure(pdf.file_path, pages_text_dict)
            logging.info(f"Document structure analysis complete with confidence {document_structure['confidence']}")
            
            # If analysis confidence is low and fallback is enabled, ignore structure
            if (document_structure["confidence"] < 0.5 and 
                DOCUMENT_ANALYZER_CONFIG["structure_analysis"]["fallback_to_legacy"]):
                logging.warning(f"Low structure confidence ({document_structure['confidence']}), using legacy processing")
                document_structure = None
        
        # Filter relevant pages with structure context
        relevant_pages = filter_relevant_pages(
            pages_text_dict,
            document_structure=document_structure
        )
        
        # Process pages with structure context
        extracted_biomarkers = await process_pages_sequentially(
            relevant_pages,
            document_structure=document_structure
        )

        # --- Metadata Extraction (Phase 3) ---
        # Extract metadata using only the first few pages (e.g., 0, 1, 2)
        num_pages_for_metadata = 3
        metadata_text = ""
        for i in range(num_pages_for_metadata):
            metadata_text += pages_text_dict.get(i, "") + "\n" # Add newline separator
        
        logger.info(f"Parsing metadata from first {num_pages_for_metadata} pages' text for PDF {pdf_id}")
        from app.services.metadata_parser import extract_metadata_with_claude
        
        # Properly handle the async function
        try:
            # Since we're already in an async context, just await the function
            metadata = await extract_metadata_with_claude(metadata_text.strip(), pdf.filename)
            logger.info(f"Successfully extracted metadata")
        except Exception as metadata_error:
            logger.error(f"Error extracting metadata: {str(metadata_error)}")
            metadata = {}
        
        # Update PDF with extracted metadata (existing logic)
        if metadata:
            logger.info(f"Extracted metadata for PDF {pdf_id}: {metadata}")
            # First, handle the report_date separately to ensure proper conversion
            if metadata.get("report_date"):
                # Convert string date to datetime object
                report_date_str = metadata.get("report_date")
                try:
                    pdf.report_date = dateutil.parser.parse(report_date_str)
                    logger.info(f"Converted report date from '{report_date_str}' to {pdf.report_date}")
                    db_session.commit()  # Commit report_date change immediately
                except Exception as e:
                    logger.error(f"Failed to parse report date '{report_date_str}': {str(e)}")
            
            # Handle other metadata fields that don't require type conversion
            update_dict = {}
            if metadata.get("patient_name"):
                update_dict["patient_name"] = metadata.get("patient_name")
            if metadata.get("patient_gender"):
                update_dict["patient_gender"] = metadata.get("patient_gender")
            if metadata.get("patient_id"):
                update_dict["patient_id"] = metadata.get("patient_id")
            if metadata.get("lab_name"):
                update_dict["lab_name"] = metadata.get("lab_name")
            
            # Apply updates if there are any
            if update_dict:
                for key, value in update_dict.items():
                    setattr(pdf, key, value)
                logger.info(f"Updated PDF with metadata: {update_dict}")
                db_session.commit()
            
            # Finally, handle patient_age separately as it requires integer conversion
            if metadata.get("patient_age"):
                # Convert patient age to integer if it's a string
                age_str = metadata.get("patient_age")
                try:
                    # Extract numeric part if it includes units like "33 years"
                    age_numeric = re.search(r'\d+', str(age_str))
                    if age_numeric:
                        pdf.patient_age = int(age_numeric.group())
                        logger.info(f"Converted patient age from '{age_str}' to {pdf.patient_age}")
                        db_session.commit()  # Commit age change separately
                    else:
                        logger.warning(f"Could not extract numeric age from '{age_str}'")
                except Exception as e:
                    logger.error(f"Failed to parse patient age '{age_str}': {str(e)}")
        else:
            logger.warning(f"No metadata extracted for PDF {pdf_id}")
        
        # --- Save Biomarkers ---
        if not extracted_biomarkers:
            logger.warning(f"No biomarkers extracted after filtering and sequential processing for PDF {pdf_id}")
        else:
            logger.info(f"Extracted {len(extracted_biomarkers)} biomarkers from PDF {pdf_id}")

            # Save biomarkers to database
            for biomarker in extracted_biomarkers:
                db_session.add(Biomarker(
                    pdf_id=pdf.id,
                    profile_id=pdf.profile_id,
                    name=biomarker.get("name", "Unknown"),
                    original_name=biomarker.get("original_name", "Unknown"),
                    original_value=biomarker.get("original_value", ""),
                    value=biomarker.get("value", 0.0),
                    original_unit=biomarker.get("original_unit", ""),
                    unit=biomarker.get("unit", ""),
                    reference_range_low=biomarker.get("reference_range_low"),
                    reference_range_high=biomarker.get("reference_range_high"),
                    reference_range_text=biomarker.get("reference_range_text", ""),
                    category=biomarker.get("category", "Other"),
                    is_abnormal=biomarker.get("is_abnormal", False)
                ))
            
            # Update parsing confidence
            confidence = 0.0
            for biomarker in extracted_biomarkers:
                confidence += biomarker.get("confidence", 0.0)
            confidence = confidence / len(extracted_biomarkers) if extracted_biomarkers else 0.0
            pdf.parsing_confidence = confidence
        
        # Update status
        pdf.status = "processed"
        pdf.processed_date = datetime.utcnow()
        db_session.commit() # Commit biomarker saves and status update

        # --- Trigger Health Summary Generation (Temporarily disabled) ---
        if pdf.profile_id and extracted_biomarkers: # Only generate if biomarkers were saved and profile exists
            try:
                logger.info(f"Triggering health summary generation for profile {pdf.profile_id} after processing PDF {pdf_id}")
                # Run the async function synchronously in this background task context
                asyncio.run(generate_and_update_health_summary(pdf.profile_id, db_session))
            except Exception as summary_error:
                # Log the error but don't let it fail the whole PDF processing
                logger.error(f"Error during triggered health summary generation for profile {pdf.profile_id}: {summary_error}", exc_info=True)
        elif not pdf.profile_id:
             logger.warning(f"PDF {pdf_id} has no associated profile_id, skipping health summary generation.")
        # If no biomarkers were found, summary generation is skipped implicitly by health_summary_service

        logger.info(f"Completed processing PDF {pdf_id}")
    except Exception as e:
        logger.error(f"Error processing PDF {pdf_id}: {str(e)}")
        pdf.status = "error"
        pdf.error_message = str(e)
        try:
            db_session.rollback()  # Rollback any pending transactions
            db_session.commit()
        except Exception as commit_error:
            logger.error(f"Error during error handling commit: {str(commit_error)}")
    finally:
        # Only close the session if we created it in this function
        if db_session is not None:
            db_session.close()
            logger.debug(f"Database session closed for PDF {pdf_id}")

# This is kept for backward compatibility
def parse_biomarkers_from_text(text: str, pdf_id=None) -> Tuple[List[Dict[str, Any]], float]:
    """
    Parse biomarker data from extracted text.
    
    Args:
        text: Extracted text from the PDF
        pdf_id: Optional PDF ID (for backward compatibility)

    Returns:
        Tuple containing a list of biomarker dictionaries and a confidence score
    """
    # Use the improved parser from biomarker_parser.py
    from app.services.biomarker_parser import parse_biomarkers_from_text as fallback_parser

    try:
        # First try to use the Claude API for better results
        if os.environ.get('ANTHROPIC_API_KEY'):
            from app.services.biomarker_parser import extract_biomarkers_with_claude
            # Ensure the pdf_id is properly formatted and sanitized to avoid format specifier issues
            pdf_filename = f"pdf_{pdf_id if pdf_id else 'unknown'}.pdf"
            biomarkers, _ = extract_biomarkers_with_claude(text, pdf_filename)
            
            # Calculate average confidence
            confidence = 0.0
            if biomarkers:
                for biomarker in biomarkers:
                    confidence += biomarker.get("confidence", 0.0)
                confidence = confidence / len(biomarkers)
            
            return biomarkers, confidence
    except Exception as e:
        logger.warning(f"Failed to extract biomarkers with Claude API: {str(e)}. Falling back to pattern matching.")
    
    # Fallback to pattern matching
    biomarkers = fallback_parser(text)
    confidence = 0.5  # Lower confidence for fallback parser
    
    return biomarkers, confidence
