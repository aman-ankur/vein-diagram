"""
Integration tests for the enhanced extraction pipeline with document structure analysis.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
import json
from pathlib import Path

from app.services.document_analyzer import (
    analyze_document_structure,
    optimize_content_for_extraction,
    create_default_extraction_context
)
from app.services.pdf_service import (
    process_pdf_background,
    filter_relevant_pages,
    process_pages_sequentially
)
from app.core.config import DOCUMENT_ANALYZER_CONFIG


# Test data
@pytest.fixture
def sample_pdf_path():
    # This would point to a test PDF file
    return "tests/data/sample_lab_report.pdf"


@pytest.fixture
def sample_pages_text():
    return {
        0: "Quest Diagnostics\nPatient: John Doe\nTest Results\nHemoglobin: 14.2 g/dL\nRef Range: 13.0-17.0",
        1: "Glucose: 95 mg/dL\nRef Range: 70-99\nAlbumin: 4.5 g/dL\nRef Range: 3.4-5.4"
    }


@pytest.fixture
def expected_biomarkers():
    return [
        {
            "name": "Hemoglobin",
            "value": "14.2",
            "unit": "g/dL",
            "reference_range": "13.0-17.0",
            "page": 0
        },
        {
            "name": "Glucose",
            "value": "95",
            "unit": "mg/dL",
            "reference_range": "70-99",
            "page": 1
        },
        {
            "name": "Albumin",
            "value": "4.5",
            "unit": "g/dL",
            "reference_range": "3.4-5.4",
            "page": 1
        }
    ]


class TestExtractionPipeline:
    """Test the complete extraction pipeline with document structure analysis."""
    
    @pytest.mark.asyncio
    @patch('app.services.pdf_service.extract_biomarkers_with_claude')
    @patch('app.services.document_analyzer.analyze_document_structure')
    @patch('app.services.pdf_service.extract_text_from_pdf')
    async def test_extraction_with_structure_analysis(
        self,
        mock_extract_text,
        mock_analyze_structure,
        mock_extract_biomarkers,
        sample_pdf_path,
        sample_pages_text,
        expected_biomarkers
    ):
        """Test the extraction pipeline with structure analysis enabled."""
        # Configure mocks
        mock_extract_text.return_value = sample_pages_text
        
        # Mock document structure
        mock_document_structure = {
            "document_type": "quest_diagnostics",
            "page_zones": {
                0: {
                    "header": {"zone_type": "header", "bbox": [0, 0, 612, 100], "confidence": 0.8},
                    "content": {"zone_type": "content", "bbox": [0, 100, 612, 700], "confidence": 0.9},
                    "footer": {"zone_type": "footer", "bbox": [0, 700, 612, 792], "confidence": 0.8}
                },
                1: {
                    "header": {"zone_type": "header", "bbox": [0, 0, 612, 100], "confidence": 0.8},
                    "content": {"zone_type": "content", "bbox": [0, 100, 612, 700], "confidence": 0.9},
                    "footer": {"zone_type": "footer", "bbox": [0, 700, 612, 792], "confidence": 0.8}
                }
            },
            "tables": {
                1: [
                    {
                        "bbox": [50, 200, 550, 300],
                        "page_number": 1,
                        "rows": 3,
                        "cols": 2,
                        "confidence": 0.85,
                        "index": 0
                    }
                ]
            },
            "biomarker_regions": [],
            "confidence": 0.8
        }
        mock_analyze_structure.return_value = mock_document_structure
        
        # Mock biomarker extraction
        mock_extract_biomarkers.side_effect = [
            [expected_biomarkers[0]],  # First call returns first biomarker
            expected_biomarkers[1:],   # Second call returns remaining biomarkers
        ]
        
        # Enable document analyzer config for test
        original_config = DOCUMENT_ANALYZER_CONFIG.copy()
        DOCUMENT_ANALYZER_CONFIG["enabled"] = True
        DOCUMENT_ANALYZER_CONFIG["structure_analysis"]["enabled"] = True
        DOCUMENT_ANALYZER_CONFIG["content_optimization"]["enabled"] = True
        DOCUMENT_ANALYZER_CONFIG["adaptive_context"]["enabled"] = True
        
        try:
            # Call the process function
            # Note: In a real implementation, you'd need to handle database interactions
            pdf_id = "test_pdf_id"
            user_id = "test_user_id"
            
            with patch('app.services.pdf_service.store_processing_result'):
                await process_pdf_background(pdf_id, sample_pdf_path, user_id)
            
            # Verify structure analysis was called
            mock_analyze_structure.assert_called_once()
            
            # Verify extraction was called with appropriate structure
            assert mock_extract_biomarkers.call_count > 0
            
            # In a real test, you would also verify the biomarkers were stored correctly
        
        finally:
            # Restore original config
            DOCUMENT_ANALYZER_CONFIG.update(original_config)
    
    @pytest.mark.asyncio
    async def test_filter_relevant_pages_with_structure(self, sample_pages_text):
        """Test page filtering with document structure."""
        # Create sample document structure
        document_structure = {
            "document_type": "quest_diagnostics",
            "tables": {1: [{"bbox": [0, 0, 100, 100], "page_number": 1}]},
            "page_zones": {
                0: {"content": {"zone_type": "content", "confidence": 0.8}},
                1: {"content": {"zone_type": "content", "confidence": 0.9}}
            },
            "biomarker_regions": [],
            "confidence": 0.8
        }
        
        # Call filter_relevant_pages with structure
        with patch('app.services.pdf_service.contain_biomarker_patterns', return_value=True):
            filtered_pages = filter_relevant_pages(sample_pages_text, document_structure)
        
        # Verify pages were filtered correctly
        assert len(filtered_pages) > 0
        # Page with table should be included
        assert 1 in filtered_pages
    
    @pytest.mark.asyncio
    @patch('app.services.pdf_service.extract_biomarkers_with_claude')
    async def test_process_pages_with_content_optimization(
        self,
        mock_extract_biomarkers,
        sample_pages_text,
        expected_biomarkers
    ):
        """Test page processing with content optimization."""
        # Configure mock
        mock_extract_biomarkers.return_value = expected_biomarkers
        
        # Create sample document structure
        document_structure = {
            "document_type": "quest_diagnostics",
            "tables": {1: [{"bbox": [0, 0, 100, 100], "page_number": 1}]},
            "page_zones": {
                0: {"content": {"zone_type": "content", "confidence": 0.8}},
                1: {"content": {"zone_type": "content", "confidence": 0.9}}
            },
            "biomarker_regions": [],
            "confidence": 0.8
        }
        
        # Enable document analyzer config for test
        original_config = DOCUMENT_ANALYZER_CONFIG.copy()
        DOCUMENT_ANALYZER_CONFIG["enabled"] = True
        DOCUMENT_ANALYZER_CONFIG["content_optimization"]["enabled"] = True
        DOCUMENT_ANALYZER_CONFIG["adaptive_context"]["enabled"] = True
        
        try:
            # Process pages with optimization
            biomarkers = await process_pages_sequentially(sample_pages_text, document_structure)
            
            # Verify results
            assert len(biomarkers) > 0
            assert mock_extract_biomarkers.call_count > 0
            
            # In a real test with real data, you'd verify the chunk optimization worked
        
        finally:
            # Restore original config
            DOCUMENT_ANALYZER_CONFIG.update(original_config) 