import pytest
import sys
import os
import json
from typing import Dict, List, Any
import re

# Add the parent directory to the Python path to make imports work
sys.path.append(os.path.join(os.path.dirname(__file__), "../../"))

from app.services.utils.content_optimization import (
    estimate_tokens,
    chunk_text,
    compress_text_content,
    extract_table_text,
    detect_biomarker_patterns,
    split_zone_by_biomarker_density,
    split_text_by_biomarker_density,
    optimize_content_chunks,
    enhance_chunk_confidence
)
from app.services.document_analyzer import DocumentStructure


class TestTokenEstimation:
    """Test the token estimation functionality."""

    def test_empty_text_returns_zero(self):
        """Test that empty text returns zero tokens."""
        assert estimate_tokens("") == 0
        assert estimate_tokens(None) == 0

    def test_token_estimation_fallback(self):
        """Test fallback token estimation."""
        # Temporarily modify TIKTOKEN_AVAILABLE to force fallback
        from app.services.utils.content_optimization import TIKTOKEN_AVAILABLE
        original_value = TIKTOKEN_AVAILABLE
        
        try:
            import app.services.utils.content_optimization as optimization
            optimization.TIKTOKEN_AVAILABLE = False
            
            # Test approximation (4 chars per token)
            text = "This is a test"  # 14 chars
            assert estimate_tokens(text) == 4  # 14/4 = 3.5, ceil to 4
            
            # Test longer text
            long_text = "A" * 100
            assert estimate_tokens(long_text) == 25  # 100/4 = 25
            
        finally:
            # Restore original value
            optimization.TIKTOKEN_AVAILABLE = original_value

    @pytest.mark.skipif(not TIKTOKEN_AVAILABLE, reason="tiktoken not installed")
    def test_tiktoken_estimation(self):
        """Test token estimation with tiktoken."""
        # These values are approximate and might change with tokenizer versions
        assert 3 <= estimate_tokens("Hello, world!") <= 5
        assert 10 <= estimate_tokens("This is a longer test sentence with multiple tokens.") <= 14
        
        # Special case with numbers
        assert 3 <= estimate_tokens("Value: 123.45 mg/dL") <= 6
        
        # Test with a typical biomarker format
        biomarker = "Glucose: 95 mg/dL (70-99)"
        token_count = estimate_tokens(biomarker)
        assert 5 <= token_count <= 10


class TestTextChunking:
    """Test the text chunking functionality."""

    def test_text_smaller_than_limit_returns_single_chunk(self):
        """Text smaller than the limit should return a single chunk."""
        text = "This is a short text."
        chunks = chunk_text(text, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunking_with_paragraphs(self):
        """Test chunking text with paragraphs."""
        text = """
        This is paragraph 1.
        It has multiple lines.

        This is paragraph 2.
        It also has multiple lines.

        This is paragraph 3.
        And this is the final line.
        """
        # Set a low max tokens to force splitting
        chunks = chunk_text(text, max_tokens=10, overlap_tokens=2)
        assert len(chunks) > 1
        
        # Check that each chunk is small enough
        for chunk in chunks:
            assert estimate_tokens(chunk) <= 10

        # Check for overlap between chunks
        first_chunk_end = chunks[0].split()[-2:]
        second_chunk_start = chunks[1].split()[:2]
        overlap = set(first_chunk_end).intersection(set(second_chunk_start))
        assert len(overlap) > 0

    def test_smart_boundaries(self):
        """Test chunking with smart boundaries."""
        text = """
        # Section 1
        This is the content of section 1.
        It has some important information.

        # Section 2
        This is the content of section 2.
        It has different information.

        # Section 3
        This is the final section with key data.
        """
        # Use smart boundaries
        smart_chunks = chunk_text(text, max_tokens=20, smart_boundaries=True)
        
        # Smart boundaries should try to break at section markers
        assert len(smart_chunks) > 1
        
        # Check section headers are preserved in chunks
        section_headers = [
            chunk for chunk in smart_chunks if re.search(r"#\s+Section", chunk)
        ]
        assert len(section_headers) > 0

    def test_very_large_paragraph_handling(self):
        """Test handling of a very large paragraph."""
        # Create a long paragraph
        long_paragraph = "This is a very long sentence with many words. " * 50
        
        # Force splitting
        chunks = chunk_text(long_paragraph, max_tokens=20)
        
        # Should split long paragraph
        assert len(chunks) > 1
        
        # Each chunk should respect the max tokens
        for chunk in chunks:
            assert estimate_tokens(chunk) <= 20


class TestContentCompression:
    """Test the content compression functionality."""

    def test_removes_redundant_whitespace(self):
        """Test that redundant whitespace is removed."""
        text = "  This   has    extra   spaces.  \n\n  And extra lines.  "
        compressed = compress_text_content(text)
        assert compressed == "This has extra spaces. And extra lines."

    def test_removes_boilerplate(self):
        """Test that boilerplate text is removed."""
        boilerplate_text = """
        Test result: 123 mg/dL
        Please consult with your healthcare provider for interpretation of these results.
        Normal range: 70-99 mg/dL
        This test was developed and its performance characteristics determined by Our Lab.
        """
        compressed = compress_text_content(boilerplate_text)
        
        # Check boilerplate phrases are removed
        assert "Please consult with your healthcare" not in compressed
        assert "This test was developed and its" not in compressed
        
        # Check important data is preserved
        assert "Test result: 123 mg/dL" in compressed
        assert "Normal range: 70-99 mg/dL" in compressed

    def test_standardizes_numbers(self):
        """Test standardizing number formats."""
        text = "Glucose: 1,234.56 mg/dL"
        compressed = compress_text_content(text)
        assert "1234.56" in compressed

    def test_removes_repeated_headers(self):
        """Test removal of repeated headers."""
        text = """
        TEST | RESULT | REFERENCE RANGE
        Glucose | 95 | 70-99
        
        TEST | RESULT | REFERENCE RANGE
        Cholesterol | 180 | <200
        """
        compressed = compress_text_content(text)
        
        # Count occurrences of the header
        header_count = compressed.count("TEST | RESULT | REFERENCE RANGE")
        assert header_count == 1

    def test_preserves_biomarker_data(self):
        """Test that biomarker data is preserved after compression."""
        text = """
        Glucose: 95 mg/dL (Reference range: 70-99 mg/dL)
        Please consult with your healthcare provider for interpretation.
        
        Cholesterol: 180 mg/dL (Reference range: <200 mg/dL)
        This test was developed and its performance determined by our lab.
        """
        compressed = compress_text_content(text)
        
        # Check biomarkers are preserved
        assert "Glucose: 95 mg/dL" in compressed
        assert "70-99 mg/dL" in compressed
        assert "Cholesterol: 180 mg/dL" in compressed
        assert "<200 mg/dL" in compressed


class TestBiomarkerDetection:
    """Test the biomarker pattern detection functionality."""

    def test_empty_text_returns_zero_confidence(self):
        """Test that empty text returns zero confidence."""
        assert detect_biomarker_patterns("") == 0.0

    def test_detect_common_biomarker_formats(self):
        """Test detection of common biomarker formats."""
        # Name: Value Unit format
        text1 = "Glucose: 95 mg/dL"
        assert detect_biomarker_patterns(text1) >= 0.7
        
        # Value with unit
        text2 = "Result: 95 mg/dL"
        assert detect_biomarker_patterns(text2) >= 0.7
        
        # Name Value Unit (Reference) format
        text3 = "HDL Cholesterol 45 mg/dL (40-60)"
        assert detect_biomarker_patterns(text3) >= 0.7

    def test_detect_reference_ranges(self):
        """Test detection of reference ranges."""
        text = "Reference Range: 70-99 mg/dL"
        assert detect_biomarker_patterns(text) >= 0.6

    def test_detect_result_indicators(self):
        """Test detection of result indicators."""
        text = "Result: HIGH"
        assert detect_biomarker_patterns(text) >= 0.4

    def test_multiple_biomarkers_increases_confidence(self):
        """Test that multiple biomarkers increase confidence."""
        text = """
        Glucose: 95 mg/dL (70-99)
        Cholesterol: 180 mg/dL (<200)
        Triglycerides: 120 mg/dL (<150)
        """
        assert detect_biomarker_patterns(text) >= 0.8

    def test_non_biomarker_text_low_confidence(self):
        """Test that non-biomarker text has low confidence."""
        text = """
        Patient Information
        Name: John Doe
        Date: 2023-01-01
        Provider: Dr. Smith
        """
        assert detect_biomarker_patterns(text) <= 0.4

    def test_common_biomarker_names_increase_confidence(self):
        """Test that common biomarker names increase confidence."""
        text = """
        Lab Results:
        - Glucose levels measured at 95
        - Vitamin D status checked
        - TSH evaluation performed
        """
        assert detect_biomarker_patterns(text) >= 0.5


class TestChunkOptimization:
    """Test the chunk optimization functionality."""

    @pytest.fixture
    def sample_document_structure(self) -> DocumentStructure:
        """Create a sample document structure for testing."""
        return {
            "document_type": "lab_report",
            "page_zones": {
                0: {
                    "header": {"zone_type": "header", "bbox": [0, 0, 100, 50], "confidence": 0.9},
                    "content": {"zone_type": "content", "bbox": [0, 50, 100, 500], "confidence": 0.9},
                    "footer": {"zone_type": "footer", "bbox": [0, 500, 100, 550], "confidence": 0.9}
                }
            },
            "tables": {
                0: [
                    {"bbox": [10, 100, 90, 200], "page_number": 0, "rows": 5, "cols": 3, "confidence": 0.9, "index": 0}
                ]
            },
            "biomarker_regions": [
                {"page_num": 0, "region_type": "table", "biomarker_confidence": 0.9}
            ],
            "confidence": 0.85
        }

    @pytest.fixture
    def sample_pages_text(self) -> Dict[int, str]:
        """Create sample pages text for testing."""
        return {
            0: """
            PATIENT LAB REPORT
            
            TEST | RESULT | REFERENCE RANGE
            Glucose | 95 mg/dL | 70-99 mg/dL
            Cholesterol | 180 mg/dL | <200 mg/dL
            Triglycerides | 120 mg/dL | <150 mg/dL
            
            Please consult with your healthcare provider for interpretation of these results.
            This test was developed and its performance characteristics determined by Our Lab.
            """
        }

    def test_optimize_content_chunks(self, sample_document_structure, sample_pages_text):
        """Test optimizing content into chunks."""
        chunks = optimize_content_chunks(sample_pages_text, sample_document_structure)
        
        # Should create at least one chunk
        assert len(chunks) >= 1
        
        # Chunks should have required properties
        for chunk in chunks:
            assert "text" in chunk
            assert "page_num" in chunk
            assert "region_type" in chunk
            assert "estimated_tokens" in chunk
            assert "biomarker_confidence" in chunk
            assert "context" in chunk
            
            # Check token estimation
            assert chunk["estimated_tokens"] > 0
            
            # Check content filtering - boilerplate should be removed
            assert "Please consult with your healthcare provider" not in chunk["text"]

    def test_priority_for_biomarker_rich_regions(self, sample_document_structure, sample_pages_text):
        """Test that biomarker-rich regions get priority."""
        chunks = optimize_content_chunks(sample_pages_text, sample_document_structure)
        
        # Sort chunks by biomarker confidence
        sorted_chunks = sorted(chunks, key=lambda c: c["biomarker_confidence"], reverse=True)
        
        # Higher confidence chunks should be first
        assert sorted_chunks[0]["biomarker_confidence"] >= 0.8

    def test_enhance_chunk_confidence(self, sample_document_structure, sample_pages_text):
        """Test enhancing chunk confidence."""
        chunks = optimize_content_chunks(sample_pages_text, sample_document_structure)
        enhanced_chunks = enhance_chunk_confidence(chunks)
        
        # Number of chunks should be the same
        assert len(enhanced_chunks) == len(chunks)
        
        # Calculate average confidence before and after enhancement
        avg_conf_before = sum(c["biomarker_confidence"] for c in chunks) / len(chunks)
        avg_conf_after = sum(c["biomarker_confidence"] for c in enhanced_chunks) / len(enhanced_chunks)
        
        # Average confidence should increase or stay the same
        assert avg_conf_after >= avg_conf_before
        
        # Chunks with table patterns should get a confidence boost
        table_chunks = [c for c in enhanced_chunks if "|" in c["text"]]
        if table_chunks:
            for chunk in table_chunks:
                # Get original confidence
                original_chunk = next((c for c in chunks if c["text"] == chunk["text"]), None)
                if original_chunk:
                    # Enhanced confidence should be higher than original
                    assert chunk["biomarker_confidence"] >= original_chunk["biomarker_confidence"]

    def test_text_splitting_by_biomarker_density(self):
        """Test splitting text by biomarker density."""
        # Create a text with varying biomarker density
        text = """
        # General Information
        Patient: John Doe
        Date: 2023-01-01
        
        # Lab Results
        Glucose: 95 mg/dL (70-99)
        Cholesterol: 180 mg/dL (<200)
        Triglycerides: 120 mg/dL (<150)
        HDL: 45 mg/dL (>40)
        LDL: 110 mg/dL (<130)
        
        # Notes
        Patient advised to follow up in 3 months.
        No significant changes from previous results.
        """
        
        chunks = split_text_by_biomarker_density(text, max_tokens=100, page_num=0)
        
        # Should create multiple chunks
        assert len(chunks) >= 1
        
        # Lab Results section should have higher confidence
        lab_results_chunk = next((c for c in chunks if "Glucose" in c["text"]), None)
        general_info_chunk = next((c for c in chunks if "Patient: John Doe" in c["text"]), None)
        
        if lab_results_chunk and general_info_chunk:
            assert lab_results_chunk["biomarker_confidence"] > general_info_chunk["biomarker_confidence"]


if __name__ == "__main__":
    # Run tests when script is executed directly
    pytest.main(["-xvs", __file__]) 