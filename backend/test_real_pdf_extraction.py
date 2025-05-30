#!/usr/bin/env python3
"""
Real PDF Biomarker Extraction Test Script

This script processes real PDF files through the complete biomarker extraction pipeline
and generates comprehensive statistics reports including:
- Token usage and optimization metrics
- Biomarker extraction results with confidence scores
- Smart chunk skipping statistics
- Biomarker caching performance
- Page filtering and processing details

Usage:
    python test_real_pdf_extraction.py path/to/your/pdf_file.pdf [--output-dir results]
"""

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import extraction pipeline components
from app.services.pdf_service import (
    extract_text_from_pdf,
    filter_relevant_pages,
    process_pages_sequentially
)
from app.services.document_analyzer import (
    analyze_document_structure,
    DocumentStructure
)
from app.services.utils.metrics import TokenUsageMetrics, ExtractionPerformanceTracker
from app.services.utils.biomarker_cache import get_biomarker_cache
from app.core.config import DOCUMENT_ANALYZER_CONFIG


class PDFExtractionTester:
    """Comprehensive PDF extraction tester with detailed reporting."""
    
    def __init__(self, pdf_path: str, output_dir: str = "extraction_results"):
        """
        Initialize the PDF extraction tester.
        
        Args:
            pdf_path: Path to the PDF file to test
            output_dir: Directory to save results
        """
        self.pdf_path = pdf_path
        self.pdf_name = Path(pdf_path).stem
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create unique run ID
        self.run_id = f"{self.pdf_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize metrics trackers
        self.metrics = TokenUsageMetrics(
            document_id=self.run_id,
            save_debug=True,
            debug_dir=str(self.output_dir)
        )
        self.performance_tracker = ExtractionPerformanceTracker(document_id=self.run_id)
        
        # Results storage
        self.results = {
            "pdf_info": {
                "file_path": pdf_path,
                "file_name": self.pdf_name,
                "file_size_mb": 0,
                "run_id": self.run_id,
                "timestamp": datetime.now().isoformat()
            },
            "extraction_results": {
                "biomarkers": [],
                "total_biomarkers": 0,
                "pages_processed": 0,
                "total_pages": 0
            },
            "performance_metrics": {},
            "cache_performance": {},
            "smart_skipping": {},
            "page_filtering": {},
            "document_structure": {},
            "processing_time": {}
        }
        
        # Setup logging
        self.setup_logging()
    
    def setup_logging(self):
        """Setup detailed logging for the test."""
        log_file = self.output_dir / f"{self.run_id}_extraction.log"
        
        # Create logger
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create file handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logging.info(f"🔬 Starting PDF extraction test for: {self.pdf_path}")
        logging.info(f"📊 Results will be saved to: {self.output_dir}")
        logging.info(f"🆔 Run ID: {self.run_id}")
    
    async def run_complete_extraction(self) -> Dict[str, Any]:
        """
        Run the complete biomarker extraction pipeline.
        
        Returns:
            Dictionary with comprehensive test results
        """
        start_time = time.time()
        
        try:
            # Step 1: Basic PDF information
            await self._collect_pdf_info()
            
            # Step 2: Extract text from PDF
            logging.info("📄 Extracting text from PDF...")
            text_start = time.time()
            pages_text_dict = extract_text_from_pdf(self.pdf_path)
            text_time = time.time() - text_start
            
            self.results["processing_time"]["text_extraction"] = text_time
            self.results["extraction_results"]["total_pages"] = len(pages_text_dict)
            
            logging.info(f"✅ Text extraction complete: {len(pages_text_dict)} pages in {text_time:.2f}s")
            
            # Step 3: Analyze document structure
            logging.info("🔍 Analyzing document structure...")
            structure_start = time.time()
            document_structure = None
            
            if DOCUMENT_ANALYZER_CONFIG["enabled"] and DOCUMENT_ANALYZER_CONFIG["structure_analysis"]["enabled"]:
                document_structure = analyze_document_structure(self.pdf_path, pages_text_dict)
                self.results["document_structure"] = {
                    "confidence": document_structure.get("confidence", 0),
                    "document_type": document_structure.get("document_type", "unknown"),
                    "tables_found": len(document_structure.get("tables", {})),
                    "biomarker_regions": len(document_structure.get("biomarker_regions", []))
                }
            
            structure_time = time.time() - structure_start
            self.results["processing_time"]["structure_analysis"] = structure_time
            
            logging.info(f"✅ Structure analysis complete in {structure_time:.2f}s")
            
            # Step 4: Filter relevant pages
            logging.info("🎯 Filtering relevant pages...")
            filter_start = time.time()
            relevant_pages = filter_relevant_pages(pages_text_dict, document_structure)
            filter_time = time.time() - filter_start
            
            self.results["page_filtering"] = {
                "total_pages": len(pages_text_dict),
                "relevant_pages": len(relevant_pages),
                "filtered_out": len(pages_text_dict) - len(relevant_pages),
                "filter_efficiency": (len(pages_text_dict) - len(relevant_pages)) / len(pages_text_dict) * 100,
                "relevant_page_numbers": list(relevant_pages.keys())
            }
            self.results["processing_time"]["page_filtering"] = filter_time
            
            logging.info(f"✅ Page filtering complete: {len(relevant_pages)}/{len(pages_text_dict)} pages relevant ({filter_time:.2f}s)")
            
            # Step 5: Process pages and extract biomarkers
            logging.info("🧬 Extracting biomarkers...")
            extraction_start = time.time()
            
            # Clear cache statistics to get accurate measurements
            cache = get_biomarker_cache()
            initial_cache_stats = cache.get_cache_statistics()
            
            extracted_biomarkers = await process_pages_sequentially(
                relevant_pages,
                document_structure=document_structure
            )
            
            extraction_time = time.time() - extraction_start
            self.results["processing_time"]["biomarker_extraction"] = extraction_time
            
            # Record extraction results
            self.results["extraction_results"]["biomarkers"] = extracted_biomarkers
            self.results["extraction_results"]["total_biomarkers"] = len(extracted_biomarkers)
            self.results["extraction_results"]["pages_processed"] = len(relevant_pages)
            
            logging.info(f"✅ Biomarker extraction complete: {len(extracted_biomarkers)} biomarkers in {extraction_time:.2f}s")
            
            # Step 6: Collect performance metrics
            await self._collect_performance_metrics(initial_cache_stats)
            
            # Step 7: Calculate total time
            total_time = time.time() - start_time
            self.results["processing_time"]["total"] = total_time
            
            logging.info(f"🎉 Complete extraction finished in {total_time:.2f}s")
            
            # Step 8: Generate reports
            await self._generate_reports()
            
            return self.results
            
        except Exception as e:
            logging.error(f"❌ Error during extraction: {e}", exc_info=True)
            self.results["error"] = str(e)
            return self.results
    
    async def _collect_pdf_info(self):
        """Collect basic PDF information."""
        try:
            file_size = os.path.getsize(self.pdf_path)
            self.results["pdf_info"]["file_size_mb"] = file_size / (1024 * 1024)
            
            logging.info(f"📋 PDF Info: {self.pdf_name} ({file_size / (1024 * 1024):.2f} MB)")
        except Exception as e:
            logging.warning(f"Could not collect PDF info: {e}")
    
    async def _collect_performance_metrics(self, initial_cache_stats: Dict[str, Any]):
        """Collect comprehensive performance metrics."""
        # Token usage metrics
        token_summary = self.metrics.get_summary()
        self.results["performance_metrics"] = token_summary
        
        # Cache performance
        final_cache_stats = get_biomarker_cache().get_cache_statistics()
        cache_performance = {
            "initial_stats": initial_cache_stats,
            "final_stats": final_cache_stats,
            "cache_improvement": {
                "hits_gained": final_cache_stats.get("cache_hits", 0) - initial_cache_stats.get("cache_hits", 0),
                "extractions_gained": final_cache_stats.get("total_extractions", 0) - initial_cache_stats.get("total_extractions", 0),
                "hit_rate_change": final_cache_stats.get("cache_hit_rate", 0) - initial_cache_stats.get("cache_hit_rate", 0)
            }
        }
        self.results["cache_performance"] = cache_performance
        
        # Smart skipping metrics (from token metrics)
        if "smart_skipping_metrics" in token_summary:
            self.results["smart_skipping"] = token_summary["smart_skipping_metrics"]
        
        # Record individual biomarker performance
        for biomarker in self.results["extraction_results"]["biomarkers"]:
            self.performance_tracker.record_biomarker(
                biomarker=biomarker,
                is_valid=True,  # Assume valid for this test
                confidence=biomarker.get("confidence", 0.0)
            )
        
        # Get performance summary
        perf_summary = self.performance_tracker.get_performance_metrics()
        self.results["extraction_accuracy"] = perf_summary
    
    async def _generate_reports(self):
        """Generate comprehensive reports in multiple formats."""
        # 1. Save complete JSON results
        json_file = self.output_dir / f"{self.run_id}_complete_results.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        logging.info(f"💾 Complete results saved to: {json_file}")
        
        # 2. Generate human-readable summary
        await self._generate_summary_report()
        
        # 3. Generate biomarkers table
        await self._generate_biomarkers_table()
        
        # 4. Generate performance dashboard
        await self._generate_performance_dashboard()
        
        # 5. Save detailed metrics report
        self.metrics.save_detailed_report()
    
    async def _generate_summary_report(self):
        """Generate a human-readable summary report."""
        summary_file = self.output_dir / f"{self.run_id}_summary.txt"
        
        with open(summary_file, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write(f"BIOMARKER EXTRACTION TEST REPORT\n")
            f.write(f"Run ID: {self.run_id}\n")
            f.write(f"PDF: {self.pdf_name}\n")
            f.write(f"Timestamp: {self.results['pdf_info']['timestamp']}\n")
            f.write("=" * 80 + "\n\n")
            
            # PDF Information
            f.write("📋 PDF INFORMATION\n")
            f.write("-" * 40 + "\n")
            f.write(f"File Size: {self.results['pdf_info']['file_size_mb']:.2f} MB\n")
            f.write(f"Total Pages: {self.results['extraction_results']['total_pages']}\n")
            f.write(f"Relevant Pages: {self.results['page_filtering']['relevant_pages']}\n")
            f.write(f"Pages Filtered Out: {self.results['page_filtering']['filtered_out']}\n")
            f.write(f"Filter Efficiency: {self.results['page_filtering']['filter_efficiency']:.1f}%\n\n")
            
            # Extraction Results
            f.write("🧬 EXTRACTION RESULTS\n")
            f.write("-" * 40 + "\n")
            f.write(f"Total Biomarkers Extracted: {self.results['extraction_results']['total_biomarkers']}\n")
            f.write(f"Pages Processed: {self.results['extraction_results']['pages_processed']}\n")
            
            if self.results['extraction_results']['biomarkers']:
                avg_confidence = sum(b.get('confidence', 0) for b in self.results['extraction_results']['biomarkers'])
                avg_confidence /= len(self.results['extraction_results']['biomarkers'])
                f.write(f"Average Confidence: {avg_confidence:.3f}\n")
                
                high_conf_count = sum(1 for b in self.results['extraction_results']['biomarkers'] if b.get('confidence', 0) >= 0.8)
                f.write(f"High Confidence (≥0.8): {high_conf_count}/{len(self.results['extraction_results']['biomarkers'])}\n")
            
            f.write("\n")
            
            # Performance Metrics
            if "performance_metrics" in self.results:
                perf = self.results["performance_metrics"]
                f.write("📊 PERFORMANCE METRICS\n")
                f.write("-" * 40 + "\n")
                
                if "token_metrics" in perf:
                    token = perf["token_metrics"]
                    f.write(f"Original Tokens: {token['original_tokens']:,}\n")
                    f.write(f"Optimized Tokens: {token['optimized_tokens']:,}\n")
                    f.write(f"Token Reduction: {token['token_reduction_percentage']:.1f}%\n")
                    f.write(f"Estimated Cost Savings: ${token['estimated_cost_savings']:.3f}\n")
                
                if "api_metrics" in perf:
                    api = perf["api_metrics"]
                    f.write(f"API Calls Made: {api['api_calls']}\n")
                    f.write(f"Total Tokens Used: {api['total_tokens_used']:,}\n")
                    f.write(f"Average Tokens per Call: {api['avg_tokens_per_call']:.1f}\n")
                
                f.write("\n")
            
            # Smart Skipping Results
            if "smart_skipping" in self.results and self.results["smart_skipping"].get("enabled"):
                skipping = self.results["smart_skipping"]
                f.write("⏭️  SMART CHUNK SKIPPING\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total Chunks: {skipping.get('total_chunks', 0)}\n")
                f.write(f"Chunks Skipped: {skipping.get('skipped', 0)}\n")
                f.write(f"Chunks Processed: {skipping.get('processed', 0)}\n")
                f.write(f"Tokens Saved: {skipping.get('tokens_saved', 0):,}\n")
                f.write(f"Skip Rate: {(skipping.get('skipped', 0) / max(1, skipping.get('total_chunks', 1))) * 100:.1f}%\n\n")
            
            # Cache Performance
            if "cache_performance" in self.results:
                cache = self.results["cache_performance"]
                f.write("🧠 BIOMARKER CACHE PERFORMANCE\n")
                f.write("-" * 40 + "\n")
                
                final_stats = cache.get("final_stats", {})
                f.write(f"Cache Hits: {final_stats.get('cache_hits', 0)}\n")
                f.write(f"Cache Misses: {final_stats.get('cache_misses', 0)}\n")
                f.write(f"Cache Hit Rate: {final_stats.get('cache_hit_rate', 0) * 100:.1f}%\n")
                f.write(f"LLM Calls Saved: {final_stats.get('llm_calls_saved', 0)}\n")
                
                improvement = cache.get("cache_improvement", {})
                f.write(f"New Cache Hits: {improvement.get('hits_gained', 0)}\n")
                f.write("\n")
            
            # Processing Times
            f.write("⏱️  PROCESSING TIMES\n")
            f.write("-" * 40 + "\n")
            times = self.results.get("processing_time", {})
            f.write(f"Text Extraction: {times.get('text_extraction', 0):.2f}s\n")
            f.write(f"Structure Analysis: {times.get('structure_analysis', 0):.2f}s\n")
            f.write(f"Page Filtering: {times.get('page_filtering', 0):.2f}s\n")
            f.write(f"Biomarker Extraction: {times.get('biomarker_extraction', 0):.2f}s\n")
            f.write(f"Total Time: {times.get('total', 0):.2f}s\n")
        
        logging.info(f"📝 Summary report saved to: {summary_file}")
    
    async def _generate_biomarkers_table(self):
        """Generate a detailed biomarkers table."""
        table_file = self.output_dir / f"{self.run_id}_biomarkers_table.html"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Biomarkers Extraction Results - {self.pdf_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .high-conf {{ background-color: #d4edda; }}
                .med-conf {{ background-color: #fff3cd; }}
                .low-conf {{ background-color: #f8d7da; }}
                .abnormal {{ font-weight: bold; color: #dc3545; }}
                .normal {{ color: #28a745; }}
            </style>
        </head>
        <body>
            <h1>Biomarker Extraction Results</h1>
            <h2>PDF: {self.pdf_name}</h2>
            <h3>Run ID: {self.run_id}</h3>
            <p>Total Biomarkers: {len(self.results['extraction_results']['biomarkers'])}</p>
            
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Value</th>
                        <th>Unit</th>
                        <th>Reference Range</th>
                        <th>Abnormal</th>
                        <th>Confidence</th>
                        <th>Category</th>
                        <th>Page</th>
                        <th>Method</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for biomarker in self.results['extraction_results']['biomarkers']:
            confidence = biomarker.get('confidence', 0)
            conf_class = "high-conf" if confidence >= 0.8 else "med-conf" if confidence >= 0.6 else "low-conf"
            abnormal_class = "abnormal" if biomarker.get('is_abnormal') else "normal"
            
            ref_range = ""
            if biomarker.get('reference_range_low') is not None and biomarker.get('reference_range_high') is not None:
                ref_range = f"{biomarker['reference_range_low']}-{biomarker['reference_range_high']}"
            elif biomarker.get('reference_range_text'):
                ref_range = biomarker['reference_range_text']
            
            html_content += f"""
                    <tr class="{conf_class}">
                        <td>{biomarker.get('name', 'Unknown')}</td>
                        <td>{biomarker.get('value', 'N/A')}</td>
                        <td>{biomarker.get('unit', 'N/A')}</td>
                        <td>{ref_range}</td>
                        <td class="{abnormal_class}">{'Yes' if biomarker.get('is_abnormal') else 'No'}</td>
                        <td>{confidence:.3f}</td>
                        <td>{biomarker.get('category', 'Other')}</td>
                        <td>{biomarker.get('page', 'N/A')}</td>
                        <td>{biomarker.get('extraction_method', 'llm')}</td>
                    </tr>
            """
        
        html_content += """
                </tbody>
            </table>
            
            <h3>Legend</h3>
            <p>
                <span class="high-conf">■</span> High Confidence (≥0.8) &nbsp;&nbsp;
                <span class="med-conf">■</span> Medium Confidence (0.6-0.8) &nbsp;&nbsp;
                <span class="low-conf">■</span> Low Confidence (<0.6)
            </p>
        </body>
        </html>
        """
        
        with open(table_file, 'w') as f:
            f.write(html_content)
        
        logging.info(f"🔬 Biomarkers table saved to: {table_file}")
    
    async def _generate_performance_dashboard(self):
        """Generate a performance dashboard."""
        dashboard_file = self.output_dir / f"{self.run_id}_performance_dashboard.html"
        
        # Prepare data for charts
        perf = self.results.get("performance_metrics", {})
        token_metrics = perf.get("token_metrics", {})
        api_metrics = perf.get("api_metrics", {})
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Performance Dashboard - {self.pdf_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .metric-card {{ 
                    border: 1px solid #ddd; 
                    border-radius: 8px; 
                    padding: 15px; 
                    margin: 10px; 
                    display: inline-block; 
                    min-width: 200px;
                    background: #f9f9f9;
                }}
                .metric-title {{ font-weight: bold; color: #333; }}
                .metric-value {{ font-size: 24px; color: #007bff; }}
                .metric-unit {{ font-size: 14px; color: #666; }}
                .dashboard-section {{ margin: 20px 0; }}
                .success {{ color: #28a745; }}
                .warning {{ color: #ffc107; }}
                .danger {{ color: #dc3545; }}
                table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <h1>Performance Dashboard</h1>
            <h2>PDF: {self.pdf_name}</h2>
            <p>Run ID: {self.run_id} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            
            <div class="dashboard-section">
                <h3>📊 Key Metrics</h3>
                
                <div class="metric-card">
                    <div class="metric-title">Biomarkers Extracted</div>
                    <div class="metric-value">{self.results['extraction_results']['total_biomarkers']}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Token Reduction</div>
                    <div class="metric-value success">{token_metrics.get('token_reduction_percentage', 0):.1f}%</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">API Calls</div>
                    <div class="metric-value">{api_metrics.get('api_calls', 0)}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Cost Savings</div>
                    <div class="metric-value success">${token_metrics.get('estimated_cost_savings', 0):.3f}</div>
                </div>
                
                <div class="metric-card">
                    <div class="metric-title">Processing Time</div>
                    <div class="metric-value">{self.results.get('processing_time', {}).get('total', 0):.1f}s</div>
                </div>
            </div>
            
            <div class="dashboard-section">
                <h3>📄 Page Processing</h3>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Details</th>
                    </tr>
                    <tr>
                        <td>Total Pages</td>
                        <td>{self.results['page_filtering']['total_pages']}</td>
                        <td>Pages in PDF</td>
                    </tr>
                    <tr>
                        <td>Relevant Pages</td>
                        <td>{self.results['page_filtering']['relevant_pages']}</td>
                        <td>Pages with biomarker content</td>
                    </tr>
                    <tr>
                        <td>Filtered Out</td>
                        <td>{self.results['page_filtering']['filtered_out']}</td>
                        <td>Pages skipped</td>
                    </tr>
                    <tr>
                        <td>Filter Efficiency</td>
                        <td>{self.results['page_filtering']['filter_efficiency']:.1f}%</td>
                        <td>Percentage of pages filtered</td>
                    </tr>
                </table>
            </div>
        """
        
        # Add smart skipping section if enabled
        if "smart_skipping" in self.results and self.results["smart_skipping"].get("enabled"):
            skipping = self.results["smart_skipping"]
            html_content += f"""
            <div class="dashboard-section">
                <h3>⏭️ Smart Chunk Skipping</h3>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Impact</th>
                    </tr>
                    <tr>
                        <td>Total Chunks</td>
                        <td>{skipping.get('total_chunks', 0)}</td>
                        <td>Content segments created</td>
                    </tr>
                    <tr>
                        <td>Chunks Skipped</td>
                        <td>{skipping.get('skipped', 0)}</td>
                        <td>Segments with low biomarker potential</td>
                    </tr>
                    <tr>
                        <td>Skip Rate</td>
                        <td>{(skipping.get('skipped', 0) / max(1, skipping.get('total_chunks', 1))) * 100:.1f}%</td>
                        <td>Efficiency of skipping</td>
                    </tr>
                    <tr>
                        <td>Tokens Saved</td>
                        <td class="success">{skipping.get('tokens_saved', 0):,}</td>
                        <td>API tokens not used</td>
                    </tr>
                </table>
            </div>
            """
        
        # Add cache performance if enabled
        if "cache_performance" in self.results:
            cache = self.results["cache_performance"]["final_stats"]
            html_content += f"""
            <div class="dashboard-section">
                <h3>🧠 Biomarker Cache Performance</h3>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                        <th>Impact</th>
                    </tr>
                    <tr>
                        <td>Cache Hits</td>
                        <td class="success">{cache.get('cache_hits', 0)}</td>
                        <td>Biomarkers found without LLM</td>
                    </tr>
                    <tr>
                        <td>Cache Misses</td>
                        <td>{cache.get('cache_misses', 0)}</td>
                        <td>Required LLM processing</td>
                    </tr>
                    <tr>
                        <td>Hit Rate</td>
                        <td class="{'success' if cache.get('cache_hit_rate', 0) > 0.5 else 'warning'}">{cache.get('cache_hit_rate', 0) * 100:.1f}%</td>
                        <td>Cache effectiveness</td>
                    </tr>
                    <tr>
                        <td>LLM Calls Saved</td>
                        <td class="success">{cache.get('llm_calls_saved', 0)}</td>
                        <td>API calls avoided</td>
                    </tr>
                </table>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        with open(dashboard_file, 'w') as f:
            f.write(html_content)
        
        logging.info(f"📈 Performance dashboard saved to: {dashboard_file}")


async def main():
    """Main function to run the PDF extraction test."""
    parser = argparse.ArgumentParser(description="Test biomarker extraction on real PDF files")
    parser.add_argument("pdf_path", help="Path to the PDF file to test")
    parser.add_argument("--output-dir", default="extraction_results", 
                       help="Directory to save results (default: extraction_results)")
    parser.add_argument("--config", help="Optional configuration file")
    
    args = parser.parse_args()
    
    # Validate PDF file exists
    if not os.path.exists(args.pdf_path):
        print(f"❌ Error: PDF file not found: {args.pdf_path}")
        sys.exit(1)
    
    # Set environment variables for optimization features
    os.environ["DEBUG_TOKEN_METRICS"] = "1"
    
    # Create tester and run extraction
    tester = PDFExtractionTester(args.pdf_path, args.output_dir)
    
    try:
        results = await tester.run_complete_extraction()
        
        # Print summary to console
        print("\n" + "=" * 80)
        print("🎉 EXTRACTION TEST COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print(f"📄 PDF: {Path(args.pdf_path).name}")
        print(f"🧬 Biomarkers Extracted: {results['extraction_results']['total_biomarkers']}")
        print(f"📊 Token Reduction: {results.get('performance_metrics', {}).get('token_metrics', {}).get('token_reduction_percentage', 0):.1f}%")
        print(f"💰 Cost Savings: ${results.get('performance_metrics', {}).get('token_metrics', {}).get('estimated_cost_savings', 0):.3f}")
        print(f"⏱️  Total Time: {results.get('processing_time', {}).get('total', 0):.2f}s")
        print(f"📁 Results saved to: {args.output_dir}")
        print("=" * 80)
        
        # List generated files
        output_path = Path(args.output_dir)
        generated_files = list(output_path.glob(f"{tester.run_id}*"))
        if generated_files:
            print("\n📂 Generated Files:")
            for file in generated_files:
                print(f"   • {file.name}")
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        logging.error("Test failed", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 