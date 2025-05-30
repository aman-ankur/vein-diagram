"""
Test suite for Biomarker Caching System.

This module tests the biomarker caching functionality that reduces LLM API calls
by using intelligent pattern matching for common biomarkers.
"""

import unittest
import tempfile
import os
import json
from unittest.mock import patch, MagicMock
import sys

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.utils.biomarker_cache import (
    BiomarkerCache,
    BiomarkerPattern,
    CacheStatistics,
    get_biomarker_cache,
    extract_cached_biomarkers
)


class TestBiomarkerCache(unittest.TestCase):
    """Test cases for biomarker caching functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary cache file for testing
        self.temp_dir = tempfile.mkdtemp()
        self.cache_file = os.path.join(self.temp_dir, 'test_cache.json')
        
        # Initialize cache with test file
        self.cache = BiomarkerCache(cache_file=self.cache_file, max_cache_size=10)
        
        # Test biomarker patterns
        self.glucose_pattern = BiomarkerPattern(
            name="glucose",
            standardized_name="Glucose",
            common_units=["mg/dL", "mg/dl"],
            typical_ranges={"mg/dL": {"low": 70, "high": 99}},
            pattern_variations=["glucose", "blood glucose", "glu"],
            confidence_threshold=0.9,
            last_seen="2024-01-01T00:00:00",
            frequency_count=5,
            success_rate=0.95
        )
        
        # Sample lab report text with various formats
        self.lab_text_simple = "Glucose: 105 mg/dL"
        self.lab_text_with_range = "Glucose: 105 mg/dL (70-99)"
        self.lab_text_table_format = """
        Test Name          Result    Unit     Reference Range
        Glucose            105       mg/dL    70-99
        Total Cholesterol  180       mg/dL    <200
        """
        self.lab_text_multiple = """
        Blood Glucose: 105 mg/dL
        HDL Cholesterol: 45 mg/dL
        LDL Cholesterol: 110 mg/dL
        Triglycerides: 120 mg/dL
        """
        
        # Real lab report example (similar to user's screenshots)
        self.real_lab_text = """
        LABORATORY REPORT                          Redcliffe labs
        Patient NAME    : Mr aman ankur            Report STATUS : Final Report
        DOB/Age/Gender  : 32 Y/Male               Barcode NO    : HQ128533
        
        Hemoglobin (Hb)                   15.2     g/dL        13.0-17.0
        Hematocrit                        45.8     %           40.0-50.0
        Total Cholesterol                 195      mg/dL       <200
        HDL Cholesterol                   42       mg/dL       >40
        LDL Cholesterol                   125      mg/dL       <100
        Triglycerides                     140      mg/dL       <150
        Glucose (Fasting)                 98       mg/dL       70-99
        Creatinine                        1.1      mg/dL       0.6-1.2
        """

    def tearDown(self):
        """Clean up test fixtures."""
        # Remove temporary files
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        os.rmdir(self.temp_dir)

    def test_cache_initialization(self):
        """Test cache initialization with common biomarkers."""
        # Fresh cache should have common biomarkers
        self.assertGreater(len(self.cache.biomarker_patterns), 0)
        
        # Check that glucose pattern exists
        self.assertIn("glucose", self.cache.biomarker_patterns)
        
        # Check glucose pattern properties
        glucose = self.cache.biomarker_patterns["glucose"]
        self.assertEqual(glucose.standardized_name, "Glucose")
        self.assertIn("mg/dL", glucose.common_units)
        self.assertIn("glucose", glucose.pattern_variations)

    def test_simple_biomarker_extraction(self):
        """Test extracting simple biomarker patterns."""
        results = self.cache.extract_cached_biomarkers(self.lab_text_simple)
        
        # Should find glucose
        self.assertGreater(len(results), 0)
        
        glucose_result = None
        for result in results:
            if "glucose" in result["name"].lower():
                glucose_result = result
                break
        
        self.assertIsNotNone(glucose_result)
        self.assertEqual(glucose_result["value"], 105.0)
        self.assertEqual(glucose_result["unit"], "mg/dL")
        self.assertEqual(glucose_result["extraction_method"], "cache")

    def test_biomarker_extraction_with_reference_range(self):
        """Test extracting biomarkers with reference ranges."""
        results = self.cache.extract_cached_biomarkers(self.lab_text_with_range)
        
        glucose_result = None
        for result in results:
            if "glucose" in result["name"].lower():
                glucose_result = result
                break
        
        self.assertIsNotNone(glucose_result)
        self.assertEqual(glucose_result["value"], 105.0)
        self.assertEqual(glucose_result["reference_range_low"], 70.0)
        self.assertEqual(glucose_result["reference_range_high"], 99.0)
        self.assertTrue(glucose_result["is_abnormal"])  # 105 > 99

    def test_table_format_extraction(self):
        """Test extracting biomarkers from table format."""
        results = self.cache.extract_cached_biomarkers(self.lab_text_table_format)
        
        # Should find glucose and cholesterol
        biomarker_names = [r["name"].lower() for r in results]
        self.assertTrue(any("glucose" in name for name in biomarker_names))
        self.assertTrue(any("cholesterol" in name for name in biomarker_names))

    def test_multiple_biomarkers_extraction(self):
        """Test extracting multiple biomarkers from text."""
        results = self.cache.extract_cached_biomarkers(self.lab_text_multiple)
        
        # Should find glucose, HDL, LDL, and triglycerides
        self.assertGreaterEqual(len(results), 3)
        
        biomarker_names = [r["name"].lower() for r in results]
        expected_biomarkers = ["glucose", "hdl", "ldl", "triglycerides"]
        
        for expected in expected_biomarkers:
            self.assertTrue(
                any(expected in name for name in biomarker_names),
                f"Expected to find {expected} in extracted biomarkers"
            )

    def test_real_lab_report_extraction(self):
        """Test extraction from real lab report format."""
        results = self.cache.extract_cached_biomarkers(self.real_lab_text)
        
        # Should find multiple biomarkers
        self.assertGreaterEqual(len(results), 5)
        
        # Check specific biomarkers
        result_dict = {r["name"].lower(): r for r in results}
        
        # Check hemoglobin
        self.assertTrue(any("hemoglobin" in name for name in result_dict.keys()))
        
        # Check glucose
        glucose_results = [r for r in results if "glucose" in r["name"].lower()]
        if glucose_results:
            glucose = glucose_results[0]
            self.assertEqual(glucose["value"], 98.0)
            self.assertEqual(glucose["unit"], "mg/dL")

    def test_cache_statistics_tracking(self):
        """Test cache statistics are properly tracked."""
        initial_stats = self.cache.get_cache_statistics()
        initial_extractions = initial_stats["total_extractions"]
        
        # Perform extractions
        self.cache.extract_cached_biomarkers(self.lab_text_simple)
        self.cache.extract_cached_biomarkers(self.lab_text_multiple)
        
        # Check updated statistics
        updated_stats = self.cache.get_cache_statistics()
        self.assertEqual(
            updated_stats["total_extractions"], 
            initial_extractions + 2
        )
        self.assertGreaterEqual(updated_stats["cache_hits"], 1)

    def test_cache_learning_from_llm_extraction(self):
        """Test cache learning from LLM extractions."""
        # Simulate LLM extraction result
        llm_biomarkers = [
            {
                "name": "Vitamin D",
                "value": 25.0,
                "unit": "ng/mL",
                "confidence": 0.9,
                "category": "Vitamins"
            }
        ]
        
        original_cache_size = len(self.cache.biomarker_patterns)
        
        # Learn from extraction
        self.cache.learn_from_extraction(
            extracted_biomarkers=llm_biomarkers,
            text="Vitamin D: 25.0 ng/mL",
            method="llm"
        )
        
        # Cache should have learned (if there's room)
        if original_cache_size < self.cache.max_cache_size:
            self.assertGreaterEqual(len(self.cache.biomarker_patterns), original_cache_size)

    def test_cache_persistence(self):
        """Test cache saving and loading."""
        # Add a test pattern
        test_pattern = BiomarkerPattern(
            name="test_biomarker",
            standardized_name="Test Biomarker",
            common_units=["units"],
            typical_ranges={"units": {"low": 0, "high": 100}},
            pattern_variations=["test"],
            confidence_threshold=0.8,
            last_seen="2024-01-01T00:00:00",
            frequency_count=1
        )
        self.cache.biomarker_patterns["test_biomarker"] = test_pattern
        
        # Save cache
        self.assertTrue(self.cache.save_cache())
        self.assertTrue(os.path.exists(self.cache_file))
        
        # Create new cache instance and load
        new_cache = BiomarkerCache(cache_file=self.cache_file)
        self.assertIn("test_biomarker", new_cache.biomarker_patterns)

    def test_cache_optimization(self):
        """Test cache optimization removes low-performing patterns."""
        # Fill cache to trigger optimization
        for i in range(self.cache.max_cache_size + 2):
            pattern = BiomarkerPattern(
                name=f"test_pattern_{i}",
                standardized_name=f"Test Pattern {i}",
                common_units=["units"],
                typical_ranges={},
                pattern_variations=[f"test{i}"],
                confidence_threshold=0.5,
                last_seen="2024-01-01T00:00:00",
                frequency_count=1 if i < 5 else 10,  # Some patterns more frequent
                success_rate=0.5 if i < 5 else 0.9   # Some patterns more successful
            )
            self.cache.biomarker_patterns[f"test_pattern_{i}"] = pattern
        
        original_size = len(self.cache.biomarker_patterns)
        self.cache.optimize_cache()
        
        # Should have removed some patterns
        self.assertLessEqual(len(self.cache.biomarker_patterns), original_size)

    def test_pattern_variations_matching(self):
        """Test different pattern variations are matched correctly."""
        # Test different glucose variations
        test_texts = [
            "Blood glucose: 105 mg/dL",
            "Fasting glucose: 105 mg/dL", 
            "Glu: 105 mg/dL",
            "Glucose (Random): 105 mg/dL"
        ]
        
        for text in test_texts:
            results = self.cache.extract_cached_biomarkers(text)
            glucose_found = any("glucose" in r["name"].lower() for r in results)
            self.assertTrue(glucose_found, f"Failed to find glucose in: {text}")

    def test_unit_variations_matching(self):
        """Test different unit variations are matched correctly."""
        # Test different unit formats
        test_texts = [
            "Glucose: 105 mg/dL",
            "Glucose: 105 mg/dl", 
            "Glucose: 5.8 mmol/L",
            "Glucose: 5.8 mmol/l"
        ]
        
        for text in test_texts:
            results = self.cache.extract_cached_biomarkers(text)
            glucose_found = any("glucose" in r["name"].lower() for r in results)
            self.assertTrue(glucose_found, f"Failed to find glucose in: {text}")

    def test_abnormal_value_detection(self):
        """Test detection of abnormal biomarker values."""
        # Test abnormal glucose (high)
        high_glucose_text = "Glucose: 250 mg/dL (70-99)"
        results = self.cache.extract_cached_biomarkers(high_glucose_text)
        
        glucose_result = None
        for result in results:
            if "glucose" in result["name"].lower():
                glucose_result = result
                break
        
        self.assertIsNotNone(glucose_result)
        self.assertTrue(glucose_result["is_abnormal"])
        
        # Test normal glucose
        normal_glucose_text = "Glucose: 85 mg/dL (70-99)"
        results = self.cache.extract_cached_biomarkers(normal_glucose_text)
        
        glucose_result = None
        for result in results:
            if "glucose" in result["name"].lower():
                glucose_result = result
                break
        
        self.assertIsNotNone(glucose_result)
        self.assertFalse(glucose_result["is_abnormal"])

    def test_cache_confidence_levels(self):
        """Test cache confidence levels are properly assigned."""
        results = self.cache.extract_cached_biomarkers(self.lab_text_simple)
        
        for result in results:
            self.assertIn("confidence", result)
            self.assertGreaterEqual(result["confidence"], 0.0)
            self.assertLessEqual(result["confidence"], 1.0)
            self.assertEqual(result["extraction_method"], "cache")

    def test_global_cache_singleton(self):
        """Test global cache singleton functionality."""
        cache1 = get_biomarker_cache()
        cache2 = get_biomarker_cache()
        
        # Should be the same instance
        self.assertIs(cache1, cache2)

    def test_extract_cached_biomarkers_convenience_function(self):
        """Test convenience function for extracting cached biomarkers."""
        # This uses the global cache
        results = extract_cached_biomarkers(self.lab_text_simple)
        
        # Should return results
        self.assertIsInstance(results, list)


class TestBiomarkerCacheIntegration(unittest.TestCase):
    """Integration tests for biomarker cache with PDF processing."""

    def setUp(self):
        """Set up integration test fixtures."""
        self.cache = BiomarkerCache(max_cache_size=50)

    def test_cache_integration_workflow(self):
        """Test complete cache integration workflow."""
        # Step 1: Extract using cache (should find some biomarkers)
        text = """
        Complete Blood Count (CBC)
        Hemoglobin: 14.5 g/dL (13.0-17.0)
        Hematocrit: 43.2% (40.0-50.0)
        
        Lipid Profile
        Total Cholesterol: 185 mg/dL (<200)
        HDL Cholesterol: 48 mg/dL (>40)
        LDL Cholesterol: 115 mg/dL (<100)
        Triglycerides: 110 mg/dL (<150)
        
        Metabolic Panel
        Glucose (Fasting): 92 mg/dL (70-99)
        Creatinine: 0.9 mg/dL (0.6-1.2)
        """
        
        # Extract with cache
        cache_results = self.cache.extract_cached_biomarkers(text)
        
        # Should find multiple biomarkers
        self.assertGreater(len(cache_results), 5)
        
        # Verify we found expected biomarkers
        found_names = [r["name"].lower() for r in cache_results]
        expected_biomarkers = [
            "hemoglobin", "cholesterol", "hdl", "ldl", 
            "triglycerides", "glucose", "creatinine"
        ]
        
        for expected in expected_biomarkers:
            found = any(expected in name for name in found_names)
            self.assertTrue(found, f"Expected to find {expected}")
        
        # Step 2: Simulate learning from LLM for missed biomarkers
        # (In real workflow, uncached biomarkers would be sent to LLM)
        llm_results = [
            {
                "name": "Hematocrit",
                "value": 43.2,
                "unit": "%",
                "confidence": 0.9
            }
        ]
        
        # Learn from LLM results
        self.cache.learn_from_extraction(llm_results, text, "llm")
        
        # Step 3: Get final statistics
        stats = self.cache.get_cache_statistics()
        self.assertGreater(stats["cache_hits"], 0)
        self.assertGreater(stats["cache_hit_rate"], 0.0)


if __name__ == '__main__':
    unittest.main() 