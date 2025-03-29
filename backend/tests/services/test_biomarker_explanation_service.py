"""
Tests for the biomarker explanation service.
"""
import pytest
import httpx
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.services.biomarker_explanation_service import (
    ExplanationCache,
    explain_biomarker,
    GENERAL_EXPLANATION_TTL,
    SPECIFIC_EXPLANATION_TTL
)

# Test data
MOCK_BIOMARKER = {
    "name": "Glucose",
    "value": 95.0,
    "unit": "mg/dL",
    "reference_range": "70-99",
    "status": "normal"
}

MOCK_CLAUDE_RESPONSE = {
    "content": [{
        "text": """ABOUT_THIS_BIOMARKER:
        Glucose is a type of sugar that serves as the primary energy source for your body's cells.
        It's carefully regulated by insulin and other hormones to maintain optimal levels.
        Normal levels indicate your body is effectively managing blood sugar.

        YOUR_RESULTS:
        Your glucose level of 95 mg/dL is within the normal range of 70-99 mg/dL.
        This suggests your body is maintaining healthy blood sugar control.
        
        DISCLAIMER:
        This information is educational only and not medical advice.
        Please discuss your results with your healthcare provider."""
    }]
}

@pytest.fixture
def explanation_cache():
    """Create a fresh explanation cache for each test."""
    return ExplanationCache()

class TestExplanationCache:
    """Test suite for the ExplanationCache class."""
    
    def test_cache_storage_and_retrieval(self, explanation_cache):
        """Test basic storage and retrieval of explanations."""
        biomarker_name = "Glucose"
        cache_key = "glucose_95_normal"
        general_exp = "General explanation"
        specific_exp = "Specific explanation"
        
        explanation_cache.add_explanation(
            biomarker_name,
            cache_key,
            general_exp,
            specific_exp
        )
        
        assert explanation_cache.get_general_explanation(biomarker_name) == general_exp
        assert explanation_cache.get_specific_explanation(cache_key) == specific_exp
    
    def test_cache_expiration(self, explanation_cache):
        """Test that cached items expire after their TTL."""
        biomarker_name = "Glucose"
        cache_key = "glucose_95_normal"
        
        # Add explanations
        explanation_cache.add_explanation(
            biomarker_name,
            cache_key,
            "General explanation",
            "Specific explanation"
        )
        
        # Simulate time passing beyond TTL
        future_time = datetime.utcnow().timestamp() + SPECIFIC_EXPLANATION_TTL + 1
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.fromtimestamp(future_time)
            
            assert explanation_cache.get_specific_explanation(cache_key) is None
            
        future_time = datetime.utcnow().timestamp() + GENERAL_EXPLANATION_TTL + 1
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = datetime.fromtimestamp(future_time)
            
            assert explanation_cache.get_general_explanation(biomarker_name) is None

@pytest.mark.asyncio
class TestExplainBiomarker:
    """Test suite for the explain_biomarker function."""
    
    async def test_successful_explanation(self):
        """Test successful biomarker explanation generation."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = MOCK_CLAUDE_RESPONSE
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            general_exp, specific_exp = await explain_biomarker(
                MOCK_BIOMARKER["name"],
                MOCK_BIOMARKER["value"],
                MOCK_BIOMARKER["unit"],
                MOCK_BIOMARKER["reference_range"],
                MOCK_BIOMARKER["status"]
            )
            
            assert "Glucose is a type of sugar" in general_exp
            assert "Your glucose level of 95 mg/dL" in specific_exp
    
    async def test_api_error_handling(self):
        """Test handling of API errors."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            general_exp, specific_exp = await explain_biomarker(
                MOCK_BIOMARKER["name"],
                MOCK_BIOMARKER["value"],
                MOCK_BIOMARKER["unit"],
                MOCK_BIOMARKER["reference_range"],
                MOCK_BIOMARKER["status"]
            )
            
            assert "temporarily unavailable" in general_exp
            assert "temporarily unavailable" in specific_exp
    
    async def test_timeout_handling(self):
        """Test handling of timeout errors."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
            
            general_exp, specific_exp = await explain_biomarker(
                MOCK_BIOMARKER["name"],
                MOCK_BIOMARKER["value"],
                MOCK_BIOMARKER["unit"],
                MOCK_BIOMARKER["reference_range"],
                MOCK_BIOMARKER["status"]
            )
            
            assert "temporarily unavailable" in general_exp
            assert "temporarily unavailable" in specific_exp
    
    async def test_missing_api_key(self):
        """Test behavior when API key is not set."""
        with patch.dict('os.environ', {'ANTHROPIC_API_KEY': ''}):
            general_exp, specific_exp = await explain_biomarker(
                MOCK_BIOMARKER["name"],
                MOCK_BIOMARKER["value"],
                MOCK_BIOMARKER["unit"],
                MOCK_BIOMARKER["reference_range"],
                MOCK_BIOMARKER["status"]
            )
            
            assert "measures the level of glucose" in general_exp.lower()
            assert f"Your {MOCK_BIOMARKER['name']} value is" in specific_exp 