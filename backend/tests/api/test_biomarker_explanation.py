"""
Tests for the biomarker explanation API endpoint.
"""
import json
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.biomarker_model import Biomarker
from app.services.llm_service import ExplanationCache

client = TestClient(app)

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    # Setup mock biomarker
    mock_biomarker = MagicMock()
    mock_biomarker.id = 1
    mock_biomarker.name = "Glucose"
    mock_biomarker.value = 95.0
    mock_biomarker.unit = "mg/dL"
    mock_biomarker.reference_range_low = 70.0
    mock_biomarker.reference_range_high = 99.0
    db.query.return_value.filter.return_value.first.return_value = mock_biomarker
    
    return db

@pytest.fixture
def explanation_payload():
    """Return a sample explanation request payload."""
    return {
        "name": "Glucose",
        "value": 95.0,
        "unit": "mg/dL",
        "reference_range": "70-99",
        "is_abnormal": False
    }

@patch("app.api.routes.biomarker_routes.explanation_cache", ExplanationCache())
@patch("app.api.routes.biomarker_routes.explain_biomarker")
@patch("app.api.routes.biomarker_routes.get_db")
def test_explain_biomarker_with_ai(mock_get_db, mock_explain_biomarker, mock_db, explanation_payload):
    """Test that the API endpoint returns a valid explanation."""
    # Setup mock database
    mock_get_db.return_value = mock_db
    
    # Setup mock LLM response
    mock_explain_biomarker.return_value = AsyncMock(
        return_value=(
            "Glucose is a sugar that serves as the primary source of energy for the body. It comes from carbohydrates in foods and is essential for brain function.",
            "Your glucose level of 95 mg/dL is within the normal reference range of 70-99 mg/dL. This suggests your body is effectively regulating blood sugar levels."
        )
    )()
    
    # Make the request
    response = client.post("/api/biomarkers/1/explain", json=explanation_payload)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["biomarker_id"] == 1
    assert data["name"] == "Glucose"
    assert "general_explanation" in data
    assert "specific_explanation" in data
    assert data["from_cache"] is False
    
    # Verify LLM was called with correct parameters
    mock_explain_biomarker.assert_called_once_with(
        biomarker_name="Glucose",
        value=95.0,
        unit="mg/dL",
        reference_range="70-99",
        status="normal"
    )

@patch("app.api.routes.biomarker_routes.explanation_cache")
@patch("app.api.routes.biomarker_routes.get_db")
def test_explain_biomarker_with_cache(mock_get_db, mock_cache, mock_db, explanation_payload):
    """Test that cached explanations are returned when available."""
    # Setup mock database
    mock_get_db.return_value = mock_db
    
    # Setup mock cache
    mock_cache.get_general_explanation.return_value = (
        "Glucose is a sugar that serves as the primary source of energy for the body."
    )
    mock_cache.get_specific_explanation.return_value = (
        "Your glucose level of 95 mg/dL is within the normal reference range."
    )
    
    # Make the request
    response = client.post("/api/biomarkers/1/explain", json=explanation_payload)
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["from_cache"] is True
    assert data["general_explanation"] == "Glucose is a sugar that serves as the primary source of energy for the body."

@patch("app.api.routes.biomarker_routes.get_db")
def test_explain_nonexistent_biomarker(mock_get_db, explanation_payload):
    """Test that a 404 is returned when the biomarker doesn't exist."""
    # Setup mock database to return no biomarker
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_get_db.return_value = mock_db
    
    # Make the request
    response = client.post("/api/biomarkers/999/explain", json=explanation_payload)
    
    # Assertions
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

@patch("app.api.routes.biomarker_routes.explain_biomarker")
@patch("app.api.routes.biomarker_routes.get_db")
def test_explain_biomarker_api_error(mock_get_db, mock_explain_biomarker, mock_db, explanation_payload):
    """Test that server errors are handled properly."""
    # Setup mock database
    mock_get_db.return_value = mock_db
    
    # Setup mock LLM to raise an exception
    mock_explain_biomarker.return_value = AsyncMock(side_effect=Exception("API Error"))()
    
    # Make the request
    response = client.post("/api/biomarkers/1/explain", json=explanation_payload)
    
    # Assertions
    assert response.status_code == 500
    assert "error" in response.json()["detail"].lower() 