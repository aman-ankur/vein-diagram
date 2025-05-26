#!/usr/bin/env python3
"""
Integration tests for the Smart Status Endpoint

Tests the PDF status endpoint's ability to detect and auto-correct
inconsistent PDF processing states.
"""

import pytest
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.pdf_model import PDF
from app.models.biomarker_model import Biomarker
from app.db.database import get_db

# Configure test logging
logging.basicConfig(level=logging.INFO)

class TestSmartStatusEndpoint:
    """Test suite for smart status endpoint functionality."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_pdf_stuck_with_biomarkers(self):
        """Create a PDF stuck in pending status but with biomarkers."""
        return PDF(
            id=1,
            file_id="stuck-pdf-with-biomarkers",
            filename="stuck_report.pdf",
            file_path="/uploads/stuck_report.pdf",
            status="pending",
            upload_date=datetime.utcnow() - timedelta(hours=2),
            processed_date=None,
            parsing_confidence=None,
            profile_id=None
        )
    
    @pytest.fixture
    def sample_pdf_processing_with_biomarkers(self):
        """Create a PDF stuck in processing status but with biomarkers."""
        return PDF(
            id=2,
            file_id="processing-pdf-with-biomarkers",
            filename="processing_report.pdf",
            file_path="/uploads/processing_report.pdf",
            status="processing",
            upload_date=datetime.utcnow() - timedelta(hours=1),
            processed_date=None,
            parsing_confidence=None,
            profile_id=None
        )
    
    @pytest.fixture
    def sample_pdf_correctly_processed(self):
        """Create a correctly processed PDF."""
        return PDF(
            id=3,
            file_id="correctly-processed-pdf",
            filename="correct_report.pdf",
            file_path="/uploads/correct_report.pdf",
            status="processed",
            upload_date=datetime.utcnow() - timedelta(hours=3),
            processed_date=datetime.utcnow() - timedelta(minutes=30),
            parsing_confidence=0.85,
            profile_id=None
        )

    def test_status_endpoint_auto_corrects_pending_with_biomarkers(self, client, mock_db_session, sample_pdf_stuck_with_biomarkers):
        """Test that status endpoint auto-corrects pending PDF with biomarkers."""
        
        # Override the dependency
        def override_get_db():
            return mock_db_session
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Mock PDF query to return stuck PDF
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.first.return_value = sample_pdf_stuck_with_biomarkers
        
        # Mock biomarker count query to return 8 biomarkers
        mock_biomarker_query = Mock()
        mock_biomarker_query.filter.return_value.count.return_value = 8
        
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        # Make request to status endpoint
        response = client.get("/api/pdf/status/stuck-pdf-with-biomarkers")
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        # Check that PDF status was corrected
        assert sample_pdf_stuck_with_biomarkers.status == "processed"
        assert sample_pdf_stuck_with_biomarkers.processed_date is not None
        assert sample_pdf_stuck_with_biomarkers.parsing_confidence == 0.9  # 0.5 + 8*0.05
        
        # Verify database operations
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(sample_pdf_stuck_with_biomarkers)
        
        # Verify response data
        assert data["status"] == "processed"
        assert data["file_id"] == "stuck-pdf-with-biomarkers"
        
        # Cleanup
        app.dependency_overrides.clear()

    @patch('app.api.routes.pdf_routes.get_db')
    def test_status_endpoint_auto_corrects_processing_with_biomarkers(self, mock_get_db, client, mock_db_session, sample_pdf_processing_with_biomarkers):
        """Test that status endpoint auto-corrects processing PDF with biomarkers."""
        mock_get_db.return_value = mock_db_session
        
        # Mock PDF query
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.first.return_value = sample_pdf_processing_with_biomarkers
        
        # Mock biomarker count query to return 12 biomarkers
        mock_biomarker_query = Mock()
        mock_biomarker_query.filter.return_value.count.return_value = 12
        
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        # Make request
        response = client.get("/api/pdf/status/processing-pdf-with-biomarkers")
        
        # Verify auto-correction
        assert response.status_code == 200
        assert sample_pdf_processing_with_biomarkers.status == "processed"
        assert sample_pdf_processing_with_biomarkers.parsing_confidence == 0.95  # Capped at 0.95

    @patch('app.api.routes.pdf_routes.get_db')
    def test_status_endpoint_no_correction_for_pending_without_biomarkers(self, mock_get_db, client, mock_db_session, sample_pdf_stuck_with_biomarkers):
        """Test that status endpoint doesn't correct pending PDF without biomarkers."""
        mock_get_db.return_value = mock_db_session
        
        # Mock PDF query
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.first.return_value = sample_pdf_stuck_with_biomarkers
        
        # Mock biomarker count query to return 0 biomarkers
        mock_biomarker_query = Mock()
        mock_biomarker_query.filter.return_value.count.return_value = 0
        
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        # Make request
        response = client.get("/api/pdf/status/stuck-pdf-with-biomarkers")
        
        # Verify no correction
        assert response.status_code == 200
        assert sample_pdf_stuck_with_biomarkers.status == "pending"  # Should remain unchanged
        mock_db_session.commit.assert_not_called()

    @patch('app.api.routes.pdf_routes.get_db')
    def test_status_endpoint_no_correction_for_processed_pdf(self, mock_get_db, client, mock_db_session, sample_pdf_correctly_processed):
        """Test that status endpoint doesn't modify already processed PDFs."""
        mock_get_db.return_value = mock_db_session
        
        # Mock PDF query
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.first.return_value = sample_pdf_correctly_processed
        
        mock_db_session.query.return_value = mock_pdf_query
        
        # Make request
        response = client.get("/api/pdf/status/correctly-processed-pdf")
        
        # Verify no changes
        assert response.status_code == 200
        assert sample_pdf_correctly_processed.status == "processed"
        assert sample_pdf_correctly_processed.parsing_confidence == 0.85  # Original value preserved
        
        # Should not query biomarkers since status is not pending/processing
        assert mock_db_session.query.call_count == 1  # Only PDF query

    @patch('app.api.routes.pdf_routes.get_db')
    def test_status_endpoint_preserves_existing_processed_date(self, mock_get_db, client, mock_db_session, sample_pdf_stuck_with_biomarkers):
        """Test that existing processed_date is preserved during auto-correction."""
        mock_get_db.return_value = mock_db_session
        
        # Set existing processed date
        existing_date = datetime.utcnow() - timedelta(hours=1)
        sample_pdf_stuck_with_biomarkers.processed_date = existing_date
        
        # Mock queries
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.first.return_value = sample_pdf_stuck_with_biomarkers
        
        mock_biomarker_query = Mock()
        mock_biomarker_query.filter.return_value.count.return_value = 5
        
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        # Make request
        response = client.get("/api/pdf/status/stuck-pdf-with-biomarkers")
        
        # Verify existing date preserved
        assert response.status_code == 200
        assert sample_pdf_stuck_with_biomarkers.processed_date == existing_date

    @patch('app.api.routes.pdf_routes.get_db')
    def test_status_endpoint_preserves_existing_confidence(self, mock_get_db, client, mock_db_session, sample_pdf_stuck_with_biomarkers):
        """Test that existing parsing confidence is preserved during auto-correction."""
        mock_get_db.return_value = mock_db_session
        
        # Set existing confidence
        sample_pdf_stuck_with_biomarkers.parsing_confidence = 0.75
        
        # Mock queries
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.first.return_value = sample_pdf_stuck_with_biomarkers
        
        mock_biomarker_query = Mock()
        mock_biomarker_query.filter.return_value.count.return_value = 10
        
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        # Make request
        response = client.get("/api/pdf/status/stuck-pdf-with-biomarkers")
        
        # Verify existing confidence preserved
        assert response.status_code == 200
        assert sample_pdf_stuck_with_biomarkers.parsing_confidence == 0.75

    @patch('app.api.routes.pdf_routes.get_db')
    def test_status_endpoint_handles_database_error_gracefully(self, mock_get_db, client, mock_db_session, sample_pdf_stuck_with_biomarkers):
        """Test that database errors during auto-correction are handled gracefully."""
        mock_get_db.return_value = mock_db_session
        
        # Mock PDF query
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.first.return_value = sample_pdf_stuck_with_biomarkers
        
        # Mock biomarker query
        mock_biomarker_query = Mock()
        mock_biomarker_query.filter.return_value.count.return_value = 5
        
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        # Make commit fail
        mock_db_session.commit.side_effect = Exception("Database error")
        
        # Make request - should not crash
        response = client.get("/api/pdf/status/stuck-pdf-with-biomarkers")
        
        # Should return 500 error due to database issue
        assert response.status_code == 500

    @patch('app.api.routes.pdf_routes.get_db')
    def test_status_endpoint_confidence_calculation_edge_cases(self, mock_get_db, client, mock_db_session, sample_pdf_stuck_with_biomarkers):
        """Test confidence calculation for edge cases."""
        mock_get_db.return_value = mock_db_session
        
        # Mock queries
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.first.return_value = sample_pdf_stuck_with_biomarkers
        
        mock_biomarker_query = Mock()
        
        # Test with 1 biomarker
        mock_biomarker_query.filter.return_value.count.return_value = 1
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        response = client.get("/api/pdf/status/stuck-pdf-with-biomarkers")
        
        assert response.status_code == 200
        assert sample_pdf_stuck_with_biomarkers.parsing_confidence == 0.55  # 0.5 + 1*0.05
        
        # Reset for next test
        sample_pdf_stuck_with_biomarkers.parsing_confidence = None
        sample_pdf_stuck_with_biomarkers.status = "pending"
        
        # Test with 20 biomarkers (should cap at 0.95)
        mock_biomarker_query.filter.return_value.count.return_value = 20
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        response = client.get("/api/pdf/status/stuck-pdf-with-biomarkers")
        
        assert response.status_code == 200
        assert sample_pdf_stuck_with_biomarkers.parsing_confidence == 0.95  # Capped at 0.95

    @patch('app.api.routes.pdf_routes.get_db')
    def test_status_endpoint_pdf_not_found(self, mock_get_db, client, mock_db_session):
        """Test status endpoint behavior when PDF is not found."""
        mock_get_db.return_value = mock_db_session
        
        # Mock PDF query to return None
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_pdf_query
        
        # Make request
        response = client.get("/api/pdf/status/non-existent-pdf")
        
        # Should return not_found status
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "not_found"
        assert data["file_id"] == "non-existent-pdf"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 