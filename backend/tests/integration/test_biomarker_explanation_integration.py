"""
Integration tests for the biomarker explanation service.
These tests make actual API calls to the Claude API and should be run with caution.
"""
import pytest
import os
from app.services.biomarker_explanation_service import explain_biomarker

# Skip all tests if no API key is set
pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set"
)

@pytest.mark.integration
@pytest.mark.asyncio
class TestBiomarkerExplanationIntegration:
    """Integration tests for biomarker explanation service."""
    
    async def test_normal_glucose_explanation(self):
        """Test getting explanation for normal glucose value."""
        general_exp, specific_exp = await explain_biomarker(
            biomarker_name="Glucose",
            value=95.0,
            unit="mg/dL",
            reference_range="70-99",
            status="normal"
        )
        
        # Verify response structure and content
        assert "ABOUT_THIS_BIOMARKER:" in general_exp
        assert "glucose" in general_exp.lower()
        assert "YOUR_RESULTS:" in specific_exp
        assert "95" in specific_exp
        assert "DISCLAIMER:" in specific_exp
    
    async def test_high_cholesterol_explanation(self):
        """Test getting explanation for high cholesterol value."""
        general_exp, specific_exp = await explain_biomarker(
            biomarker_name="Total Cholesterol",
            value=250.0,
            unit="mg/dL",
            reference_range="125-200",
            status="high"
        )
        
        # Verify response structure and content
        assert "ABOUT_THIS_BIOMARKER:" in general_exp
        assert "cholesterol" in general_exp.lower()
        assert "YOUR_RESULTS:" in specific_exp
        assert "250" in specific_exp
        assert "high" in specific_exp.lower()
        assert "DISCLAIMER:" in specific_exp
    
    async def test_low_iron_explanation(self):
        """Test getting explanation for low iron value."""
        general_exp, specific_exp = await explain_biomarker(
            biomarker_name="Iron",
            value=30.0,
            unit="µg/dL",
            reference_range="60-170",
            status="low"
        )
        
        # Verify response structure and content
        assert "ABOUT_THIS_BIOMARKER:" in general_exp
        assert "iron" in general_exp.lower()
        assert "YOUR_RESULTS:" in specific_exp
        assert "30" in specific_exp
        assert "low" in specific_exp.lower()
        assert "DISCLAIMER:" in specific_exp 