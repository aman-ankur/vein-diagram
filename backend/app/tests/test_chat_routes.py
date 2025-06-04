"""
Tests for chat API routes.
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.core.auth import get_current_user
from app.schemas.chat_schema import (
    ChatRequest, ChatResponse, ChatSuggestionsResponse, 
    BiomarkerContext, BiomarkerContextItem, HealthScoreContext,
    ChatMessage, UsageMetrics, FeedbackRequest, BiomarkerReference
)

# Mock user for authentication
MOCK_USER = {
    "user_id": "test-user-123",
    "email": "test@example.com",
    "role": "user"
}

def mock_get_current_user():
    """Mock function to return test user"""
    return MOCK_USER

class TestChatRoutes:
    """Test cases for chat API routes"""
    
    @pytest.fixture
    def client(self):
        """Create test client with mocked authentication"""
        app.dependency_overrides[get_current_user] = mock_get_current_user
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()
    
    @pytest.fixture
    def sample_chat_request(self):
        """Sample chat request payload"""
        return {
            "message": "What can I do to improve my glucose levels?",
            "profile_id": "test-profile-123",
            "conversation_history": [
                {
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2023-01-01T10:00:00Z"
                },
                {
                    "role": "assistant",
                    "content": "Hi! How can I help you with your biomarkers?",
                    "timestamp": "2023-01-01T10:00:01Z"
                }
            ],
            "biomarker_context": {
                "relevant_biomarkers": [
                    {
                        "name": "Glucose",
                        "value": 110.0,
                        "unit": "mg/dL",
                        "reference_range": "70-99",
                        "is_abnormal": True,
                        "trend": "worsened",
                        "is_favorite": True
                    },
                    {
                        "name": "HDL",
                        "value": 35.0,
                        "unit": "mg/dL",
                        "reference_range": "40-200",
                        "is_abnormal": True,
                        "is_favorite": True
                    }
                ],
                "health_score_context": {
                    "current_score": 72.5,
                    "influencing_factors": ["glucose", "hdl"],
                    "trend": "declining"
                }
            }
        }
    
    @pytest.fixture
    def mock_chat_response(self):
        """Mock chat service response"""
        return ChatResponse(
            response="Based on your glucose level of 110 mg/dL, I recommend reducing refined carbohydrates and increasing fiber intake.",
            biomarker_references=[
                BiomarkerReference(
                    name="Glucose",
                    value=110.0,
                    unit="mg/dL",
                    reference_range="70-99",
                    is_abnormal=True
                )
            ],
            suggested_follow_ups=[
                "What specific foods should I avoid?",
                "How much exercise do I need?",
                "When should I retest my glucose?"
            ],
            sources=["American Diabetes Association"],
            response_id="response-123",
            is_from_cache=False,
            token_usage=150,
            response_time_ms=1200
        )
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_chat_endpoint_success(self, mock_chat_service, client, sample_chat_request, mock_chat_response):
        """Test successful chat interaction"""
        # Mock the service instance and its method
        mock_chat_service.get_chat_response = AsyncMock(return_value=mock_chat_response)
        
        response = client.post("/api/chat", json=sample_chat_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["response"] == mock_chat_response.response
        assert data["response_id"] == mock_chat_response.response_id
        assert len(data["biomarker_references"]) == 1
        assert len(data["suggested_follow_ups"]) == 3
        assert data["is_from_cache"] == False
        assert data["token_usage"] == 150
        assert data["response_time_ms"] == 1200
        
        # Verify service was called correctly
        mock_chat_service.get_chat_response.assert_called_once()
        call_args = mock_chat_service.get_chat_response.call_args[0][0]
        assert call_args.message == sample_chat_request["message"]
        assert call_args.profile_id == sample_chat_request["profile_id"]
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_chat_endpoint_validation_error(self, mock_chat_service, client):
        """Test chat endpoint with invalid request data"""
        invalid_request = {
            "message": "",  # Empty message should fail validation
            "profile_id": "test-profile-123"
        }
        
        response = client.post("/api/chat", json=invalid_request)
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "detail" in data
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_chat_endpoint_service_error(self, mock_chat_service, client, sample_chat_request):
        """Test chat endpoint when service raises an exception"""
        # Mock service to raise an exception
        mock_chat_service.get_chat_response = AsyncMock(side_effect=Exception("Service error"))
        
        response = client.post("/api/chat", json=sample_chat_request)
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Internal server error" in data["detail"]
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_suggestions_endpoint_success(self, mock_chat_service, client):
        """Test successful suggestions retrieval"""
        mock_suggestions = ChatSuggestionsResponse(
            suggestions=[
                {
                    "question": "What does my high glucose mean?",
                    "category": "abnormal",
                    "priority": 1
                },
                {
                    "question": "How can I improve my HDL?",
                    "category": "favorites",
                    "priority": 2
                },
                {
                    "question": "What's a healthy diet for my biomarkers?",
                    "category": "general",
                    "priority": 3
                }
            ],
            welcome_message="Hello! I can help you understand your biomarker results."
        )
        
        mock_chat_service.get_suggestions = AsyncMock(return_value=mock_suggestions)
        
        response = client.get("/api/chat/suggestions/test-profile-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data["suggestions"]) == 3
        assert data["welcome_message"] == mock_suggestions.welcome_message
        assert data["suggestions"][0]["category"] == "abnormal"
        assert data["suggestions"][0]["priority"] == 1
        
        # Verify service was called correctly
        mock_chat_service.get_suggestions.assert_called_once_with("test-profile-123")
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_suggestions_endpoint_service_error(self, mock_chat_service, client):
        """Test suggestions endpoint when service fails"""
        mock_chat_service.get_suggestions = AsyncMock(side_effect=Exception("Service error"))
        
        response = client.get("/api/chat/suggestions/test-profile-123")
        
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert "Error generating chat suggestions" in data["detail"]
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_feedback_endpoint_success(self, mock_chat_service, client):
        """Test successful feedback submission"""
        feedback_request = {
            "response_id": "response-123",
            "is_helpful": True,
            "feedback_type": "accuracy",
            "comment": "Very helpful response!"
        }
        
        # Mock service doesn't need to do anything for feedback
        
        response = client.post("/api/chat/feedback", json=feedback_request)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "Thank you for your feedback" in data["message"]
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_feedback_endpoint_validation_error(self, mock_chat_service, client):
        """Test feedback endpoint with invalid data"""
        invalid_feedback = {
            "response_id": "",  # Empty response_id should fail
            "is_helpful": True
        }
        
        response = client.post("/api/chat/feedback", json=invalid_feedback)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_usage_endpoint_success(self, mock_chat_service, client):
        """Test successful usage metrics retrieval"""
        mock_usage = UsageMetrics(
            daily_api_calls=5,
            daily_tokens=750,
            cache_hit_rate=20.0,
            average_response_time=1200.5,
            date="2024-01-15"
        )
        
        mock_chat_service.get_usage_metrics = Mock(return_value=mock_usage)
        
        response = client.get("/api/chat/usage/test-profile-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["daily_api_calls"] == 5
        assert data["daily_tokens"] == 750
        assert data["cache_hit_rate"] == 20.0
        assert data["average_response_time"] == 1200.5
        assert data["date"] == "2024-01-15"
        
        # Verify service was called correctly
        mock_chat_service.get_usage_metrics.assert_called_once_with("test-profile-123")
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_usage_endpoint_no_data(self, mock_chat_service, client):
        """Test usage endpoint when no data is available"""
        mock_chat_service.get_usage_metrics = Mock(return_value=None)
        
        response = client.get("/api/chat/usage/test-profile-123")
        
        assert response.status_code == 404
        data = response.json()
        assert "No usage data available" in data["detail"]
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_clear_history_endpoint_success(self, mock_chat_service, client):
        """Test successful conversation history clearing"""
        
        response = client.delete("/api/chat/history/test-profile-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "Conversation history cleared" in data["message"]
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_clear_history_endpoint_failure(self, mock_chat_service, client):
        """Test clear history endpoint failure handling"""
        
        response = client.delete("/api/chat/history/invalid-profile")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True  # Always succeeds for client-side storage
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test chat health check endpoint"""
        response = client.get("/api/chat/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "chat_service" in data
        assert data["timestamp"] is not None
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_chat_endpoint_minimal_request(self, mock_chat_service, client, mock_chat_response):
        """Test chat endpoint with minimal required fields"""
        mock_chat_service.get_chat_response = AsyncMock(return_value=mock_chat_response)
        
        minimal_request = {
            "message": "What does my glucose level mean?",
            "profile_id": "test-profile-123"
            # No optional fields like conversation_history or biomarker_context
        }
        
        response = client.post("/api/chat", json=minimal_request)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["response"] == mock_chat_response.response
        assert data["response_id"] == mock_chat_response.response_id
        
        # Verify service was called
        mock_chat_service.get_chat_response.assert_called_once()
        call_args = mock_chat_service.get_chat_response.call_args[0][0]
        assert call_args.message == minimal_request["message"]
        assert call_args.profile_id == minimal_request["profile_id"]
        assert call_args.conversation_history == []  # Should default to empty
        assert call_args.biomarker_context is None  # Should default to None
    
    @patch('app.api.routes.chat_routes.chat_service')
    @pytest.mark.asyncio
    async def test_chat_endpoint_with_empty_biomarker_context(self, mock_chat_service, client, mock_chat_response):
        """Test chat endpoint with empty biomarker context"""
        mock_chat_service.get_chat_response = AsyncMock(return_value=mock_chat_response)
        
        request_with_empty_context = {
            "message": "General health question",
            "profile_id": "test-profile-123",
            "biomarker_context": {
                "relevant_biomarkers": [],  # Empty list
                "health_score_context": None
            }
        }
        
        response = client.post("/api/chat", json=request_with_empty_context)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["response"] == mock_chat_response.response
        assert data["response_id"] == mock_chat_response.response_id
        
        # Verify service was called with empty context
        mock_chat_service.get_chat_response.assert_called_once()
        call_args = mock_chat_service.get_chat_response.call_args[0][0]
        assert call_args.message == request_with_empty_context["message"]
        assert call_args.biomarker_context.relevant_biomarkers == []
        assert call_args.biomarker_context.health_score_context is None

class TestChatRoutesIntegration:
    """Integration tests that test the full stack with minimal mocking"""
    
    @pytest.fixture
    def client(self):
        """Create test client for integration tests with mocked authentication"""
        app.dependency_overrides[get_current_user] = mock_get_current_user
        client = TestClient(app)
        yield client
        app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_health_endpoint_integration(self, client):
        """Test health endpoint without mocking"""
        response = client.get("/api/chat/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "chat_service" in data
        assert data["timestamp"] is not None
    
    @patch('app.services.chat_service.get_llm_response')
    @pytest.mark.asyncio
    async def test_chat_integration_with_mocked_llm(self, mock_llm, client):
        """Test chat endpoint with real service but mocked LLM"""
        # Mock the LLM response only
        mock_llm.return_value = "Based on your glucose level of 110 mg/dL, I recommend reducing refined carbohydrates and increasing fiber intake."
        
        chat_request = {
            "message": "What can I do about my high glucose?",
            "profile_id": "test-profile-123",
            "biomarker_context": {
                "relevant_biomarkers": [
                    {
                        "name": "Glucose",
                        "value": 110.0,
                        "unit": "mg/dL",
                        "reference_range": "70-99",
                        "is_abnormal": True,
                        "is_favorite": False
                    }
                ]
            }
        }
        
        response = client.post("/api/chat", json=chat_request)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify the response structure
        assert data["response"] is not None
        assert data["response_id"] is not None
        assert data["is_from_cache"] == False
        assert data["token_usage"] > 0
        assert data["response_time_ms"] >= 0
        
        # Should include biomarker references
        assert len(data["biomarker_references"]) > 0
        assert data["biomarker_references"][0]["name"] == "Glucose"
        
        # Should include follow-up suggestions (may be empty in real service)
        assert "suggested_follow_ups" in data
        assert isinstance(data["suggested_follow_ups"], list)
        
        # Verify LLM was called
        mock_llm.assert_called_once() 