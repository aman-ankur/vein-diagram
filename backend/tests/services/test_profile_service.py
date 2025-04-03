import pytest
from unittest.mock import MagicMock, patch, call
from uuid import uuid4, UUID
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

# Assuming models and schemas are accessible via app path
from app.models.profile_model import Profile
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF
from app.schemas.profile_schema import ProfileMergeRequest
from app.services.profile_service import merge_profiles

# --- Test Fixtures ---

@pytest.fixture
def mock_db_session():
    """Provides a mocked SQLAlchemy Session."""
    session = MagicMock(spec=Session)
    # Mock the nested transaction context manager
    session.begin_nested = MagicMock()
    session.begin_nested.return_value.__enter__ = MagicMock()
    session.begin_nested.return_value.__exit__ = MagicMock()
    # Mock query capabilities
    session.query = MagicMock()
    session.execute = MagicMock() # For update/delete statements
    return session

@pytest.fixture
def target_profile():
    """Provides a sample target Profile object."""
    return Profile(
        id=uuid4(), 
        name="Target Profile", 
        favorite_biomarkers=["Glucose", "HDL"],
        created_at=datetime.utcnow(),
        last_modified=datetime.utcnow()
    )

@pytest.fixture
def source_profile_1():
    """Provides a sample source Profile object."""
    return Profile(
        id=uuid4(), 
        name="Source Profile 1", 
        favorite_biomarkers=["LDL"],
        created_at=datetime.utcnow(),
        last_modified=datetime.utcnow()
    )

@pytest.fixture
def source_profile_2():
    """Provides a sample source Profile object."""
    return Profile(
        id=uuid4(), 
        name="Source Profile 2", 
        favorite_biomarkers=["Triglycerides"],
        created_at=datetime.utcnow(),
        last_modified=datetime.utcnow()
    )

# --- Test Cases ---

def test_merge_profiles_success(mock_db_session, target_profile, source_profile_1, source_profile_2):
    """Tests a successful merge of two source profiles into a target profile."""
    
    # Arrange
    source_ids = [source_profile_1.id, source_profile_2.id]
    target_id = target_profile.id
    merge_request = ProfileMergeRequest(source_profile_ids=source_ids, target_profile_id=target_id)

    # Mock DB query results more directly
    mock_target_query = MagicMock()
    mock_target_query.first.return_value = target_profile
    
    mock_source_query = MagicMock()
    mock_source_query.all.return_value = [source_profile_1, source_profile_2]

    mock_biomarker_query = MagicMock()
    mock_biomarker_query.join.return_value = mock_biomarker_query
    mock_biomarker_query.filter.return_value = mock_biomarker_query
    mock_biomarker_query.order_by.return_value = mock_biomarker_query
    mock_biomarker_query.all.return_value = [] # No duplicates for this test

    # Configure the main query mock
    def query_side_effect(model):
        if model == Profile:
            # Crude way to distinguish target vs source query based on call order in this test
            if mock_db_session.query.call_count == 1: # First call is for target
                return MagicMock(filter=MagicMock(return_value=mock_target_query))
            elif mock_db_session.query.call_count == 2: # Second call is for sources
                return MagicMock(filter=MagicMock(return_value=mock_source_query))
        elif model == Biomarker.id: # Third call is for biomarker dedupe
             return mock_biomarker_query
        # Fallback for any other unexpected query
        return MagicMock() 

    mock_db_session.query.side_effect = query_side_effect
    mock_db_session.query.call_count = 0 # Reset count for side effect logic
    
    # Mock execute results for update/delete rowcounts
    mock_db_session.execute.side_effect = [
        MagicMock(rowcount=5), # Biomarker update
        MagicMock(rowcount=2), # PDF update
        MagicMock(rowcount=0), # Duplicate biomarker delete (none found)
        MagicMock(rowcount=2)  # Profile delete
    ]

    # Act
    merge_profiles(db=mock_db_session, merge_request=merge_request)

    # Assert
    # Check validation queries (Target profile + Source profiles = 2 calls minimum)
    # The deduplication query might not run if no biomarkers are found after re-association in the test setup.
    assert mock_db_session.query.call_count >= 2 # Target + Source queries minimum
    
    # Check that execute was called for the updates and deletes
    # Expecting 4 execute calls: Biomarker Update, PDF Update, Duplicate Delete, Profile Delete
    assert mock_db_session.execute.call_count == 4 
    
    # Check transaction management
    mock_db_session.begin_nested.assert_called_once()
    mock_db_session.begin_nested.return_value.__enter__.assert_called_once()
    mock_db_session.begin_nested.return_value.__exit__.assert_called_once()


def test_merge_profiles_target_not_found(mock_db_session, source_profile_1):
    """Tests error handling when the target profile does not exist."""
    
    # Arrange
    source_ids = [source_profile_1.id]
    target_id = uuid4() # Non-existent target
    merge_request = ProfileMergeRequest(source_profile_ids=source_ids, target_profile_id=target_id)

    # Mock DB query results specifically for this test
    # Mock the chain: query(Profile).filter(...).first() -> None
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        merge_profiles(db=mock_db_session, merge_request=merge_request)
    
    assert exc_info.value.status_code == 404
    assert f"Target profile {target_id} not found" in exc_info.value.detail
    mock_db_session.begin_nested.assert_called_once() # Should still enter transaction context


def test_merge_profiles_source_not_found(mock_db_session, target_profile, source_profile_1):
    """Tests error handling when one of the source profiles does not exist."""
    
    # Arrange
    missing_source_id = uuid4()
    source_ids = [source_profile_1.id, missing_source_id]
    target_id = target_profile.id
    merge_request = ProfileMergeRequest(source_profile_ids=source_ids, target_profile_id=target_id)

    # Mock DB query results specifically for this test
    mock_target_query = MagicMock()
    mock_target_query.first.return_value = target_profile # Target exists

    mock_source_query = MagicMock()
    mock_source_query.all.return_value = [source_profile_1] # Return only one source, simulating missing one

    # Configure the main query mock using side_effect for sequence
    
    # Mock the chain query(Profile).filter(...).first() -> target_profile
    mock_filter_target = MagicMock()
    mock_filter_target.first.return_value = target_profile
    
    # Mock the chain query(Profile).filter(...).all() -> [source_profile_1]
    mock_filter_source = MagicMock()
    mock_filter_source.all.return_value = [source_profile_1] # Incomplete list

    # Set up side_effect on the query mock itself
    mock_db_session.query.side_effect = [
        MagicMock(filter=MagicMock(return_value=mock_filter_target)), # First call to query(Profile)
        MagicMock(filter=MagicMock(return_value=mock_filter_source))  # Second call to query(Profile)
    ]

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        merge_profiles(db=mock_db_session, merge_request=merge_request)
    
    assert exc_info.value.status_code == 404
    assert f"Source profiles not found: {{{missing_source_id}}}" in exc_info.value.detail # Check for the missing ID
    mock_db_session.begin_nested.assert_called_once()


def test_merge_profiles_target_in_source(mock_db_session, target_profile, source_profile_1):
    """Tests error handling when the target profile ID is also in the source list."""
    
    # Arrange
    source_ids = [source_profile_1.id, target_profile.id] # Target is included in source
    target_id = target_profile.id
    merge_request = ProfileMergeRequest(source_profile_ids=source_ids, target_profile_id=target_id)

    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        merge_profiles(db=mock_db_session, merge_request=merge_request)
    
    assert exc_info.value.status_code == 400
    assert "Target profile cannot be one of the source profiles" in exc_info.value.detail
    mock_db_session.begin_nested.assert_not_called() # Should fail before entering transaction


# TODO: Add more tests:
# - Test deduplication logic with actual duplicate data
# - Test metadata merging (if implemented)
# - Test transaction rollback on error during update/delete
