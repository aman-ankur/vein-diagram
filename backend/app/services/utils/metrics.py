"""
Metrics Collection and Analysis Module

This module provides utilities for tracking token usage, extraction performance,
and optimization metrics throughout the biomarker extraction pipeline.
"""
from typing import Dict, List, Any, Optional
import json
import os
import logging
from datetime import datetime
import time

from app.services.utils.content_optimization import estimate_tokens

class TokenUsageMetrics:
    """
    Track and analyze token usage metrics for API calls and content optimization.
    """
    
    def __init__(self, 
                 document_id: str = None, 
                 save_debug: bool = False,
                 debug_dir: str = None):
        """
        Initialize token usage metrics tracker.
        
        Args:
            document_id: Identifier for the document being processed
            save_debug: Whether to save detailed debug information
            debug_dir: Directory to save debug information
        """
        self.document_id = document_id or f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.save_debug = save_debug
        self.debug_dir = debug_dir
        
        # Token usage metrics
        self.original_tokens = 0
        self.optimized_tokens = 0
        self.api_calls = 0
        self.call_details = []
        
        # Time metrics
        self.start_time = time.time()
        self.optimization_time = 0
        self.extraction_time = 0
        
        # Performance metrics
        self.biomarkers_extracted = 0
        self.pages_processed = 0
        self.chunks_processed = 0
        
        # Debug info for chunks
        self.chunk_details = []
        
        # Ensure debug directory exists if saving debug info
        if self.save_debug and self.debug_dir:
            os.makedirs(self.debug_dir, exist_ok=True)
    
    def record_original_text(self, text: str, page_num: int = None) -> int:
        """
        Record token count of original text.
        
        Args:
            text: Original text
            page_num: Optional page number
            
        Returns:
            Token count
        """
        tokens = estimate_tokens(text)
        self.original_tokens += tokens
        
        if self.save_debug and page_num is not None:
            self.chunk_details.append({
                "type": "original",
                "page_num": page_num,
                "tokens": tokens,
                "length": len(text)
            })
            
        return tokens
    
    def record_optimized_text(self, text: str, chunk_info: Dict[str, Any]) -> int:
        """
        Record token count of optimized text.
        
        Args:
            text: Optimized text
            chunk_info: Information about the chunk
            
        Returns:
            Token count
        """
        tokens = estimate_tokens(text)
        self.optimized_tokens += tokens
        
        if self.save_debug:
            self.chunk_details.append({
                "type": "optimized",
                "page_num": chunk_info.get("page_num"),
                "region_type": chunk_info.get("region_type"),
                "tokens": tokens,
                "length": len(text),
                "confidence": chunk_info.get("biomarker_confidence", 0)
            })
            
        return tokens
    
    def record_api_call(self, 
                        prompt_tokens: int, 
                        completion_tokens: int, 
                        chunk_info: Dict[str, Any],
                        biomarkers_found: int = 0) -> None:
        """
        Record details of an API call.
        
        Args:
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            chunk_info: Information about the chunk
            biomarkers_found: Number of biomarkers extracted
        """
        self.api_calls += 1
        total_tokens = prompt_tokens + completion_tokens
        
        call_detail = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "biomarkers_found": biomarkers_found,
            "page_num": chunk_info.get("page_num"),
            "region_type": chunk_info.get("region_type", "unknown"),
            "token_efficiency": biomarkers_found / total_tokens if total_tokens > 0 else 0
        }
        
        self.call_details.append(call_detail)
        self.biomarkers_extracted += biomarkers_found
        self.chunks_processed += 1
    
    def record_optimization_complete(self, 
                                     optimization_time: float,
                                     chunk_count: int) -> None:
        """
        Record completion of content optimization.
        
        Args:
            optimization_time: Time taken for optimization (seconds)
            chunk_count: Number of chunks created
        """
        self.optimization_time = optimization_time
        self.chunks_processed = chunk_count
    
    def record_extraction_complete(self, 
                                   extraction_time: float,
                                   pages_processed: int,
                                   biomarkers_extracted: int) -> None:
        """
        Record completion of biomarker extraction.
        
        Args:
            extraction_time: Time taken for extraction (seconds)
            pages_processed: Number of pages processed
            biomarkers_extracted: Number of biomarkers extracted
        """
        self.extraction_time = extraction_time
        self.pages_processed = pages_processed
        self.biomarkers_extracted = biomarkers_extracted
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of token usage metrics.
        
        Returns:
            Dictionary with summary metrics
        """
        # Calculate token reduction
        if self.original_tokens == 0:
            reduction_percentage = 0
        else:
            reduction_percentage = (1 - self.optimized_tokens/self.original_tokens) * 100
        
        # Calculate cost savings (approximate based on Claude pricing)
        # ~$0.008 per 1K tokens for Claude Sonnet 3
        approx_cost_per_1k = 0.008
        original_cost = (self.original_tokens / 1000) * approx_cost_per_1k
        optimized_cost = (self.optimized_tokens / 1000) * approx_cost_per_1k
        cost_savings = original_cost - optimized_cost
        
        # Calculate performance metrics
        total_time = time.time() - self.start_time
        tokens_per_biomarker = sum(d["total_tokens"] for d in self.call_details) / max(1, self.biomarkers_extracted)
        
        # Build full summary
        summary = {
            "document_id": self.document_id,
            "timestamp": datetime.now().isoformat(),
            "token_metrics": {
                "original_tokens": self.original_tokens,
                "optimized_tokens": self.optimized_tokens,
                "token_reduction_percentage": reduction_percentage,
                "token_reduction_absolute": self.original_tokens - self.optimized_tokens,
                "estimated_cost_savings": cost_savings
            },
            "api_metrics": {
                "api_calls": self.api_calls,
                "avg_tokens_per_call": sum(d["total_tokens"] for d in self.call_details) / max(1, self.api_calls),
                "prompt_tokens": sum(d["prompt_tokens"] for d in self.call_details),
                "completion_tokens": sum(d["completion_tokens"] for d in self.call_details),
                "total_tokens_used": sum(d["total_tokens"] for d in self.call_details)
            },
            "performance_metrics": {
                "biomarkers_extracted": self.biomarkers_extracted,
                "pages_processed": self.pages_processed,
                "chunks_processed": self.chunks_processed,
                "tokens_per_biomarker": tokens_per_biomarker,
                "biomarkers_per_page": self.biomarkers_extracted / max(1, self.pages_processed),
                "optimization_time_seconds": self.optimization_time,
                "extraction_time_seconds": self.extraction_time,
                "total_time_seconds": total_time
            }
        }
        
        return summary
    
    def log_summary(self) -> None:
        """
        Log a summary of token usage metrics.
        """
        summary = self.get_summary()
        token_metrics = summary["token_metrics"]
        api_metrics = summary["api_metrics"]
        perf_metrics = summary["performance_metrics"]
        
        logging.info("=" * 50)
        logging.info(f"OPTIMIZATION METRICS SUMMARY - {self.document_id}")
        logging.info("=" * 50)
        logging.info(f"Token Reduction: {token_metrics['token_reduction_percentage']:.2f}% ({token_metrics['token_reduction_absolute']} tokens)")
        logging.info(f"API Calls: {api_metrics['api_calls']}, Avg tokens per call: {api_metrics['avg_tokens_per_call']:.1f}")
        logging.info(f"Biomarkers: {perf_metrics['biomarkers_extracted']}, Tokens per biomarker: {perf_metrics['tokens_per_biomarker']:.1f}")
        logging.info(f"Estimated cost savings: ${token_metrics['estimated_cost_savings']:.3f}")
        logging.info(f"Processing time: {perf_metrics['total_time_seconds']:.2f}s (optimization: {perf_metrics['optimization_time_seconds']:.2f}s)")
        logging.info("=" * 50)
    
    def save_detailed_report(self, filename: str = None) -> None:
        """
        Save a detailed report of token usage metrics.
        
        Args:
            filename: Optional filename, otherwise auto-generated
        """
        if not self.save_debug:
            return
            
        if not filename:
            filename = f"token_metrics_{self.document_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
        if self.debug_dir:
            filepath = os.path.join(self.debug_dir, filename)
        else:
            filepath = filename
        
        summary = self.get_summary()
        
        # Add detailed call information
        detailed_report = {
            **summary,
            "call_details": self.call_details,
            "chunk_details": self.chunk_details
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(detailed_report, f, indent=2)
            logging.info(f"Detailed metrics report saved to {filepath}")
        except Exception as e:
            logging.error(f"Failed to save detailed metrics report: {e}")


class ExtractionPerformanceTracker:
    """
    Track biomarker extraction performance metrics for accuracy evaluation.
    """
    
    def __init__(self, document_id: str = None):
        """
        Initialize extraction performance tracker.
        
        Args:
            document_id: Identifier for the document being processed
        """
        self.document_id = document_id or f"doc_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.extraction_start = time.time()
        
        # Extraction metrics
        self.true_positives = 0
        self.false_positives = 0
        self.false_negatives = 0
        self.biomarker_confidence_sum = 0
        self.biomarker_count = 0
        
        # Individual biomarker tracking
        self.extracted_biomarkers = []
    
    def record_biomarker(self, 
                         biomarker: Dict[str, Any], 
                         is_valid: bool = True,
                         confidence: float = None) -> None:
        """
        Record a biomarker extraction result.
        
        Args:
            biomarker: The extracted biomarker
            is_valid: Whether the biomarker is valid
            confidence: Override confidence if available
        """
        # Extract confidence from biomarker if not provided
        if confidence is None and "confidence" in biomarker:
            confidence = float(biomarker.get("confidence", 0.0))
        
        # Store confidence for averaging
        if confidence is not None:
            self.biomarker_confidence_sum += confidence
            self.biomarker_count += 1
        
        # Track true/false positives
        if is_valid:
            self.true_positives += 1
        else:
            self.false_positives += 1
        
        # Store biomarker details
        self.extracted_biomarkers.append({
            "biomarker": biomarker,
            "is_valid": is_valid,
            "confidence": confidence
        })
    
    def record_missed_biomarker(self, biomarker_name: str, reason: str = None) -> None:
        """
        Record a biomarker that was missed during extraction.
        
        Args:
            biomarker_name: Name of the missed biomarker
            reason: Optional reason for the miss
        """
        self.false_negatives += 1
        
        # Store missed biomarker details
        self.extracted_biomarkers.append({
            "biomarker": {"name": biomarker_name},
            "is_valid": False,
            "is_missed": True,
            "reason": reason
        })
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for biomarker extraction.
        
        Returns:
            Dictionary with performance metrics
        """
        # Calculate precision, recall, and F1
        if self.true_positives + self.false_positives == 0:
            precision = 0
        else:
            precision = self.true_positives / (self.true_positives + self.false_positives)
            
        if self.true_positives + self.false_negatives == 0:
            recall = 0
        else:
            recall = self.true_positives / (self.true_positives + self.false_negatives)
            
        if precision + recall == 0:
            f1 = 0
        else:
            f1 = 2 * (precision * recall) / (precision + recall)
        
        # Calculate average confidence
        avg_confidence = self.biomarker_confidence_sum / max(1, self.biomarker_count)
        
        # Calculate processing time
        processing_time = time.time() - self.extraction_start
        
        return {
            "document_id": self.document_id,
            "timestamp": datetime.now().isoformat(),
            "accuracy_metrics": {
                "true_positives": self.true_positives,
                "false_positives": self.false_positives,
                "false_negatives": self.false_negatives,
                "precision": precision,
                "recall": recall,
                "f1_score": f1
            },
            "confidence_metrics": {
                "avg_confidence": avg_confidence,
                "biomarker_count": self.biomarker_count
            },
            "processing_metrics": {
                "total_time_seconds": processing_time,
                "biomarkers_per_second": self.biomarker_count / max(1, processing_time)
            }
        }
    
    def log_performance_summary(self) -> None:
        """
        Log a summary of extraction performance metrics.
        """
        metrics = self.get_performance_metrics()
        accuracy = metrics["accuracy_metrics"]
        confidence = metrics["confidence_metrics"]
        processing = metrics["processing_metrics"]
        
        logging.info("=" * 50)
        logging.info(f"EXTRACTION PERFORMANCE SUMMARY - {self.document_id}")
        logging.info("=" * 50)
        logging.info(f"Precision: {accuracy['precision']:.3f}, Recall: {accuracy['recall']:.3f}, F1: {accuracy['f1_score']:.3f}")
        logging.info(f"True Positives: {accuracy['true_positives']}, False Positives: {accuracy['false_positives']}, False Negatives: {accuracy['false_negatives']}")
        logging.info(f"Average Confidence: {confidence['avg_confidence']:.3f}")
        logging.info(f"Processing Speed: {processing['biomarkers_per_second']:.2f} biomarkers/second")
        logging.info("=" * 50) 