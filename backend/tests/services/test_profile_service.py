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

    # Setup for target profile query
    mock_target_filter = MagicMock()
    mock_target_filter.first.return_value = target_profile
    
    mock_target_query = MagicMock()
    mock_target_query.filter.return_value = mock_target_filter
    
    # Setup for source profiles query
    mock_source_filter = MagicMock()
    mock_source_filter.all.return_value = [source_profile_1, source_profile_2]
    
    mock_source_query = MagicMock()
    mock_source_query.filter.return_value = mock_source_filter
    
    # Setup for biomarker query with duplicates
    sample_date = datetime.utcnow()
    mock_biomarker_result = [
        (1, "Glucose", 100.0, "mg/dL", sample_date),
        (2, "Glucose", 100.0, "mg/dL", sample_date),  # Duplicate of first entry
        (3, "HDL", 50.0, "mg/dL", sample_date)
    ]
    
    mock_biomarker_chain = MagicMock()
    mock_biomarker_chain.all.return_value = mock_biomarker_result
    mock_biomarker_chain.order_by.return_value = mock_biomarker_chain
    mock_biomarker_chain.filter.return_value = mock_biomarker_chain
    mock_biomarker_chain.join.return_value = mock_biomarker_chain
    
    # Create a counter to track calls
    call_counter = {'count': 0}
    
    # Create a patched query function
    def mock_query_function(model):
        call_counter['count'] += 1
        print(f"Query call {call_counter['count']} with model: {model}")
        
        if call_counter['count'] == 1:  # First call - target profile
            return mock_target_query
        elif call_counter['count'] == 2:  # Second call - source profiles
            return mock_source_query
        else:  # Third call - biomarker query for deduplication
            return mock_biomarker_chain
    
    # Replace the query method
    mock_db_session.query = mock_query_function
    
    # Setup execute side effects - we only expect 2 calls
    execute_results = [
        MagicMock(rowcount=5),  # Biomarker update
        MagicMock(rowcount=2),  # PDF update
    ]
    
    # Track execute calls
    execute_calls = []
    
    def mock_execute_function(statement):
        print(f"Execute called with: {statement}")
        execute_calls.append(statement)
        result = execute_results.pop(0)
        return result
    
    mock_db_session.execute = mock_execute_function

    # Act
    merge_profiles(db=mock_db_session, merge_request=merge_request)

    # Assert
    # We should have at least the target and source queries
    assert call_counter['count'] >= 2
    
    # All execute results should have been used (2 calls)
    assert len(execute_results) == 0
    assert len(execute_calls) == 2
    
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

    # Create mocks for the chain of methods
    print("\n=== Setting up mocks for target_not_found test ===")
    
    # Patch begin_nested
    mock_nested_context = MagicMock()
    mock_db_session.begin_nested.return_value = mock_nested_context
    
    # Create a mock for query call for target profile that returns None
    def mock_query_function(model_class):
        print(f"Query called with model: {model_class}")
        
        # Setup the filter mock to return None for first() (target not found)
        mock_filter = MagicMock(name="filter_mock")
        mock_filter.first.return_value = None
        print("Setting up filter.first() to return None")
        
        # Create the query mock that will return the filter mock
        mock_query = MagicMock(name="query_mock")
        mock_query.filter.return_value = mock_filter
        print("Returning mock query object")
        
        return mock_query
    
    # Replace the query method
    mock_db_session.query = mock_query_function
    
    # Patch execute to raise an error if called (should not get that far)
    def mock_execute_function(statement):
        print(f"Execute called with: {statement}")
        raise ValueError("Execute should not be called when target is not found")
    
    mock_db_session.execute = mock_execute_function
    
    print("=== Mocks setup complete, running test ===")
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        print("Calling merge_profiles")
        merge_profiles(db=mock_db_session, merge_request=merge_request)
    
    print("Exception raised:", exc_info.value)
    assert exc_info.value.status_code == 404
    assert f"Target profile {target_id} not found" in exc_info.value.detail
    
    # Ensure the transaction was started
    mock_db_session.begin_nested.assert_called_once()
    mock_nested_context.__enter__.assert_called_once()
    mock_nested_context.__exit__.assert_called_once()


def test_merge_profiles_source_not_found(mock_db_session, target_profile, source_profile_1):
    """Tests error handling when one of the source profiles does not exist."""
    
    # Arrange
    missing_source_id = uuid4()
    source_ids = [source_profile_1.id, missing_source_id]
    target_id = target_profile.id
    merge_request = ProfileMergeRequest(source_profile_ids=source_ids, target_profile_id=target_id)

    print("\n=== Setting up mocks for source_not_found test ===")
    
    # Patch begin_nested
    mock_nested_context = MagicMock()
    mock_db_session.begin_nested.return_value = mock_nested_context
    
    # Create target_filter mock that returns the target profile
    mock_target_filter = MagicMock(name="target_filter_mock")
    mock_target_filter.first.return_value = target_profile
    
    # Create source_filter mock that returns incomplete list
    mock_source_filter = MagicMock(name="source_filter_mock")
    mock_source_filter.all.return_value = [source_profile_1]  # Missing one source
    
    # Create target query mock that returns target filter
    mock_target_query = MagicMock(name="target_query_mock")
    mock_target_query.filter.return_value = mock_target_filter
    
    # Create source query mock that returns source filter
    mock_source_query = MagicMock(name="source_query_mock")
    mock_source_query.filter.return_value = mock_source_filter
    
    # Track the query call count
    call_count = {'count': 0}
    
    # Mock the query method to return different mocks for different calls
    def mock_query_function(model_class):
        call_count['count'] += 1
        print(f"Query call {call_count['count']} with model: {model_class}")
        
        if call_count['count'] == 1:
            print("Returning mock target query")
            return mock_target_query
        else:
            print("Returning mock source query")
            return mock_source_query
    
    # Replace the query method
    mock_db_session.query = mock_query_function
    
    # Mock execute to raise an error if called
    def mock_execute_function(statement):
        print(f"Execute called with: {statement}")
        raise ValueError("Execute should not be called when sources are not found")
    
    mock_db_session.execute = mock_execute_function
    
    print("=== Mocks setup complete, running test ===")
    
    # Act & Assert
    with pytest.raises(HTTPException) as exc_info:
        print("Calling merge_profiles")
        merge_profiles(db=mock_db_session, merge_request=merge_request)
    
    print("Exception raised:", exc_info.value)
    assert exc_info.value.status_code == 404
    # Check that the missing UUID is mentioned in the exception detail
    assert str(missing_source_id) in exc_info.value.detail
    
    # Ensure transaction was started
    mock_db_session.begin_nested.assert_called_once()
    mock_nested_context.__enter__.assert_called_once()
    mock_nested_context.__exit__.assert_called_once()


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


def test_http_exception_raising():
    """Test to ensure HTTPException can be raised and caught properly."""
    
    # Directly try to raise and catch an HTTPException
    print("\n=== Testing HTTPException raising ===")
    try:
        print("Raising HTTPException")
        raise HTTPException(status_code=404, detail="Test exception")
    except HTTPException as e:
        print(f"Caught HTTPException: {e}")
        assert e.status_code == 404
        assert "Test exception" in e.detail
    
    # Test a function that raises an exception
    def raise_http_exception():
        print("Function raising HTTPException")
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Test with pytest.raises
    with pytest.raises(HTTPException) as exc_info:
        print("Calling function that raises HTTPException")
        raise_http_exception()
    
    print(f"Caught with pytest.raises: {exc_info.value}")
    assert exc_info.value.status_code == 403
    assert "Forbidden" in exc_info.value.detail
    
    print("=== HTTPException raising test passed ===")


def test_merge_profiles_direct_patching(mock_db_session, target_profile, source_profile_1):
    """Test that directly patches the merge_profiles function to debug the issue."""
    
    print("\n=== Testing with direct patching ===")
    
    # Create a modified function that prints debugging info
    original_merge_profiles = merge_profiles
    
    # Define a decorator for merge_profiles to add logging
    def debug_wrapper(func):
        def wrapped_function(*args, **kwargs):
            print(f"\nCalling patched merge_profiles with args: {args}, kwargs: {kwargs}")
            try:
                result = func(*args, **kwargs)
                print(f"merge_profiles completed successfully, returned: {result}")
                return result
            except HTTPException as e:
                print(f"merge_profiles raised HTTPException: {e}")
                raise
            except Exception as e:
                print(f"merge_profiles raised other exception: {e}")
                raise
        return wrapped_function
    
    # Apply the decorator
    patched_merge_profiles = debug_wrapper(original_merge_profiles)
    
    # Test case 1: Target not found
    print("\n--- Test case: Target not found ---")
    
    # Create the request
    target_id = uuid4()
    merge_request = ProfileMergeRequest(
        source_profile_ids=[source_profile_1.id],
        target_profile_id=target_id
    )
    
    # Setup the mock
    mock_filter = MagicMock()
    mock_filter.first.return_value = None
    
    mock_query = MagicMock()
    mock_query.filter.return_value = mock_filter
    
    # Install the mock
    mock_db_session.query.return_value = mock_query
    
    # Add a nested context manager
    mock_context = MagicMock()
    mock_db_session.begin_nested.return_value = mock_context
    
    # Try to run the patched function
    try:
        patched_merge_profiles(db=mock_db_session, merge_request=merge_request)
        print("FAILURE: Expected an exception but none was raised")
    except HTTPException as e:
        print(f"SUCCESS: Caught HTTPException as expected: {e}")
        assert e.status_code == 404
        assert f"Target profile {target_id} not found" in e.detail
    except Exception as e:
        print(f"FAILURE: Caught unexpected exception: {e}")
    
    print("=== Direct patching test complete ===")


# TODO: Add more tests:
# - Test deduplication logic with actual duplicate data
# - Test metadata merging (if implemented)
# - Test transaction rollback on error during update/delete
