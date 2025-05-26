import pytest
import sys
import os
import json
import tempfile
from datetime import datetime
from typing import Dict, List, Any
import re

# Add the parent directory to the Python path to make imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.services.utils.metrics import TokenUsageMetrics, ExtractionPerformanceTracker


class TestTokenUsageMetrics:
    """Test the token usage metrics functionality."""

    @pytest.fixture
    def token_metrics(self):
        """Create a TokenUsageMetrics instance for testing."""
        # Use a temporary directory for debug files
        with tempfile.TemporaryDirectory() as tmpdir:
            metrics = TokenUsageMetrics(
                document_id="test_doc",
                save_debug=True,
                debug_dir=tmpdir
            )
            yield metrics

    def test_record_original_text(self, token_metrics):
        """Test recording original text."""
        # Record some text
        tokens = token_metrics.record_original_text("This is a test", page_num=1)
        
        # Check token count is reasonable
        assert tokens > 0
        
        # Check running total
        assert token_metrics.original_tokens == tokens
        
        # Add another page
        token_metrics.record_original_text("This is another test", page_num=2)
        
        # Check running total increases
        assert token_metrics.original_tokens > tokens
        
        # Check chunk details are recorded
        assert len(token_metrics.chunk_details) == 2
        assert token_metrics.chunk_details[0]["type"] == "original"
        assert token_metrics.chunk_details[0]["page_num"] == 1

    def test_record_optimized_text(self, token_metrics):
        """Test recording optimized text."""
        # Record optimized text
        chunk_info = {
            "page_num": 1,
            "region_type": "table",
            "biomarker_confidence": 0.9
        }
        tokens = token_metrics.record_optimized_text("This is optimized", chunk_info)
        
        # Check token count is reasonable
        assert tokens > 0
        
        # Check running total
        assert token_metrics.optimized_tokens == tokens
        
        # Check chunk details are recorded
        assert len(token_metrics.chunk_details) == 1
        assert token_metrics.chunk_details[0]["type"] == "optimized"
        assert token_metrics.chunk_details[0]["page_num"] == 1
        assert token_metrics.chunk_details[0]["region_type"] == "table"

    def test_record_api_call(self, token_metrics):
        """Test recording API calls."""
        # Record an API call
        chunk_info = {
            "page_num": 1,
            "region_type": "table"
        }
        token_metrics.record_api_call(
            prompt_tokens=100,
            completion_tokens=50,
            chunk_info=chunk_info,
            biomarkers_found=5
        )
        
        # Check API call is recorded
        assert token_metrics.api_calls == 1
        assert len(token_metrics.call_details) == 1
        assert token_metrics.call_details[0]["prompt_tokens"] == 100
        assert token_metrics.call_details[0]["completion_tokens"] == 50
        assert token_metrics.call_details[0]["total_tokens"] == 150
        assert token_metrics.call_details[0]["biomarkers_found"] == 5
        assert token_metrics.biomarkers_extracted == 5
        
        # Record another API call
        token_metrics.record_api_call(
            prompt_tokens=200,
            completion_tokens=100,
            chunk_info={"page_num": 2, "region_type": "content"},
            biomarkers_found=10
        )
        
        # Check totals are updated
        assert token_metrics.api_calls == 2
        assert token_metrics.biomarkers_extracted == 15
        assert len(token_metrics.call_details) == 2

    def test_optimization_completion_tracking(self, token_metrics):
        """Test tracking optimization completion."""
        # Record optimization completion
        token_metrics.record_optimization_complete(
            optimization_time=1.5,
            chunk_count=5
        )
        
        # Check metrics are recorded
        assert token_metrics.optimization_time == 1.5
        assert token_metrics.chunks_processed == 5

    def test_extraction_completion_tracking(self, token_metrics):
        """Test tracking extraction completion."""
        # Record extraction completion
        token_metrics.record_extraction_complete(
            extraction_time=2.5,
            pages_processed=3,
            biomarkers_extracted=15
        )
        
        # Check metrics are recorded
        assert token_metrics.extraction_time == 2.5
        assert token_metrics.pages_processed == 3
        assert token_metrics.biomarkers_extracted == 15

    def test_get_summary(self, token_metrics):
        """Test generating a summary of metrics."""
        # Record some data
        token_metrics.record_original_text("Original text", page_num=1)
        token_metrics.record_optimized_text("Optimized", {"page_num": 1, "region_type": "table"})
        token_metrics.record_api_call(100, 50, {"page_num": 1, "region_type": "table"}, 5)
        token_metrics.record_optimization_complete(1.0, 1)
        token_metrics.record_extraction_complete(2.0, 1, 5)
        
        # Get summary
        summary = token_metrics.get_summary()
        
        # Check summary structure and values
        assert "token_metrics" in summary
        assert "api_metrics" in summary
        assert "performance_metrics" in summary
        
        # Check token metrics
        token_metrics_data = summary["token_metrics"]
        assert token_metrics_data["original_tokens"] > 0
        assert token_metrics_data["optimized_tokens"] > 0
        assert token_metrics_data["token_reduction_percentage"] >= 0
        
        # Check API metrics
        api_metrics_data = summary["api_metrics"]
        assert api_metrics_data["api_calls"] == 1
        assert api_metrics_data["prompt_tokens"] == 100
        assert api_metrics_data["completion_tokens"] == 50
        
        # Check performance metrics
        perf_metrics_data = summary["performance_metrics"]
        assert perf_metrics_data["biomarkers_extracted"] == 5
        assert perf_metrics_data["pages_processed"] == 1
        assert perf_metrics_data["optimization_time_seconds"] == 1.0
        assert perf_metrics_data["extraction_time_seconds"] == 2.0

    def test_save_detailed_report(self, token_metrics):
        """Test saving a detailed report."""
        # Record some data
        token_metrics.record_original_text("Original text", page_num=1)
        token_metrics.record_optimized_text("Optimized", {"page_num": 1, "region_type": "table"})
        token_metrics.record_api_call(100, 50, {"page_num": 1, "region_type": "table"}, 5)
        
        # Generate a filename in the temp directory
        filename = f"test_report_{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
        
        # Save the report
        token_metrics.save_detailed_report(filename)
        
        # Check file exists in debug directory
        report_path = os.path.join(token_metrics.debug_dir, filename)
        assert os.path.exists(report_path)
        
        # Load and verify the report
        with open(report_path, "r") as f:
            report = json.load(f)
        
        # Check report structure
        assert "token_metrics" in report
        assert "call_details" in report
        assert "chunk_details" in report
        assert len(report["call_details"]) == 1
        assert len(report["chunk_details"]) == 2


class TestExtractionPerformanceTracker:
    """Test the extraction performance tracker functionality."""

    @pytest.fixture
    def performance_tracker(self):
        """Create an ExtractionPerformanceTracker instance for testing."""
        return ExtractionPerformanceTracker(document_id="test_doc")
    
    def test_record_biomarker(self, performance_tracker):
        """Test recording a biomarker extraction result."""
        # Record a valid biomarker
        biomarker = {
            "name": "Glucose",
            "value": 95,
            "unit": "mg/dL",
            "confidence": 0.9
        }
        performance_tracker.record_biomarker(biomarker, is_valid=True)
        
        # Check metrics
        assert performance_tracker.true_positives == 1
        assert performance_tracker.false_positives == 0
        assert performance_tracker.biomarker_count == 1
        assert performance_tracker.biomarker_confidence_sum == 0.9
        
        # Record a false positive
        performance_tracker.record_biomarker(biomarker, is_valid=False)
        
        # Check metrics updated
        assert performance_tracker.true_positives == 1
        assert performance_tracker.false_positives == 1
        assert performance_tracker.biomarker_count == 2

    def test_record_missed_biomarker(self, performance_tracker):
        """Test recording a missed biomarker."""
        # Record a missed biomarker
        performance_tracker.record_missed_biomarker("Cholesterol", reason="Not detected")
        
        # Check metrics
        assert performance_tracker.false_negatives == 1
        
        # Check biomarker details
        assert len(performance_tracker.extracted_biomarkers) == 1
        assert performance_tracker.extracted_biomarkers[0]["biomarker"]["name"] == "Cholesterol"
        assert performance_tracker.extracted_biomarkers[0]["is_missed"]
        assert performance_tracker.extracted_biomarkers[0]["reason"] == "Not detected"

    def test_get_performance_metrics(self, performance_tracker):
        """Test generating performance metrics."""
        # Record some data
        biomarker1 = {"name": "Glucose", "confidence": 0.9}
        biomarker2 = {"name": "Cholesterol", "confidence": 0.8}
        
        performance_tracker.record_biomarker(biomarker1, is_valid=True)
        performance_tracker.record_biomarker(biomarker2, is_valid=True)
        performance_tracker.record_biomarker({"name": "Invalid"}, is_valid=False)
        performance_tracker.record_missed_biomarker("Missing", "Not found")
        
        # Get performance metrics
        metrics = performance_tracker.get_performance_metrics()
        
        # Check metrics structure
        assert "accuracy_metrics" in metrics
        assert "confidence_metrics" in metrics
        assert "processing_metrics" in metrics
        
        # Check accuracy metrics
        accuracy = metrics["accuracy_metrics"]
        assert accuracy["true_positives"] == 2
        assert accuracy["false_positives"] == 1
        assert accuracy["false_negatives"] == 1
        
        # Calculate expected values
        precision = 2 / 3  # TP / (TP + FP)
        recall = 2 / 3  # TP / (TP + FN)
        f1 = 2 * (precision * recall) / (precision + recall)
        
        # Check calculated metrics match expected
        assert accuracy["precision"] == pytest.approx(precision)
        assert accuracy["recall"] == pytest.approx(recall)
        assert accuracy["f1_score"] == pytest.approx(f1)
        
        # Check confidence metrics
        confidence = metrics["confidence_metrics"]
        assert confidence["avg_confidence"] == pytest.approx((0.9 + 0.8) / 2)
        assert confidence["biomarker_count"] == 2


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main(["-xvs", __file__]) 