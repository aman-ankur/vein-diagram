import unittest
from unittest.mock import patch, MagicMock, mock_open
import os
import sys
import json

# Adjust path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.document_analyzer import (
    analyze_document_structure,
    optimize_content_for_extraction,
    create_adaptive_prompt,
    update_extraction_context,
    create_default_extraction_context
)
from app.services.utils.structure_detection import (
    detect_tables,
    detect_document_zones,
    detect_document_type
)
from app.services.pdf_service import filter_relevant_pages

class TestDocumentAnalyzer(unittest.TestCase):
    def setUp(self):
        # Sample data for testing
        self.sample_text = {
            0: "This is a header with company info\nQUEST DIAGNOSTICS\nPage 1",
            1: "TEST RESULTS\nGlucose: 105 mg/dL (70-99)\nHemoglobin A1c: 5.8% (4.0-5.6)\nHigh",
            2: "More test results\nCholesterol: 210 mg/dL\nHDL: 55 mg/dL\nReference Range information"
        }
        
        self.sample_document_structure = {
            "document_type": "quest_diagnostics",
            "page_zones": {
                0: {"header": {"confidence": 0.9}, "content": {"confidence": 0.8}},
                1: {"content": {"confidence": 0.9}}
            },
            "tables": {
                1: [{"rows": 3, "cols": 3, "confidence": 0.85}]
            },
            "biomarker_regions": [
                {"page_num": 1, "biomarker_confidence": 0.9}
            ],
            "confidence": 0.8
        }
        
        self.extraction_context = {
            "known_biomarkers": {},
            "extraction_patterns": [],
            "section_context": {},
            "call_count": 0,
            "token_usage": {"input": 0, "output": 0},
            "confidence_threshold": 0.7
        }
        
        self.content_chunk = {
            "text": "Glucose: 105 mg/dL (70-99)",
            "page_num": 1,
            "region_type": "table",
            "estimated_tokens": 20,
            "biomarker_confidence": 0.9,
            "context": "TEST RESULTS"
        }

    @patch('pdfplumber.open')
    def test_analyze_document_structure(self, mock_pdf_open):
        # Mock pdfplumber functionality
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.width = 600
        mock_page.height = 800
        mock_page.extract_words.return_value = [{"bottom": 100}, {"bottom": 200}]
        mock_page.find_tables.return_value = []
        
        mock_pdf.pages = [mock_page]
        mock_pdf_open.return_value.__enter__.return_value = mock_pdf
        
        # Test document structure analysis
        result = analyze_document_structure("test.pdf", self.sample_text)
        
        # Basic assertions
        self.assertIsNotNone(result)
        self.assertIn("document_type", result)
        self.assertIn("confidence", result)
        
    def test_optimize_content_for_extraction(self):
        # Mock dependencies
        with patch('app.services.utils.content_optimization.optimize_content_chunks') as mock_optimize:
            mock_optimize.return_value = [
                {
                    "text": "Glucose: 105 mg/dL (70-99)",
                    "page_num": 1,
                    "region_type": "table",
                    "estimated_tokens": 20,
                    "biomarker_confidence": 0.9,
                    "context": "TEST RESULTS"
                }
            ]
            
            result = optimize_content_for_extraction(self.sample_text, self.sample_document_structure)
            
            # Assertions
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["text"], "Glucose: 105 mg/dL (70-99)")
            
    def test_create_adaptive_prompt(self):
        result = create_adaptive_prompt(self.content_chunk, self.extraction_context)
        
        # Assertions
        self.assertIsInstance(result, str)
        self.assertIn("Extract biomarkers", result)
        self.assertIn(self.content_chunk["text"], result)
        
    def test_update_extraction_context(self):
        biomarker_results = [
            {"name": "Glucose", "value": 105, "unit": "mg/dL"}
        ]
        
        updated_context = update_extraction_context(
            self.extraction_context,
            self.content_chunk,
            biomarker_results
        )
        
        # Assertions
        self.assertIn("glucose", updated_context["known_biomarkers"])
        self.assertEqual(updated_context["call_count"], 1)
        
    def test_filter_relevant_pages_basic(self):
        """Test the basic functionality of filter_relevant_pages without document structure."""
        with patch('app.services.pdf_service._load_biomarker_aliases') as mock_load:
            mock_load.return_value = ["glucose", "cholesterol", "hemoglobin"]
            
            # Test with biomarker text
            pages_text = {
                0: "Header page with no biomarkers",
                1: "Glucose: 105 mg/dL Results",
                2: "Normal text with no biomarkers"
            }
            
            result = filter_relevant_pages(pages_text)
            
            # Should include page 1 with biomarkers
            self.assertIn(1, result)
            
    def test_filter_relevant_pages_with_structure(self):
        """Test filter_relevant_pages with document structure."""
        with patch('app.services.pdf_service._load_biomarker_aliases') as mock_load, \
             patch('app.services.pdf_service.contain_biomarker_patterns') as mock_patterns:
            
            mock_load.return_value = ["glucose", "cholesterol"]
            # Make contain_biomarker_patterns return True for testing
            mock_patterns.return_value = True
            
            pages_text = {
                0: "Header page",
                1: "Page with table",
                2: "Content page"
            }
            
            document_structure = {
                "tables": {1: [{"some": "table"}]},
                "page_zones": {
                    0: {"content": {"confidence": 0.8}},
                    2: {"content": {"confidence": 0.8}}
                }
            }
            
            result = filter_relevant_pages(pages_text, document_structure)
            
            # Should include pages based on structure and biomarker patterns
            self.assertIn(1, result)  # Has table
            self.assertIn(0, result)  # Has content and biomarkers
            self.assertIn(2, result)  # Has content and biomarkers
    
    def test_filter_relevant_pages_empty_structure(self):
        """Test filter_relevant_pages with empty document structure."""
        with patch('app.services.pdf_service._load_biomarker_aliases') as mock_load:
            mock_load.return_value = ["glucose", "cholesterol"]
            
            pages_text = {
                0: "Glucose: 105 mg/dL",
                1: "Cholesterol: 200 mg/dL"
            }
            
            # Empty structure
            document_structure = {
                "tables": {},
                "page_zones": {},
                "biomarker_regions": [],
                "confidence": 0.1
            }
            
            result = filter_relevant_pages(pages_text, document_structure)
            
            # Should fall back to original method
            self.assertIn(0, result)
            self.assertIn(1, result)
    
    def test_create_default_extraction_context(self):
        context = create_default_extraction_context()
        
        # Assertions
        self.assertEqual(context["call_count"], 0)
        self.assertIn("known_biomarkers", context)
        self.assertIn("confidence_threshold", context)
    
    def test_table_detection_robust(self):
        """Test that table detection handles errors gracefully."""
        # Create a mock page that will cause errors
        mock_page = MagicMock()
        
        # Case 1: Mock find_tables raising exception
        mock_page.find_tables.side_effect = Exception("Test exception")
        
        # Should not raise exception
        result = detect_tables(mock_page, 0)
        self.assertEqual(result, [])
        
        # Case 2: Mock cells attribute that's a list but has weird structure
        mock_page.find_tables.side_effect = None
        mock_table = MagicMock()
        mock_table.bbox = [0, 0, 100, 100]
        mock_table.cells = [(1,), (2,)]  # Malformed cell data
        mock_page.find_tables.return_value = [mock_table]
        
        # Should handle gracefully
        result = detect_tables(mock_page, 0)
        self.assertEqual(len(result), 1)

if __name__ == '__main__':
    unittest.main() 