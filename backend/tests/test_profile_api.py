"""
Test script for the profile management API endpoints.
"""
import unittest
import requests
import json
import uuid
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

class TestProfileAPI(unittest.TestCase):
    """Test cases for the profile management API."""
    
    def setUp(self):
        """Set up test case - create a test profile."""
        self.profile_data = {
            "name": f"Test Profile {uuid.uuid4()}",
            "date_of_birth": "1990-01-01T00:00:00",
            "gender": "other",
            "patient_id": f"TEST-{uuid.uuid4()}"
        }
        
        # Create a test profile
        response = requests.post(
            f"{BASE_URL}/profiles/",
            json=self.profile_data
        )
        
        self.assertEqual(response.status_code, 201, "Failed to create test profile")
        self.profile = response.json()
        self.profile_id = self.profile["id"]
    
    def tearDown(self):
        """Clean up after test - delete the test profile."""
        # Delete the test profile
        response = requests.delete(f"{BASE_URL}/profiles/{self.profile_id}")
        self.assertEqual(response.status_code, 204, "Failed to delete test profile")
    
    def test_create_profile(self):
        """Test creating a new profile."""
        # Create a new profile
        new_profile_data = {
            "name": f"New Test Profile {uuid.uuid4()}",
            "date_of_birth": "1995-05-05T00:00:00",
            "gender": "female",
            "patient_id": f"TEST-{uuid.uuid4()}"
        }
        
        response = requests.post(
            f"{BASE_URL}/profiles/",
            json=new_profile_data
        )
        
        self.assertEqual(response.status_code, 201, "Failed to create profile")
        
        # Verify the response data
        profile = response.json()
        self.assertEqual(profile["name"], new_profile_data["name"])
        self.assertEqual(profile["gender"], new_profile_data["gender"])
        self.assertEqual(profile["patient_id"], new_profile_data["patient_id"])
        
        # Clean up - delete the created profile
        delete_response = requests.delete(f"{BASE_URL}/profiles/{profile['id']}")
        self.assertEqual(delete_response.status_code, 204, "Failed to delete profile")
    
    def test_get_profile(self):
        """Test getting a profile by ID."""
        response = requests.get(f"{BASE_URL}/profiles/{self.profile_id}")
        
        self.assertEqual(response.status_code, 200, "Failed to get profile")
        
        # Verify the response data
        profile = response.json()
        self.assertEqual(profile["id"], self.profile_id)
        self.assertEqual(profile["name"], self.profile_data["name"])
        self.assertEqual(profile["gender"], self.profile_data["gender"])
        self.assertEqual(profile["patient_id"], self.profile_data["patient_id"])
    
    def test_update_profile(self):
        """Test updating a profile."""
        # Update data
        update_data = {
            "name": f"Updated Profile {uuid.uuid4()}",
            "gender": "male"
        }
        
        response = requests.put(
            f"{BASE_URL}/profiles/{self.profile_id}",
            json=update_data
        )
        
        self.assertEqual(response.status_code, 200, "Failed to update profile")
        
        # Verify the response data
        profile = response.json()
        self.assertEqual(profile["id"], self.profile_id)
        self.assertEqual(profile["name"], update_data["name"])
        self.assertEqual(profile["gender"], update_data["gender"])
        # Patient ID should remain unchanged
        self.assertEqual(profile["patient_id"], self.profile_data["patient_id"])
    
    def test_list_profiles(self):
        """Test listing all profiles."""
        response = requests.get(f"{BASE_URL}/profiles/")
        
        self.assertEqual(response.status_code, 200, "Failed to list profiles")
        
        # Verify the response structure
        data = response.json()
        self.assertIn("profiles", data)
        self.assertIn("total", data)
        
        # Verify our test profile is in the list
        profile_ids = [p["id"] for p in data["profiles"]]
        self.assertIn(self.profile_id, profile_ids)
    
    def test_search_profiles(self):
        """Test searching for profiles."""
        # Extract a unique part of the name to search for
        search_term = self.profile_data["name"].split()[-1]
        
        response = requests.get(f"{BASE_URL}/profiles/?search={search_term}")
        
        self.assertEqual(response.status_code, 200, "Failed to search profiles")
        
        # Verify the response structure
        data = response.json()
        self.assertIn("profiles", data)
        
        # Verify our test profile is in the search results
        profile_ids = [p["id"] for p in data["profiles"]]
        self.assertIn(self.profile_id, profile_ids)

if __name__ == "__main__":
    unittest.main() 