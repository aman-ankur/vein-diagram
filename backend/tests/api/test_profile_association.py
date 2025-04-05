"""
Tests for the profile association API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import uuid
from datetime import datetime

from app.models.pdf_model import PDF
from app.models.profile_model import Profile

@pytest.fixture
def test_pdf(db_session):
    """Create a test PDF entry in the database."""
    pdf = PDF(
        file_id=str(uuid.uuid4()),
        filename="test.pdf",
        file_path="/path/to/test.pdf",
        extracted_text="Test PDF content",
        status="processed"
    )
    db_session.add(pdf)
    db_session.commit()
    db_session.refresh(pdf)
    return pdf

@pytest.fixture
def test_profile(db_session):
    """Create a test profile entry in the database."""
    profile = Profile(
        name="Test Profile",
        date_of_birth=datetime(1990, 1, 1),
        gender="male",
        patient_id="TEST123",
        user_id="test-user-id"
    )
    db_session.add(profile)
    db_session.commit()
    db_session.refresh(profile)
    return profile

@pytest.mark.asyncio
@patch('app.api.routes.profile_routes.extract_metadata_with_claude')
async def test_associate_pdf_with_existing_profile(mock_extract, client, db_session, test_pdf, test_profile):
    """Test associating a PDF with an existing profile."""
    # Mock the authentication middleware
    with patch('app.api.routes.profile_routes.get_current_user', return_value={"user_id": "test-user-id"}):
        # Arrange
        request_data = {
            "pdf_id": test_pdf.file_id,
            "profile_id": str(test_profile.id),
            "create_new_profile": False,
            "user_id": "test-user-id"
        }
        
        # Act
        response = client.post("/api/profiles/associate", json=request_data)
        
        # Assert
        assert response.status_code == 200
        assert response.json()["id"] == str(test_profile.id)
        # Verify the PDF was associated with the profile
        db_session.refresh(test_pdf)
        assert test_pdf.profile_id == test_profile.id

@pytest.mark.asyncio
@patch('app.api.routes.profile_routes.extract_metadata_with_claude')
async def test_create_profile_from_pdf(mock_extract, client, db_session, test_pdf):
    """Test creating a new profile from PDF metadata."""
    # Mock the metadata extraction
    metadata = {
        "lab_name": "Test Lab",
        "report_date": "2023-01-15",
        "patient_name": "John Doe",
        "patient_dob": "1995-05-05",
        "patient_gender": "male",
        "patient_id": "P12345",
        "patient_age": "28"
    }
    mock_extract.return_value = metadata
    
    # Mock the authentication middleware
    with patch('app.api.routes.profile_routes.get_current_user', return_value={"user_id": "test-user-id"}):
        # Arrange
        request_data = {
            "pdf_id": test_pdf.file_id,
            "create_new_profile": True,
            "user_id": "test-user-id"
        }
        
        # Act
        response = client.post("/api/profiles/associate", json=request_data)
        
        # Assert
        assert response.status_code == 200
        profile_data = response.json()
        assert profile_data["name"] == "John Doe"
        assert profile_data["gender"] == "male"
        assert profile_data["patient_id"] == "P12345"
        
        # Verify the profile was created in the database
        profile_id = profile_data["id"]
        profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
        assert profile is not None
        assert profile.user_id == "test-user-id"
        
        # Verify the PDF was associated with the new profile
        db_session.refresh(test_pdf)
        assert test_pdf.profile_id == profile.id

@pytest.mark.asyncio
@patch('app.api.routes.profile_routes.extract_metadata_with_claude')
async def test_associate_with_metadata_updates(mock_extract, client, db_session, test_pdf):
    """Test creating a profile with metadata updates."""
    # Mock the metadata extraction
    metadata = {
        "lab_name": "Test Lab",
        "patient_name": "Original Name",
        "patient_gender": "female"
    }
    mock_extract.return_value = metadata
    
    # Mock the authentication middleware
    with patch('app.api.routes.profile_routes.get_current_user', return_value={"user_id": "test-user-id"}):
        # Arrange
        request_data = {
            "pdf_id": test_pdf.file_id,
            "create_new_profile": True,
            "metadata_updates": {
                "patient_name": "Updated Name"
            },
            "user_id": "test-user-id"
        }
        
        # Act
        response = client.post("/api/profiles/associate", json=request_data)
        
        # Assert
        assert response.status_code == 200
        profile_data = response.json()
        assert profile_data["name"] == "Updated Name"  # Name should be updated
        assert profile_data["gender"] == "female"      # Original gender should be preserved
        
        # Verify the profile was created with the updated metadata
        profile_id = profile_data["id"]
        profile = db_session.query(Profile).filter(Profile.id == profile_id).first()
        assert profile is not None
        assert profile.name == "Updated Name"
        assert profile.gender == "female"
        assert profile.user_id == "test-user-id" 