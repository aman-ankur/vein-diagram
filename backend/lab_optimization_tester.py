#!/usr/bin/env python3
"""
Lab Optimization Tester
========================

Comprehensive testing tool for validating chunking strategies, accuracy metrics, 
and token optimization across different lab report formats.

Features:
- Real PDF processing with multiple optimization modes
- Detailed metrics collection and analysis
- Support for various lab formats (Quest, LabCorp, etc.)
- Performance benchmarking
- Biomarker accuracy validation

Usage:
    python lab_optimization_tester.py --pdf path/to/report.pdf
    python lab_optimization_tester.py --pdf path/to/report.pdf --mode balanced
    python lab_optimization_tester.py --benchmark --all-modes
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add the app directory to Python path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import our application modules
from app.services.pdf_service import extract_text_from_pdf
from app.services.biomarker_parser import extract_biomarkers_with_claude
from app.services.utils.content_optimization import (
    optimize_content_for_extraction,
    estimate_tokens,
    optimize_content_chunks_legacy,
    optimize_content_chunks_accuracy_first,
    optimize_content_chunks_balanced
)


class LabOptimizationTester:
    """Comprehensive tester for lab report optimization strategies."""
    
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode
        self.results = {}
        self.start_time = None
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration."""
        import logging
        
        log_level = logging.DEBUG if self.debug_mode else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/lab_optimization_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def test_pdf_optimization(self, pdf_path: str, mode: str = "all") -> Dict[str, Any]:
        """
        Test PDF optimization with specified mode(s).
        
        Args:
            pdf_path: Path to the PDF file
            mode: Optimization mode ("legacy", "accuracy", "balanced", "all")
            
        Returns:
            Dictionary containing test results and metrics
        """
        self.start_time = time.time()
        self.logger.info(f"🧪 Starting optimization test for: {pdf_path}")
        self.logger.info(f"📊 Test mode: {mode}")
        
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Extract text from PDF
        self.logger.info("📄 Extracting text from PDF...")
        try:
            pages_text_dict = extract_text_from_pdf(pdf_path)
            total_pages = len(pages_text_dict)
            original_text_length = sum(len(text) for text in pages_text_dict.values())
            
            self.logger.info(f"✅ Extracted text from {total_pages} pages")
            self.logger.info(f"📏 Total text length: {original_text_length:,} characters")
        except Exception as e:
            self.logger.error(f"❌ Failed to extract text: {e}")
            return {"error": str(e)}
        
        # Test different optimization modes
        test_results = {
            "pdf_path": pdf_path,
            "total_pages": total_pages,
            "original_text_length": original_text_length,
            "test_timestamp": datetime.now().isoformat(),
            "modes_tested": {}
        }
        
        modes_to_test = ["legacy", "accuracy", "balanced"] if mode == "all" else [mode]
        
        for test_mode in modes_to_test:
            self.logger.info(f"\n🔬 Testing {test_mode.upper()} mode...")
            mode_results = self._test_single_mode(pages_text_dict, test_mode)
            test_results["modes_tested"][test_mode] = mode_results
        
        # Calculate comparative metrics
        if len(modes_to_test) > 1:
            test_results["comparison"] = self._calculate_mode_comparison(test_results["modes_tested"])
        
        self.logger.info(f"\n✅ Test completed in {time.time() - self.start_time:.2f} seconds")
        return test_results
    
    def _test_single_mode(self, pages_text_dict: Dict[int, str], mode: str) -> Dict[str, Any]:
        """Test a single optimization mode."""
        mode_start_time = time.time()
        
        # Set environment variables for the mode
        self._set_mode_environment(mode)
        
        try:
            # Optimize content
            optimized_chunks = optimize_content_for_extraction(pages_text_dict, {})
            
            # Calculate token metrics
            original_tokens = sum(estimate_tokens(text) for text in pages_text_dict.values())
            optimized_tokens = sum(chunk.get("estimated_tokens", 0) for chunk in optimized_chunks)
            token_reduction = ((original_tokens - optimized_tokens) / original_tokens * 100) if original_tokens > 0 else 0
            
            # Extract biomarkers for accuracy testing
            biomarkers = []
            total_confidence = 0
            api_calls = 0
            
            for chunk in optimized_chunks[:3]:  # Test first 3 chunks for speed
                try:
                    chunk_biomarkers = extract_biomarkers_with_claude(
                        chunk["text"], 
                        chunk["page_num"], 
                        existing_biomarkers=biomarkers
                    )
                    biomarkers.extend(chunk_biomarkers)
                    total_confidence += sum(float(b.get("confidence", 0)) for b in chunk_biomarkers)
                    api_calls += 1
                except Exception as e:
                    self.logger.warning(f"⚠️  Chunk extraction failed: {e}")
            
            avg_confidence = (total_confidence / len(biomarkers)) if biomarkers else 0
            
            mode_results = {
                "processing_time": time.time() - mode_start_time,
                "chunks_created": len(optimized_chunks),
                "token_metrics": {
                    "original_tokens": original_tokens,
                    "optimized_tokens": optimized_tokens,
                    "token_reduction_percent": token_reduction,
                    "tokens_saved": original_tokens - optimized_tokens
                },
                "biomarker_metrics": {
                    "biomarkers_extracted": len(biomarkers),
                    "average_confidence": avg_confidence,
                    "high_confidence_count": len([b for b in biomarkers if float(b.get("confidence", 0)) >= 0.7]),
                    "api_calls_made": api_calls
                },
                "chunk_analysis": {
                    "avg_chunk_tokens": optimized_tokens / len(optimized_chunks) if optimized_chunks else 0,
                    "chunk_sizes": [chunk.get("estimated_tokens", 0) for chunk in optimized_chunks]
                }
            }
            
            self.logger.info(f"📊 {mode.upper()} Results:")
            self.logger.info(f"   💰 Token reduction: {token_reduction:.2f}%")
            self.logger.info(f"   🎯 Biomarkers extracted: {len(biomarkers)}")
            self.logger.info(f"   📈 Average confidence: {avg_confidence:.3f}")
            self.logger.info(f"   ⏱️  Processing time: {time.time() - mode_start_time:.2f}s")
            
            return mode_results
            
        except Exception as e:
            self.logger.error(f"❌ {mode.upper()} mode failed: {e}")
            return {"error": str(e)}
        finally:
            self._clear_mode_environment()
    
    def _set_mode_environment(self, mode: str):
        """Set environment variables for the specified mode."""
        # Clear existing mode variables
        for var in ["ACCURACY_MODE", "BALANCED_MODE"]:
            if var in os.environ:
                del os.environ[var]
        
        # Set mode-specific variables
        if mode == "accuracy":
            os.environ["ACCURACY_MODE"] = "true"
        elif mode == "balanced":
            os.environ["BALANCED_MODE"] = "true"
        # Legacy mode uses default (no special env vars)
    
    def _clear_mode_environment(self):
        """Clear optimization mode environment variables."""
        for var in ["ACCURACY_MODE", "BALANCED_MODE"]:
            if var in os.environ:
                del os.environ[var]
    
    def _calculate_mode_comparison(self, modes_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comparative metrics between different modes."""
        comparison = {
            "best_token_reduction": {"mode": None, "reduction": 0},
            "best_accuracy": {"mode": None, "confidence": 0},
            "fastest_processing": {"mode": None, "time": float('inf')},
            "most_biomarkers": {"mode": None, "count": 0}
        }
        
        for mode, results in modes_results.items():
            if "error" in results:
                continue
                
            # Check token reduction
            token_reduction = results["token_metrics"]["token_reduction_percent"]
            if token_reduction > comparison["best_token_reduction"]["reduction"]:
                comparison["best_token_reduction"] = {"mode": mode, "reduction": token_reduction}
            
            # Check accuracy
            avg_confidence = results["biomarker_metrics"]["average_confidence"]
            if avg_confidence > comparison["best_accuracy"]["confidence"]:
                comparison["best_accuracy"] = {"mode": mode, "confidence": avg_confidence}
            
            # Check processing time
            processing_time = results["processing_time"]
            if processing_time < comparison["fastest_processing"]["time"]:
                comparison["fastest_processing"] = {"mode": mode, "time": processing_time}
            
            # Check biomarker count
            biomarker_count = results["biomarker_metrics"]["biomarkers_extracted"]
            if biomarker_count > comparison["most_biomarkers"]["count"]:
                comparison["most_biomarkers"] = {"mode": mode, "count": biomarker_count}
        
        return comparison
    
    def benchmark_lab_formats(self, sample_reports_dir: str) -> Dict[str, Any]:
        """
        Benchmark optimization across multiple lab report formats.
        
        Args:
            sample_reports_dir: Directory containing sample lab reports
            
        Returns:
            Benchmark results across all formats
        """
        self.logger.info(f"🏆 Starting lab format benchmark from: {sample_reports_dir}")
        
        if not os.path.exists(sample_reports_dir):
            raise FileNotFoundError(f"Sample reports directory not found: {sample_reports_dir}")
        
        benchmark_results = {
            "benchmark_timestamp": datetime.now().isoformat(),
            "sample_reports_dir": sample_reports_dir,
            "lab_formats": {}
        }
        
        # Find all PDF files in the directory
        pdf_files = list(Path(sample_reports_dir).glob("*.pdf"))
        
        if not pdf_files:
            self.logger.warning("⚠️  No PDF files found in sample reports directory")
            return benchmark_results
        
        self.logger.info(f"📋 Found {len(pdf_files)} lab reports to benchmark")
        
        for pdf_file in pdf_files:
            lab_name = pdf_file.stem  # Use filename without extension as lab identifier
            self.logger.info(f"\n🧪 Benchmarking {lab_name}...")
            
            try:
                lab_results = self.test_pdf_optimization(str(pdf_file), mode="all")
                benchmark_results["lab_formats"][lab_name] = lab_results
                
                # Log summary for this lab
                if "modes_tested" in lab_results:
                    balanced_results = lab_results["modes_tested"].get("balanced", {})
                    if "token_metrics" in balanced_results:
                        reduction = balanced_results["token_metrics"]["token_reduction_percent"]
                        self.logger.info(f"   💰 {lab_name}: {reduction:.1f}% token reduction")
                
            except Exception as e:
                self.logger.error(f"❌ Failed to benchmark {lab_name}: {e}")
                benchmark_results["lab_formats"][lab_name] = {"error": str(e)}
        
        # Calculate overall benchmark statistics
        benchmark_results["overall_stats"] = self._calculate_benchmark_stats(benchmark_results["lab_formats"])
        
        return benchmark_results
    
    def _calculate_benchmark_stats(self, lab_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall statistics from benchmark results."""
        stats = {
            "total_labs_tested": len(lab_results),
            "successful_tests": 0,
            "failed_tests": 0,
            "average_token_reduction": 0,
            "average_accuracy": 0,
            "best_performing_lab": None,
            "worst_performing_lab": None
        }
        
        reductions = []
        accuracies = []
        
        for lab_name, results in lab_results.items():
            if "error" in results:
                stats["failed_tests"] += 1
                continue
                
            stats["successful_tests"] += 1
            
            # Get balanced mode results for comparison
            balanced_results = results.get("modes_tested", {}).get("balanced", {})
            if "token_metrics" in balanced_results:
                reduction = balanced_results["token_metrics"]["token_reduction_percent"]
                reductions.append(reduction)
                
                if stats["best_performing_lab"] is None or reduction > reductions[0]:
                    stats["best_performing_lab"] = {"lab": lab_name, "reduction": reduction}
                
                if stats["worst_performing_lab"] is None or reduction < reductions[-1]:
                    stats["worst_performing_lab"] = {"lab": lab_name, "reduction": reduction}
            
            if "biomarker_metrics" in balanced_results:
                accuracy = balanced_results["biomarker_metrics"]["average_confidence"]
                accuracies.append(accuracy)
        
        if reductions:
            stats["average_token_reduction"] = sum(reductions) / len(reductions)
        if accuracies:
            stats["average_accuracy"] = sum(accuracies) / len(accuracies)
        
        return stats
    
    def save_results(self, results: Dict[str, Any], output_file: Optional[str] = None):
        """Save test results to JSON file."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"lab_optimization_results_{timestamp}.json"
        
        os.makedirs("logs", exist_ok=True)
        output_path = os.path.join("logs", output_file)
        
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        self.logger.info(f"💾 Results saved to: {output_path}")
        return output_path


def main():
    """Main CLI interface for the lab optimization tester."""
    parser = argparse.ArgumentParser(
        description="Lab Optimization Tester - Test chunking, accuracy, and token optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--pdf", 
        type=str, 
        help="Path to PDF file to test"
    )
    
    parser.add_argument(
        "--mode", 
        choices=["legacy", "accuracy", "balanced", "all"],
        default="all",
        help="Optimization mode to test (default: all)"
    )
    
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run benchmark across multiple lab formats"
    )
    
    parser.add_argument(
        "--sample-dir",
        type=str,
        default="sample_reports",
        help="Directory containing sample lab reports for benchmarking"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        help="Output file for results (default: auto-generated)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Initialize tester
    tester = LabOptimizationTester(debug_mode=args.debug)
    
    try:
        if args.benchmark:
            # Run benchmark across multiple lab formats
            results = tester.benchmark_lab_formats(args.sample_dir)
            print(f"\n🏆 Benchmark Results Summary:")
            print(f"   📊 Labs tested: {results['overall_stats']['total_labs_tested']}")
            print(f"   ✅ Successful: {results['overall_stats']['successful_tests']}")
            print(f"   ❌ Failed: {results['overall_stats']['failed_tests']}")
            print(f"   💰 Avg token reduction: {results['overall_stats']['average_token_reduction']:.1f}%")
            print(f"   🎯 Avg accuracy: {results['overall_stats']['average_accuracy']:.3f}")
            
        elif args.pdf:
            # Test single PDF
            results = tester.test_pdf_optimization(args.pdf, args.mode)
            print(f"\n📋 Test Results Summary:")
            if "modes_tested" in results:
                for mode, mode_results in results["modes_tested"].items():
                    if "error" not in mode_results:
                        print(f"   {mode.upper()}:")
                        print(f"     💰 Token reduction: {mode_results['token_metrics']['token_reduction_percent']:.2f}%")
                        print(f"     🎯 Biomarkers: {mode_results['biomarker_metrics']['biomarkers_extracted']}")
                        print(f"     📈 Avg confidence: {mode_results['biomarker_metrics']['average_confidence']:.3f}")
            
        else:
            parser.print_help()
            return
        
        # Save results
        output_file = tester.save_results(results, args.output)
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main()) 