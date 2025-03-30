import pytest
from unittest.mock import patch, MagicMock
import json

# Assuming the service is in app.services.metadata_parser
from app.services.metadata_parser import extract_metadata_with_claude

# Sample Claude API response for metadata
SAMPLE_CLAUDE_RESPONSE_TEXT = '''
{{
  "metadata": {{
    "lab_name": "Test Lab Inc.",
    "report_date": "2023-10-27",
    "patient_name": "John Doe",
    "patient_dob": "1990-01-15",
    "patient_gender": "Male",
    "patient_id": "MRN12345",
    "patient_age": "33"
  }}
}}
'''

# Sample response with some nulls
SAMPLE_CLAUDE_RESPONSE_NULLS = '''
{{
  "metadata": {{
    "lab_name": "Another Lab",
    "report_date": null,
    "patient_name": "Jane Smith",
    "patient_dob": "1985-03-20",
    "patient_gender": "F",
    "patient_id": null,
    "patient_age": null
  }}
}}
'''

# Sample response with no metadata found
SAMPLE_CLAUDE_RESPONSE_EMPTY = '''
{{
  "metadata": {{}}
}}
'''

# Malformed JSON response
SAMPLE_CLAUDE_RESPONSE_MALFORMED = '''
Here is the metadata:
{{
  "metadata": {{
    "lab_name": "Bad Lab",
    "patient_name": "Test User"
    "report_date": "2023-11-01" // Missing comma
  }}
}}
Oops, forgot something.
'''


@pytest.fixture
def mock_anthropic_client():
    """Fixture to mock the Anthropic client and its response."""
    with patch('app.services.metadata_parser.anthropic.Anthropic') as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        yield mock_client # Yield the mocked client instance

@patch('app.services.metadata_parser._preprocess_text_for_claude', return_value="Processed Sample Text")
@patch('app.services.metadata_parser._repair_json', side_effect=lambda x: x) # Assume repair passes through initially
def test_extract_metadata_success(mock_repair, mock_preprocess, mock_anthropic_client):
    """Test successful metadata extraction with a valid Claude response."""
    # Configure the mock response
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = SAMPLE_CLAUDE_RESPONSE_TEXT
    mock_anthropic_client.messages.create.return_value = mock_response
    
    # Call the function
    metadata = extract_metadata_with_claude("Sample PDF Text", "test.pdf - page 1")
    
    # Assertions
    mock_preprocess.assert_called_once_with("Sample PDF Text")
    mock_anthropic_client.messages.create.assert_called_once()
    assert metadata == {
        "lab_name": "Test Lab Inc.",
        "report_date": "2023-10-27",
        "patient_name": "John Doe",
        "patient_dob": "1990-01-15",
        "patient_gender": "Male",
        "patient_id": "MRN12345",
        "patient_age": "33"
    }
    mock_repair.assert_called() # Repair should be called even if JSON is good

@patch('app.services.metadata_parser._preprocess_text_for_claude', return_value="Processed Sample Text")
@patch('app.services.metadata_parser._repair_json', side_effect=lambda x: x)
def test_extract_metadata_with_nulls(mock_repair, mock_preprocess, mock_anthropic_client):
    """Test extraction when Claude response contains null values."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = SAMPLE_CLAUDE_RESPONSE_NULLS
    mock_anthropic_client.messages.create.return_value = mock_response
    
    metadata = extract_metadata_with_claude("Sample PDF Text", "test_nulls.pdf - page 1")
    
    assert metadata == {
        "lab_name": "Another Lab",
        "patient_name": "Jane Smith",
        "patient_dob": "1985-03-20",
        "patient_gender": "F" # Note: nulls are filtered out
    }
    mock_repair.assert_called_once()

@patch('app.services.metadata_parser._preprocess_text_for_claude', return_value="Processed Sample Text")
@patch('app.services.metadata_parser._repair_json', side_effect=lambda x: x)
def test_extract_metadata_empty(mock_repair, mock_preprocess, mock_anthropic_client):
    """Test extraction when Claude response returns an empty metadata object."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = SAMPLE_CLAUDE_RESPONSE_EMPTY
    mock_anthropic_client.messages.create.return_value = mock_response
    
    metadata = extract_metadata_with_claude("Sample PDF Text", "test_empty.pdf - page 1")
    
    assert metadata == {}
    mock_repair.assert_called_once()

@patch('app.services.metadata_parser._preprocess_text_for_claude', return_value="Processed Sample Text")
@patch('app.services.metadata_parser._repair_json') # Let repair mock handle the fix
def test_extract_metadata_malformed_json_repair(mock_repair, mock_preprocess, mock_anthropic_client):
    """Test extraction when Claude response is malformed but repairable."""
    # Simulate _repair_json fixing the malformed JSON
    repaired_json_str = '{"metadata": {"lab_name": "Bad Lab", "patient_name": "Test User", "report_date": "2023-11-01"}}'
    mock_repair.return_value = repaired_json_str
    
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = SAMPLE_CLAUDE_RESPONSE_MALFORMED
    mock_anthropic_client.messages.create.return_value = mock_response
    
    metadata = extract_metadata_with_claude("Sample PDF Text", "test_malformed.pdf - page 1")
    
    assert metadata == {
        "lab_name": "Bad Lab",
        "patient_name": "Test User",
        "report_date": "2023-11-01"
    }
    # Check that repair was called with the extracted (malformed) JSON part
    json_match = re.search(r'({[\s\S]*})', SAMPLE_CLAUDE_RESPONSE_MALFORMED)
    expected_malformed_json = json_match.group(1) if json_match else ""
    mock_repair.assert_called_once_with(expected_malformed_json)

@patch('app.services.metadata_parser._preprocess_text_for_claude', return_value="Processed Sample Text")
@patch('app.services.metadata_parser._repair_json', side_effect=json.JSONDecodeError("Mock Repair Failed", "doc", 0))
def test_extract_metadata_unrepairable_json(mock_repair, mock_preprocess, mock_anthropic_client):
    """Test extraction when Claude response is unrepairable JSON."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock()]
    mock_response.content[0].text = "Invalid JSON String {{ not json"
    mock_anthropic_client.messages.create.return_value = mock_response
    
    metadata = extract_metadata_with_claude("Sample PDF Text", "test_unrepairable.pdf - page 1")
    
    # Should return empty dict if JSON parsing fails even after repair attempt
    assert metadata == {}
    mock_repair.assert_called() # Repair should still be called

@patch('app.services.metadata_parser._preprocess_text_for_claude', return_value="Processed Sample Text")
def test_extract_metadata_api_error(mock_preprocess, mock_anthropic_client):
    """Test extraction when the Claude API call raises an exception."""
    # Simulate an API error
    mock_anthropic_client.messages.create.side_effect = anthropic.APIError("Test API Error")
    
    metadata = extract_metadata_with_claude("Sample PDF Text", "test_api_error.pdf - page 1")
    
    # Should return empty dict on API error
    assert metadata == {} 