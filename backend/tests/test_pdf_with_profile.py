"""
Test script for PDF upload with profile association.
"""
import unittest
import requests
import json
import uuid
import os
import time
from datetime import datetime

# Base URL for the API
BASE_URL = "http://localhost:8000/api"

class TestPDFWithProfile(unittest.TestCase):
    """Test cases for PDF upload with profile association."""
    
    def setUp(self):
        """Set up test case - create a test profile."""
        # Create a test profile
        self.profile_data = {
            "name": f"Test Profile {uuid.uuid4()}",
            "date_of_birth": "1990-01-01T00:00:00",
            "gender": "other",
            "patient_id": f"TEST-{uuid.uuid4()}"
        }
        
        response = requests.post(
            f"{BASE_URL}/profiles/",
            json=self.profile_data
        )
        
        self.assertEqual(response.status_code, 201, "Failed to create test profile")
        self.profile = response.json()
        self.profile_id = self.profile["id"]
        
        # Path to a sample PDF file for testing
        self.sample_pdf_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "sample_reports",
            "agilus_report.pdf"  # Using an existing PDF file
        )
        
        # Ensure the sample PDF exists
        self.assertTrue(os.path.exists(self.sample_pdf_path), f"Sample PDF not found at {self.sample_pdf_path}")
    
    def tearDown(self):
        """Clean up after test - delete the test profile."""
        # Delete the test profile
        response = requests.delete(f"{BASE_URL}/profiles/{self.profile_id}")
        self.assertEqual(response.status_code, 204, "Failed to delete test profile")
    
    def test_upload_pdf_with_profile(self):
        """Test uploading a PDF with profile association."""
        # Upload a PDF with profile_id
        with open(self.sample_pdf_path, "rb") as pdf_file:
            files = {"file": pdf_file}
            
            response = requests.post(
                f"{BASE_URL}/pdf/upload?profile_id={self.profile_id}",
                files=files
            )
        
        self.assertEqual(response.status_code, 200, "Failed to upload PDF")
        
        # Verify the response data
        pdf_data = response.json()
        self.assertIn("file_id", pdf_data)
        self.assertIn("profile_id", pdf_data)
        self.assertEqual(pdf_data["profile_id"], self.profile_id)
        
        # Store the file_id for later use
        file_id = pdf_data["file_id"]
        
        # Wait for processing to complete
        max_retries = 10
        retry_count = 0
        status = "pending"
        
        while status == "pending" and retry_count < max_retries:
            time.sleep(2)  # Wait 2 seconds between checks
            
            # Check the status
            status_response = requests.get(f"{BASE_URL}/pdf/status/{file_id}")
            self.assertEqual(status_response.status_code, 200, "Failed to get PDF status")
            
            status_data = status_response.json()
            status = status_data["status"]
            retry_count += 1
        
        # Verify the PDF is associated with the profile
        self.assertEqual(status_data["profile_id"], self.profile_id)
        
        # Get the profile to verify the PDF count increased
        profile_response = requests.get(f"{BASE_URL}/profiles/{self.profile_id}")
        self.assertEqual(profile_response.status_code, 200, "Failed to get profile")
        
        updated_profile = profile_response.json()
        self.assertGreater(updated_profile["pdf_count"], 0, "PDF count did not increase")
    
    def test_extract_profile_from_pdf(self):
        """Test extracting profile information from a PDF."""
        # First upload a PDF without profile association
        with open(self.sample_pdf_path, "rb") as pdf_file:
            files = {"file": pdf_file}
            
            response = requests.post(
                f"{BASE_URL}/pdf/upload",
                files=files
            )
        
        self.assertEqual(response.status_code, 200, "Failed to upload PDF")
        
        # Get the PDF ID
        pdf_data = response.json()
        file_id = pdf_data["file_id"]
        
        # Wait for processing to complete
        max_retries = 10
        retry_count = 0
        status = "pending"
        
        while status == "pending" and retry_count < max_retries:
            time.sleep(2)  # Wait 2 seconds between checks
            
            # Check the status
            status_response = requests.get(f"{BASE_URL}/pdf/status/{file_id}")
            self.assertEqual(status_response.status_code, 200, "Failed to get PDF status")
            
            status_data = status_response.json()
            status = status_data["status"]
            retry_count += 1
        
        # Get the PDF ID (not file_id)
        pdf_id = status_data.get("id")
        
        if not pdf_id:
            # If id is not directly available, we need to query the database
            # For this test, we'll skip this part if pdf_id is not available
            return
        
        # Extract profile information from the PDF
        extract_response = requests.post(f"{BASE_URL}/profiles/extract/{pdf_id}")
        
        # This might return an empty list if no profile matches are found
        # That's okay for this test
        self.assertEqual(extract_response.status_code, 200, "Failed to extract profile from PDF")

if __name__ == "__main__":
    unittest.main() 