"""
Tests for the document_analyzer module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import pytest_asyncio

from app.services.document_analyzer import (
    analyze_document_structure,
    optimize_content_for_extraction,
    create_adaptive_prompt,
    update_extraction_context,
    create_default_extraction_context,
    DocumentStructure,
    ContentChunk,
    ExtractionContext
)

# Mock data for tests
@pytest.fixture
def sample_pages_text():
    return {
        0: "Quest Diagnostics\nPatient: John Doe\nTest Results\nHemoglobin: 14.2 g/dL\nRef Range: 13.0-17.0",
        1: "Glucose: 95 mg/dL\nRef Range: 70-99\nAlbumin: 4.5 g/dL\nRef Range: 3.4-5.4"
    }

@pytest.fixture
def sample_document_structure():
    return {
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

@pytest.fixture
def sample_extraction_context():
    return {
        "known_biomarkers": {
            "hemoglobin": {
                "name": "Hemoglobin",
                "value": "14.2",
                "unit": "g/dL",
                "reference_range": "13.0-17.0",
                "page": 0
            }
        },
        "extraction_patterns": ["Hemoglobin: 14.2 g/dL"],
        "section_context": {"last_page": "0", "biomarker_count": "1"},
        "call_count": 1,
        "token_usage": {"input": 1000, "output": 500},
        "confidence_threshold": 0.7
    }


class TestDocumentAnalyzer:
    """Tests for document analyzer module."""

    def test_analyze_document_structure_with_no_pdfplumber(self, sample_pages_text):
        """Test analyze_document_structure with pdfplumber unavailable."""
        with patch('app.services.document_analyzer.pdfplumber', None):
            result = analyze_document_structure("dummy.pdf", sample_pages_text)
            assert result["confidence"] == 0.0
            assert result["document_type"] is None
    
    @patch('app.services.document_analyzer.pdfplumber')
    def test_analyze_document_structure_basic(self, mock_pdfplumber, sample_pages_text):
        """Test basic document structure analysis."""
        # Create mock PDF and pages
        mock_pdf = MagicMock()
        mock_page1 = MagicMock()
        mock_page2 = MagicMock()
        
        # Configure mocks
        mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        mock_pdf.pages = [mock_page1, mock_page2]
        
        # Call the function
        result = analyze_document_structure("dummy.pdf", sample_pages_text)
        
        # Verify the result
        assert result["confidence"] > 0
        assert isinstance(result, dict)
        assert "document_type" in result
        assert "page_zones" in result
        assert "tables" in result
    
    def test_optimize_content_for_extraction(self, sample_pages_text, sample_document_structure):
        """Test content optimization."""
        chunks = optimize_content_for_extraction(sample_pages_text, sample_document_structure)
        
        # Verify the result
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        for chunk in chunks:
            assert "text" in chunk
            assert "page_num" in chunk
            assert "estimated_tokens" in chunk
            assert chunk["page_num"] in sample_pages_text
    
    def test_create_adaptive_prompt(self, sample_extraction_context):
        """Test adaptive prompt creation."""
        chunk = {
            "text": "Glucose: 95 mg/dL\nRef Range: 70-99",
            "page_num": 1,
            "region_type": "text",
            "estimated_tokens": 100,
            "biomarker_confidence": 0.8,
            "context": "Page 1, text"
        }
        
        prompt = create_adaptive_prompt(chunk, sample_extraction_context)
        
        # Verify prompt contains expected elements
        assert "glucose" in prompt.lower() or "95 mg/dl" in prompt.lower()
        assert "page 1" in prompt.lower()
        
        # Test with new context (first call)
        new_context = create_default_extraction_context()
        new_prompt = create_adaptive_prompt(chunk, new_context)
        
        # First prompt should be different from subsequent ones
        assert new_prompt != prompt
    
    def test_update_extraction_context(self, sample_extraction_context):
        """Test extraction context updates."""
        chunk = {
            "text": "Glucose: 95 mg/dL\nRef Range: 70-99",
            "page_num": 1,
            "region_type": "text",
            "estimated_tokens": 100,
            "biomarker_confidence": 0.8,
            "context": "Page 1, text"
        }
        
        results = [
            {
                "name": "Glucose",
                "value": "95",
                "unit": "mg/dL",
                "reference_range": "70-99"
            }
        ]
        
        updated_context = update_extraction_context(
            sample_extraction_context, 
            chunk,
            results
        )
        
        # Verify the context was updated
        assert updated_context["call_count"] == sample_extraction_context["call_count"] + 1
        assert "glucose" in [k.lower() for k in updated_context["known_biomarkers"].keys()]
        assert updated_context["token_usage"]["input"] >= sample_extraction_context["token_usage"]["input"]
    
    def test_create_default_extraction_context(self):
        """Test default extraction context creation."""
        context = create_default_extraction_context()
        
        # Verify the context has expected structure
        assert "known_biomarkers" in context
        assert "extraction_patterns" in context
        assert "call_count" in context
        assert context["call_count"] == 0
        assert "token_usage" in context
        assert "confidence_threshold" in context 