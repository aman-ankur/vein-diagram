"""
Tests for the profile matcher service.
"""
import pytest
from datetime import datetime
from uuid import uuid4
from app.services.profile_matcher import (
    preprocess_profile_metadata,
    calculate_profile_match_score,
    find_matching_profiles,
    create_profile_from_metadata
)
from app.models.profile_model import Profile
from unittest.mock import MagicMock, patch

@pytest.fixture
def db_session():
    """
    Create a mock database session for testing.
    """
    session = MagicMock()
    session.add = MagicMock()
    session.commit = MagicMock()
    session.refresh = MagicMock()
    session.rollback = MagicMock()
    return session

def test_preprocess_profile_metadata():
    """Test the preprocess_profile_metadata function."""
    # Test with complete metadata
    metadata = {
        "patient_name": " John Doe ",
        "patient_dob": "1990-01-01",
        "patient_gender": "M",
        "patient_id": " P12345 "
    }
    
    processed = preprocess_profile_metadata(metadata)
    
    assert processed["patient_name"] == "john doe"
    assert isinstance(processed["patient_dob"], datetime)
    assert processed["patient_gender"] == "male"
    assert processed["patient_id"] == "P12345"
    
    # Test with partial metadata
    metadata = {
        "patient_name": "Jane Doe",
        "patient_gender": "female"
    }
    
    processed = preprocess_profile_metadata(metadata)
    
    assert processed["patient_name"] == "jane doe"
    assert processed["patient_gender"] == "female"
    assert "patient_dob" not in processed
    assert "patient_id" not in processed

def test_create_profile_from_metadata(db_session):
    """Test creating a profile from metadata."""
    # Test with complete metadata
    metadata = {
        "patient_name": "John Doe",
        "patient_dob": "1990-01-01",
        "patient_gender": "male",
        "patient_id": "P12345"
    }
    
    # Mock the Profile creation
    mock_profile = MagicMock()
    mock_profile.id = str(uuid4())
    mock_profile.name = "John Doe"
    db_session.refresh.side_effect = lambda x: None
    
    # Patch the Profile constructor
    with patch('app.services.profile_matcher.Profile', return_value=mock_profile) as mock_profile_class:
        profile = create_profile_from_metadata(db_session, metadata)
        
        # Verify the Profile was created with correct parameters
        mock_profile_class.assert_called_once()
        _, kwargs = mock_profile_class.call_args
        assert kwargs["name"] == "John Doe"
        assert "date_of_birth" in kwargs
        assert kwargs["gender"] == "male"
        assert kwargs["patient_id"] == "P12345"
        assert kwargs.get("user_id") is None
        
        # Verify profile was added and committed
        db_session.add.assert_called_once_with(mock_profile)
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once_with(mock_profile)
        
        # Verify the function returned the mock profile
        assert profile is mock_profile

def test_create_profile_from_metadata_with_user_id(db_session):
    """Test creating a profile from metadata with a user_id."""
    # Test with complete metadata and user_id
    metadata = {
        "patient_name": "John Doe",
        "patient_dob": "1990-01-01",
        "patient_gender": "male",
        "patient_id": "P12345"
    }
    user_id = "test-user-123"
    
    # Mock the Profile creation
    mock_profile = MagicMock()
    mock_profile.id = str(uuid4())
    mock_profile.name = "John Doe"
    db_session.refresh.side_effect = lambda x: None
    
    # Patch the Profile constructor
    with patch('app.services.profile_matcher.Profile', return_value=mock_profile) as mock_profile_class:
        profile = create_profile_from_metadata(db_session, metadata, user_id)
        
        # Verify the Profile was created with correct parameters
        mock_profile_class.assert_called_once()
        _, kwargs = mock_profile_class.call_args
        assert kwargs["name"] == "John Doe"
        assert "date_of_birth" in kwargs
        assert kwargs["gender"] == "male"
        assert kwargs["patient_id"] == "P12345"
        assert kwargs["user_id"] == user_id
        
        # Verify profile was added and committed
        db_session.add.assert_called_once_with(mock_profile)
        db_session.commit.assert_called_once()
        db_session.refresh.assert_called_once_with(mock_profile)
        
        # Verify the function returned the mock profile
        assert profile is mock_profile

def test_create_profile_from_metadata_with_minimal_data(db_session):
    """Test creating a profile with minimal metadata."""
    # Test with minimal metadata
    metadata = {
        "patient_name": "Jane Smith"
    }
    
    # Mock the Profile creation
    mock_profile = MagicMock()
    mock_profile.id = str(uuid4())
    mock_profile.name = "Jane Smith"
    db_session.refresh.side_effect = lambda x: None
    
    # Patch the Profile constructor
    with patch('app.services.profile_matcher.Profile', return_value=mock_profile) as mock_profile_class:
        profile = create_profile_from_metadata(db_session, metadata)
        
        # Verify the Profile was created with correct parameters
        mock_profile_class.assert_called_once()
        _, kwargs = mock_profile_class.call_args
        assert kwargs["name"] == "Jane Smith"
        assert kwargs.get("date_of_birth") is None
        assert kwargs.get("gender") is None
        assert kwargs.get("patient_id") is None
        
        # Verify the function returned the mock profile
        assert profile is mock_profile

def test_create_profile_from_metadata_error_handling(db_session):
    """Test error handling when creating a profile fails."""
    metadata = {
        "patient_name": "Error Test"
    }
    
    # Make db.commit raise an exception
    db_session.commit.side_effect = Exception("Database error")
    
    # Execute the function
    profile = create_profile_from_metadata(db_session, metadata)
    
    # Verify rollback was called
    db_session.rollback.assert_called_once()
    
    # Verify function returned None
    assert profile is None

# More tests for the other functions can be added here 