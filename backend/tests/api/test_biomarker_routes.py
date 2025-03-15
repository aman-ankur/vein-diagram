import pytest
from unittest.mock import MagicMock, patch
import json
from datetime import datetime
from sqlalchemy.orm import Session

# Import the client from test_client.py
from tests.utils.test_client import client
from app.db.database import get_db
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF

# Test data
test_biomarker = {
    "name": "Glucose",
    "original_name": "Glucose",
    "value": 95.0,
    "original_value": 95.0,
    "unit": "mg/dL",
    "original_unit": "mg/dL",
    "reference_range_low": 70.0,
    "reference_range_high": 99.0,
    "category": "Metabolic",
    "is_abnormal": False
}

# Override the database dependency
@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = MagicMock(spec=Session)
    
    # Replace the app dependency
    app.dependency_overrides[get_db] = lambda: db
    
    yield db
    
    # Remove the override after the test
    app.dependency_overrides = {}

@pytest.fixture
def sample_biomarkers():
    """Create sample biomarker data for testing"""
    pdf = PDF(
        id=1,
        file_id="test_file_id",
        filename="test.pdf",
        status="processed",
        upload_date=datetime.datetime.utcnow()
    )
    
    biomarkers = [
        Biomarker(
            id=1,
            pdf_id=1,
            name="Glucose",
            value=95.0,
            unit="mg/dL",
            original_name="Glucose",
            original_value="95",
            original_unit="mg/dL",
            reference_range_low=70.0,
            reference_range_high=99.0,
            reference_range_text="70-99",
            category="Metabolic",
            is_abnormal=False,
            pdf=pdf
        ),
        Biomarker(
            id=2,
            pdf_id=1,
            name="Total Cholesterol",
            value=210.0,
            unit="mg/dL",
            original_name="Total Cholesterol",
            original_value="210",
            original_unit="mg/dL",
            reference_range_low=None,
            reference_range_high=200.0,
            reference_range_text="< 200",
            category="Lipid",
            is_abnormal=True,
            pdf=pdf
        ),
        Biomarker(
            id=3,
            pdf_id=1,
            name="Vitamin D, 25-OH",
            value=32.0,
            unit="ng/mL",
            original_name="25-Hydroxyvitamin D",
            original_value="32",
            original_unit="ng/mL",
            reference_range_low=30.0,
            reference_range_high=100.0,
            reference_range_text="30-100",
            category="Vitamin",
            is_abnormal=False,
            pdf=pdf
        )
    ]
    
    return biomarkers

def test_get_biomarkers_by_file_id(mock_db, sample_biomarkers):
    """Test retrieving biomarkers for a specific PDF file"""
    # Setup mock query
    pdf = sample_biomarkers[0].pdf
    mock_db.query.return_value.filter.return_value.first.return_value = pdf
    
    # Setup biomarkers query
    biomarker_query = MagicMock()
    mock_db.query.return_value.filter.return_value = biomarker_query
    biomarker_query.all.return_value = sample_biomarkers
    
    # Make the request
    response = client.get("/api/pdf/test_file_id/biomarkers")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Glucose"
    assert data[1]["name"] == "Total Cholesterol"
    assert data[2]["name"] == "Vitamin D, 25-OH"

def test_get_biomarkers_by_file_id_not_found(mock_db):
    """Test retrieving biomarkers when the PDF file is not found"""
    # Setup mock query to return None
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Make the request
    response = client.get("/api/pdf/nonexistent_id/biomarkers")
    
    # Verify the response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_all_biomarkers(mock_db, sample_biomarkers):
    """Test retrieving all biomarkers"""
    # Setup the mock query builder chain
    query_builder = MagicMock()
    mock_db.query.return_value = query_builder
    
    # Setup filter method (for category filter)
    filtered_query = MagicMock()
    query_builder.filter.return_value = filtered_query
    
    # Setup order_by, offset, limit chain
    ordered_query = MagicMock()
    query_builder.order_by.return_value = ordered_query
    offset_query = MagicMock()
    ordered_query.offset.return_value = offset_query
    limit_query = MagicMock()
    offset_query.limit.return_value = limit_query
    
    # Setup final result
    limit_query.all.return_value = sample_biomarkers
    
    # Make the request
    response = client.get("/api/biomarkers")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    
    # Check that the order_by, offset, limit methods were called
    query_builder.order_by.assert_called_once()
    ordered_query.offset.assert_called_once_with(0)
    offset_query.limit.assert_called_once_with(100)

def test_get_all_biomarkers_with_category_filter(mock_db, sample_biomarkers):
    """Test retrieving biomarkers filtered by category"""
    # Filter to only return Lipid biomarkers
    lipid_biomarkers = [b for b in sample_biomarkers if b.category == "Lipid"]
    
    # Setup the mock query builder chain
    query_builder = MagicMock()
    mock_db.query.return_value = query_builder
    
    # Setup filter method
    filtered_query = MagicMock()
    query_builder.filter.return_value = filtered_query
    
    # Setup order_by, offset, limit chain
    ordered_query = MagicMock()
    filtered_query.order_by.return_value = ordered_query
    offset_query = MagicMock()
    ordered_query.offset.return_value = offset_query
    limit_query = MagicMock()
    offset_query.limit.return_value = limit_query
    
    # Setup final result
    limit_query.all.return_value = lipid_biomarkers
    
    # Make the request
    response = client.get("/api/biomarkers?category=Lipid")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Total Cholesterol"
    assert data[0]["category"] == "Lipid"
    
    # Verify the filter was called with the right category
    query_builder.filter.assert_called_once()

def test_get_biomarker_categories(mock_db, sample_biomarkers):
    """Test retrieving all unique biomarker categories"""
    # Setup distinct query to return rows with category values
    distinct_query = MagicMock()
    mock_db.query.return_value.distinct.return_value = distinct_query
    
    # Return rows as tuples with a single value (as SQLAlchemy would)
    distinct_query.all.return_value = [
        ("Metabolic",),
        ("Lipid",),
        ("Vitamin",)
    ]
    
    # Make the request
    response = client.get("/api/biomarkers/categories")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert sorted(data) == ["Lipid", "Metabolic", "Vitamin"]

def test_search_biomarkers(mock_db, sample_biomarkers):
    """Test searching for biomarkers by name"""
    # Setup the filter query to return matching biomarkers
    query_builder = MagicMock()
    mock_db.query.return_value = query_builder
    
    # Setup filter method
    filtered_query = MagicMock()
    query_builder.filter.return_value = filtered_query
    
    # For this test, assume we're searching for "cholesterol"
    matching_biomarkers = [b for b in sample_biomarkers if "cholesterol" in b.name.lower()]
    
    # Setup result
    filtered_query.limit.return_value = matching_biomarkers
    
    # Make the request
    response = client.get("/api/biomarkers/search?query=cholesterol")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Total Cholesterol"

def test_get_biomarker_by_id(mock_db, sample_biomarkers):
    """Test retrieving a specific biomarker by ID"""
    # Setup the query to return a specific biomarker
    mock_db.query.return_value.filter.return_value.first.return_value = sample_biomarkers[0]
    
    # Make the request
    response = client.get("/api/biomarkers/1")
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Glucose"
    assert data["value"] == 95.0
    assert data["unit"] == "mg/dL"

def test_get_biomarker_by_id_not_found(mock_db):
    """Test retrieving a biomarker that doesn't exist"""
    # Setup the query to return None
    mock_db.query.return_value.filter.return_value.first.return_value = None
    
    # Make the request
    response = client.get("/api/biomarkers/999")
    
    # Verify the response
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower() 