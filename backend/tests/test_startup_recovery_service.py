#!/usr/bin/env python3
"""
Unit tests for the Startup Recovery Service

Tests the detection and fixing of inconsistent PDF processing states.
"""

import pytest
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.startup_recovery_service import (
    detect_inconsistent_pdfs,
    fix_inconsistent_pdf,
    run_startup_recovery,
    check_processing_health
)
from app.models.pdf_model import PDF
from app.models.biomarker_model import Biomarker

# Configure test logging
logging.basicConfig(level=logging.INFO)

class TestStartupRecoveryService:
    """Test suite for startup recovery service functions."""
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session."""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_pdf_pending(self):
        """Create a sample PDF with pending status."""
        return PDF(
            id=1,
            file_id="test-file-id-1",
            filename="test_report_1.pdf",
            file_path="/uploads/test_report_1.pdf",
            status="pending",
            upload_date=datetime.utcnow() - timedelta(hours=1),
            processed_date=None,
            parsing_confidence=None
        )
    
    @pytest.fixture
    def sample_pdf_processing(self):
        """Create a sample PDF with processing status."""
        return PDF(
            id=2,
            file_id="test-file-id-2",
            filename="test_report_2.pdf",
            file_path="/uploads/test_report_2.pdf",
            status="processing",
            upload_date=datetime.utcnow() - timedelta(hours=2),
            processed_date=None,
            parsing_confidence=None
        )
    
    @pytest.fixture
    def sample_pdf_processed(self):
        """Create a sample PDF with processed status."""
        return PDF(
            id=3,
            file_id="test-file-id-3",
            filename="test_report_3.pdf",
            file_path="/uploads/test_report_3.pdf",
            status="processed",
            upload_date=datetime.utcnow() - timedelta(hours=3),
            processed_date=datetime.utcnow() - timedelta(minutes=30),
            parsing_confidence=0.85
        )

    def test_detect_inconsistent_pdfs_no_stuck_pdfs(self, mock_db_session):
        """Test detection when no PDFs are stuck."""
        # Mock query to return no stuck PDFs
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = []
        mock_db_session.query.return_value = mock_query
        
        result = detect_inconsistent_pdfs(mock_db_session)
        
        assert result == []
        mock_db_session.query.assert_called_with(PDF)

    def test_detect_inconsistent_pdfs_stuck_without_biomarkers(self, mock_db_session, sample_pdf_pending):
        """Test detection of stuck PDFs without biomarkers (not inconsistent)."""
        # Mock query to return stuck PDF
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.all.return_value = [sample_pdf_pending]
        
        # Mock biomarker query to return 0 biomarkers
        mock_biomarker_query = Mock()
        mock_biomarker_query.filter.return_value.count.return_value = 0
        
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        result = detect_inconsistent_pdfs(mock_db_session)
        
        assert result == []

    def test_detect_inconsistent_pdfs_stuck_with_biomarkers(self, mock_db_session, sample_pdf_pending):
        """Test detection of stuck PDFs with biomarkers (inconsistent)."""
        # Mock query to return stuck PDF
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.all.return_value = [sample_pdf_pending]
        
        # Mock biomarker query to return 5 biomarkers
        mock_biomarker_query = Mock()
        mock_biomarker_query.filter.return_value.count.return_value = 5
        
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query]
        
        result = detect_inconsistent_pdfs(mock_db_session)
        
        assert len(result) == 1
        assert result[0][0] == sample_pdf_pending
        assert result[0][1] == 5

    def test_detect_inconsistent_pdfs_multiple_stuck(self, mock_db_session, sample_pdf_pending, sample_pdf_processing):
        """Test detection with multiple stuck PDFs."""
        stuck_pdfs = [sample_pdf_pending, sample_pdf_processing]
        
        # Mock PDF query
        mock_pdf_query = Mock()
        mock_pdf_query.filter.return_value.all.return_value = stuck_pdfs
        
        # Mock biomarker queries - first has biomarkers, second doesn't
        mock_biomarker_query1 = Mock()
        mock_biomarker_query1.filter.return_value.count.return_value = 8
        
        mock_biomarker_query2 = Mock()
        mock_biomarker_query2.filter.return_value.count.return_value = 0
        
        mock_db_session.query.side_effect = [mock_pdf_query, mock_biomarker_query1, mock_biomarker_query2]
        
        result = detect_inconsistent_pdfs(mock_db_session)
        
        assert len(result) == 1
        assert result[0][0] == sample_pdf_pending
        assert result[0][1] == 8

    def test_fix_inconsistent_pdf_success(self, mock_db_session, sample_pdf_pending):
        """Test successful fixing of an inconsistent PDF."""
        biomarker_count = 10
        
        result = fix_inconsistent_pdf(mock_db_session, sample_pdf_pending, biomarker_count)
        
        assert result is True
        assert sample_pdf_pending.status == "processed"
        assert sample_pdf_pending.processed_date is not None
        assert sample_pdf_pending.parsing_confidence == 0.95  # min(0.95, 0.5 + 10*0.05)
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once_with(sample_pdf_pending)

    def test_fix_inconsistent_pdf_confidence_calculation(self, mock_db_session, sample_pdf_pending):
        """Test parsing confidence calculation for different biomarker counts."""
        # Test with 3 biomarkers
        fix_inconsistent_pdf(mock_db_session, sample_pdf_pending, 3)
        expected_confidence = 0.5 + (3 * 0.05)  # 0.65
        assert sample_pdf_pending.parsing_confidence == expected_confidence
        
        # Reset for next test
        sample_pdf_pending.parsing_confidence = None
        
        # Test with 20 biomarkers (should cap at 0.95)
        fix_inconsistent_pdf(mock_db_session, sample_pdf_pending, 20)
        assert sample_pdf_pending.parsing_confidence == 0.95

    def test_fix_inconsistent_pdf_preserves_existing_confidence(self, mock_db_session, sample_pdf_pending):
        """Test that existing parsing confidence is preserved."""
        sample_pdf_pending.parsing_confidence = 0.75
        
        fix_inconsistent_pdf(mock_db_session, sample_pdf_pending, 10)
        
        assert sample_pdf_pending.parsing_confidence == 0.75  # Should not change

    def test_fix_inconsistent_pdf_preserves_existing_processed_date(self, mock_db_session, sample_pdf_pending):
        """Test that existing processed date is preserved."""
        existing_date = datetime.utcnow() - timedelta(hours=1)
        sample_pdf_pending.processed_date = existing_date
        
        fix_inconsistent_pdf(mock_db_session, sample_pdf_pending, 5)
        
        assert sample_pdf_pending.processed_date == existing_date

    def test_fix_inconsistent_pdf_database_error(self, mock_db_session, sample_pdf_pending):
        """Test handling of database errors during fixing."""
        mock_db_session.commit.side_effect = Exception("Database error")
        
        result = fix_inconsistent_pdf(mock_db_session, sample_pdf_pending, 5)
        
        assert result is False
        mock_db_session.rollback.assert_called_once()

    @patch('app.services.startup_recovery_service.SessionLocal')
    def test_run_startup_recovery_no_inconsistencies(self, mock_session_local):
        """Test startup recovery when no inconsistencies are found."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        # Mock detect_inconsistent_pdfs to return empty list
        with patch('app.services.startup_recovery_service.detect_inconsistent_pdfs') as mock_detect:
            mock_detect.return_value = []
            
            result = run_startup_recovery()
            
            assert result["inconsistent_found"] == 0
            assert result["successfully_fixed"] == 0
            assert result["failed_to_fix"] == 0
            assert result["fixed_pdfs"] == []
            mock_db.close.assert_called_once()

    @patch('app.services.startup_recovery_service.SessionLocal')
    def test_run_startup_recovery_with_fixes(self, mock_session_local, sample_pdf_pending, sample_pdf_processing):
        """Test startup recovery with successful fixes."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        inconsistent_pdfs = [
            (sample_pdf_pending, 5),
            (sample_pdf_processing, 8)
        ]
        
        with patch('app.services.startup_recovery_service.detect_inconsistent_pdfs') as mock_detect, \
             patch('app.services.startup_recovery_service.fix_inconsistent_pdf') as mock_fix:
            
            mock_detect.return_value = inconsistent_pdfs
            mock_fix.return_value = True
            
            result = run_startup_recovery()
            
            assert result["inconsistent_found"] == 2
            assert result["successfully_fixed"] == 2
            assert result["failed_to_fix"] == 0
            assert len(result["fixed_pdfs"]) == 2
            assert mock_fix.call_count == 2

    @patch('app.services.startup_recovery_service.SessionLocal')
    def test_run_startup_recovery_with_failures(self, mock_session_local, sample_pdf_pending):
        """Test startup recovery with some failures."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        inconsistent_pdfs = [(sample_pdf_pending, 5)]
        
        with patch('app.services.startup_recovery_service.detect_inconsistent_pdfs') as mock_detect, \
             patch('app.services.startup_recovery_service.fix_inconsistent_pdf') as mock_fix:
            
            mock_detect.return_value = inconsistent_pdfs
            mock_fix.return_value = False  # Simulate failure
            
            result = run_startup_recovery()
            
            assert result["inconsistent_found"] == 1
            assert result["successfully_fixed"] == 0
            assert result["failed_to_fix"] == 1
            assert result["fixed_pdfs"] == []

    @patch('app.services.startup_recovery_service.SessionLocal')
    def test_run_startup_recovery_exception_handling(self, mock_session_local):
        """Test startup recovery exception handling."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        with patch('app.services.startup_recovery_service.detect_inconsistent_pdfs') as mock_detect:
            mock_detect.side_effect = Exception("Test exception")
            
            result = run_startup_recovery()
            
            assert "error" in result
            assert result["error"] == "Test exception"
            mock_db.close.assert_called_once()

    @patch('app.services.startup_recovery_service.SessionLocal')
    def test_check_processing_health(self, mock_session_local, sample_pdf_pending, sample_pdf_processed):
        """Test processing health check."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        
        all_pdfs = [sample_pdf_pending, sample_pdf_processed]
        
        # Mock PDF query
        mock_pdf_query = Mock()
        mock_pdf_query.all.return_value = all_pdfs
        mock_db.query.return_value = mock_pdf_query
        
        with patch('app.services.startup_recovery_service.detect_inconsistent_pdfs') as mock_detect:
            mock_detect.return_value = [(sample_pdf_pending, 3)]
            
            result = check_processing_health()
            
            assert result["total_pdfs"] == 2
            assert result["pending"] == 1
            assert result["processed"] == 1
            assert result["inconsistent"] == 1

    @patch('app.services.startup_recovery_service.SessionLocal')
    def test_check_processing_health_exception(self, mock_session_local):
        """Test processing health check with exception."""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_db.query.side_effect = Exception("Database error")
        
        result = check_processing_health()
        
        assert "error_message" in result
        assert result["error_message"] == "Database error"

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 