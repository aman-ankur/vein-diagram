import pytest
import jwt
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import get_current_user, get_optional_current_user, AuthError
from uuid import UUID

client = TestClient(app)

# Helper function to create test tokens
def create_test_token(user_id="test_user_id", email="test@example.com", expired=False, missing_sub=False):
    """Create a test JWT token with different configurations"""
    # Current timestamp or expired timestamp
    exp_time = int(time.time()) - 3600 if expired else int(time.time()) + 3600
    
    payload = {
        "exp": exp_time,
        "email": email
    }
    
    # Add sub claim unless testing missing sub
    if not missing_sub:
        payload["sub"] = user_id
        
    # Use a test secret
    return jwt.encode(payload, "test_secret", algorithm="HS256")

@pytest.fixture(autouse=True)
def cleanup_test_profiles():
    """Cleanup test profiles before each test"""
    token = create_test_token(user_id="test_user_id")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get all profiles for test user
    response = client.get("/api/profiles/", headers=headers)
    if response.status_code == 200:
        profiles = response.json()["profiles"]
        for profile in profiles:
            client.delete(f"/api/profiles/{profile['id']}", headers=headers)
    
    yield

# Test cases for unauthenticated requests
def test_protected_endpoint_without_token():
    """Test accessing a protected endpoint without a token"""
    response = client.get("/api/profiles/")
    assert response.status_code == 403  # FastAPI's security middleware returns 403 for missing token
    assert "Not authenticated" in response.json()["detail"]

# Test cases for invalid tokens
def test_protected_endpoint_with_invalid_token():
    """Test accessing a protected endpoint with an invalid token"""
    headers = {"Authorization": "Bearer invalid_token_format"}
    response = client.get("/api/profiles/", headers=headers)
    assert response.status_code == 401

def test_protected_endpoint_with_expired_token():
    """Test accessing a protected endpoint with an expired token"""
    token = create_test_token(expired=True)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/profiles/", headers=headers)
    # In development mode, expired tokens are still accepted
    assert response.status_code == 200

def test_protected_endpoint_with_missing_sub():
    """Test accessing a protected endpoint with token missing sub claim"""
    token = create_test_token(missing_sub=True)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/profiles/", headers=headers)
    assert response.status_code == 401

# Test case for valid token in development mode
def test_protected_endpoint_with_valid_token_dev_mode():
    """Test accessing a protected endpoint with a valid token in dev mode"""
    token = create_test_token(user_id="test_user_id")
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/profiles/", headers=headers)
    # In development mode with mock JWT_SECRET, this should succeed
    assert response.status_code == 200

# Test CRUD operations with authentication
def test_profile_crud_with_auth():
    """Test profile CRUD operations with authentication"""
    token = create_test_token(user_id="test_user_id")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test profile
    profile_data = {
        "name": "Test User",
        "date_of_birth": "1990-01-01T00:00:00Z",
        "gender": "male",
        "patient_id": "TEST123"
    }
    
    # Test profile creation
    create_response = client.post(
        "/api/profiles/", 
        json=profile_data,
        headers=headers
    )
    assert create_response.status_code == 201
    created_profile = create_response.json()
    profile_id = created_profile["id"]
    
    # Test get profile
    get_response = client.get(f"/api/profiles/{profile_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Test User"
    
    # Test partial update - update only name
    update_data = {"name": "Updated Test User"}
    update_response = client.put(f"/api/profiles/{profile_id}", json=update_data, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated Test User"
    assert update_response.json()["gender"] == "male"  # Other fields should remain unchanged
    
    # Test full update
    full_update_data = {
        "name": "Fully Updated User",
        "date_of_birth": "1991-02-02T00:00:00Z",
        "gender": "female",
        "patient_id": "TEST456"
    }
    full_update_response = client.put(f"/api/profiles/{profile_id}", json=full_update_data, headers=headers)
    assert full_update_response.status_code == 200
    updated_profile = full_update_response.json()
    assert updated_profile["name"] == "Fully Updated User"
    assert updated_profile["gender"] == "female"
    assert updated_profile["patient_id"] == "TEST456"
    
    # Test update with invalid profile ID
    invalid_update_response = client.put(
        f"/api/profiles/invalid-uuid", 
        json=update_data,
        headers=headers
    )
    assert invalid_update_response.status_code == 422  # FastAPI returns 422 for invalid UUID format
    error_detail = invalid_update_response.json()["detail"][0]
    assert error_detail["type"] == "uuid_parsing"  # Check error type
    assert "input should be a valid uuid" in error_detail["msg"].lower()  # Check error message
    
    # Test delete profile
    delete_response = client.delete(f"/api/profiles/{profile_id}", headers=headers)
    assert delete_response.status_code == 204
    
    # Verify profile is deleted
    get_deleted_response = client.get(f"/api/profiles/{profile_id}", headers=headers)
    assert get_deleted_response.status_code == 404

def test_profile_favorite_biomarkers():
    """Test updating favorite biomarkers for a profile"""
    token = create_test_token(user_id="test_user_id")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a test profile
    profile_data = {
        "name": "Test User",
        "date_of_birth": "1990-01-01T00:00:00Z",
        "gender": "male",
        "patient_id": "TEST123"
    }
    create_response = client.post("/api/profiles/", json=profile_data, headers=headers)
    assert create_response.status_code == 201
    profile_id = create_response.json()["id"]
    
    # Test updating favorite biomarkers
    update_data = {
        "favorite_biomarkers": ["Glucose", "Cholesterol", "HDL"]
    }
    update_response = client.put(f"/api/profiles/{profile_id}", json=update_data, headers=headers)
    assert update_response.status_code == 200
    assert update_response.json()["favorite_biomarkers"] == ["Glucose", "Cholesterol", "HDL"]
    
    # Test updating with empty list
    empty_update = {"favorite_biomarkers": []}
    empty_update_response = client.put(f"/api/profiles/{profile_id}", json=empty_update, headers=headers)
    assert empty_update_response.status_code == 200
    assert empty_update_response.json()["favorite_biomarkers"] == []
    
    # Clean up
    client.delete(f"/api/profiles/{profile_id}", headers=headers)

def test_profile_list_pagination():
    """Test profile listing with pagination"""
    token = create_test_token(user_id="test_user_id")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create multiple test profiles
    profile_ids = []
    for i in range(5):
        profile_data = {
            "name": f"Test User {i}",
            "date_of_birth": "1990-01-01T00:00:00Z",
            "gender": "male",
            "patient_id": f"TEST{i}"
        }
        response = client.post("/api/profiles/", json=profile_data, headers=headers)
        assert response.status_code == 201
        profile_ids.append(response.json()["id"])
    
    # Test default pagination
    list_response = client.get("/api/profiles/", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["profiles"]) == 5
    assert list_response.json()["total"] == 5
    
    # Test with limit
    limited_response = client.get("/api/profiles/?limit=2", headers=headers)
    assert limited_response.status_code == 200
    assert len(limited_response.json()["profiles"]) == 2
    assert limited_response.json()["total"] == 5
    
    # Test with offset
    offset_response = client.get("/api/profiles/?skip=2&limit=2", headers=headers)
    assert offset_response.status_code == 200
    assert len(offset_response.json()["profiles"]) == 2
    assert offset_response.json()["total"] == 5
    
    # Test search by name
    search_response = client.get("/api/profiles/?search=User 1", headers=headers)
    assert search_response.status_code == 200
    assert len(search_response.json()["profiles"]) == 1
    assert search_response.json()["profiles"][0]["name"] == "Test User 1"
    
    # Clean up
    for profile_id in profile_ids:
        client.delete(f"/api/profiles/{profile_id}", headers=headers)

# Test user isolation - users can only access their own data
def test_user_data_isolation():
    """Test that users can only access their own data"""
    # Create first user and profile
    user1_token = create_test_token(user_id="user_1")
    headers1 = {"Authorization": f"Bearer {user1_token}"}
    
    profile1_data = {
        "name": "User One",
        "date_of_birth": "1990-01-01T00:00:00Z",
        "gender": "male",
        "patient_id": "USER1_ID"
    }
    profile1_response = client.post("/api/profiles/", json=profile1_data, headers=headers1)
    assert profile1_response.status_code == 201  # FastAPI returns 201 for successful creation
    profile1_id = profile1_response.json()["id"]
    
    # Create second user and profile
    user2_token = create_test_token(user_id="user_2")
    headers2 = {"Authorization": f"Bearer {user2_token}"}
    
    profile2_data = {
        "name": "User Two",
        "date_of_birth": "1992-02-02T00:00:00Z",
        "gender": "female",
        "patient_id": "USER2_ID"
    }
    profile2_response = client.post("/api/profiles/", json=profile2_data, headers=headers2)
    assert profile2_response.status_code == 201  # FastAPI returns 201 for successful creation
    profile2_id = profile2_response.json()["id"]
    
    # User 1 should not be able to access User 2's profile
    user1_accessing_user2 = client.get(f"/api/profiles/{profile2_id}", headers=headers1)
    assert user1_accessing_user2.status_code == 404  # Should return not found, not forbidden
    
    # User 2 should not be able to access User 1's profile
    user2_accessing_user1 = client.get(f"/api/profiles/{profile1_id}", headers=headers2)
    assert user2_accessing_user1.status_code == 404
    
    # Clean up
    client.delete(f"/api/profiles/{profile1_id}", headers=headers1)
    client.delete(f"/api/profiles/{profile2_id}", headers=headers2)

# Test optional authentication
def test_optional_authentication():
    """Test endpoints with optional authentication"""
    # Test health check endpoint which should be public
    public_response = client.get("/health")
    assert public_response.status_code == 200
    assert public_response.json()["status"] == "healthy"
    
    # Test with authentication
    token = create_test_token()
    headers = {"Authorization": f"Bearer {token}"}
    auth_response = client.get("/health", headers=headers)
    assert auth_response.status_code == 200
    assert auth_response.json()["status"] == "healthy"
