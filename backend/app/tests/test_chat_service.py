"""
Tests for the chat service functionality.
"""
import pytest
import json
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from app.services.chat_service import ChatService
from app.schemas.chat_schema import (
    ChatRequest, BiomarkerContext, BiomarkerContextItem,
    HealthScoreContext, ChatMessage
)

class TestChatService:
    """Test cases for ChatService"""
    
    @pytest.fixture
    def chat_service(self):
        """Create a chat service instance for testing"""
        return ChatService()
    
    @pytest.fixture
    def sample_biomarker_context(self):
        """Sample biomarker context for testing"""
        return BiomarkerContext(
            relevant_biomarkers=[
                BiomarkerContextItem(
                    name="Glucose",
                    value=110.0,
                    unit="mg/dL",
                    reference_range="70-99",
                    is_abnormal=True,
                    trend="worsened",
                    is_favorite=True
                ),
                BiomarkerContextItem(
                    name="Cholesterol",
                    value=180.0,
                    unit="mg/dL", 
                    reference_range="0-200",
                    is_abnormal=False,
                    is_favorite=False
                ),
                BiomarkerContextItem(
                    name="HDL",
                    value=35.0,
                    unit="mg/dL",
                    reference_range="40-200", 
                    is_abnormal=True,
                    is_favorite=True
                )
            ],
            health_score_context=HealthScoreContext(
                current_score=72.5,
                influencing_factors=["glucose", "hdl"],
                trend="declining"
            )
        )
    
    @pytest.fixture
    def sample_chat_request(self, sample_biomarker_context):
        """Sample chat request for testing"""
        return ChatRequest(
            message="What can I do to improve my glucose levels?",
            profile_id="test-profile-123",
            conversation_history=[
                ChatMessage(
                    role="user",
                    content="Hello",
                    timestamp="2023-01-01T10:00:00Z"
                ),
                ChatMessage(
                    role="assistant", 
                    content="Hi! How can I help you with your biomarkers?",
                    timestamp="2023-01-01T10:00:01Z"
                )
            ],
            biomarker_context=sample_biomarker_context
        )
    
    def test_feature_flags_loading(self, chat_service):
        """Test that feature flags are loaded correctly"""
        assert hasattr(chat_service, 'feature_flags')
        assert hasattr(chat_service.feature_flags, 'health_score_integration')
        assert hasattr(chat_service.feature_flags, 'usage_limits_enabled')
        assert hasattr(chat_service.feature_flags, 'advanced_caching')
        assert hasattr(chat_service.feature_flags, 'feedback_collection')
    
    @patch.dict(os.environ, {
        'CHAT_HEALTH_SCORE_ENABLED': 'true',
        'CHAT_USAGE_LIMITS_ENABLED': 'false',
        'CHAT_ADVANCED_CACHING': 'true',
        'CHAT_FEEDBACK_ENABLED': 'true'
    })
    def test_feature_flags_from_environment(self):
        """Test feature flags are correctly loaded from environment variables"""
        service = ChatService()
        assert service.feature_flags.health_score_integration == True
        assert service.feature_flags.usage_limits_enabled == False
        assert service.feature_flags.advanced_caching == True
        assert service.feature_flags.feedback_collection == True
    
    def test_biomarker_cache_loading(self, chat_service):
        """Test that biomarker cache is loaded"""
        assert hasattr(chat_service, 'biomarker_cache')
        assert isinstance(chat_service.biomarker_cache, dict)
        # Should have biomarker_patterns key even if empty
        assert 'biomarker_patterns' in chat_service.biomarker_cache
    
    def test_prepare_biomarker_context_basic(self, chat_service, sample_chat_request):
        """Test basic biomarker context preparation"""
        context = chat_service._prepare_biomarker_context(sample_chat_request)
        
        assert isinstance(context, dict)
        assert 'relevant_biomarkers' in context
        assert 'abnormal_count' in context
        assert 'favorites_count' in context
        assert 'health_score_available' in context
        
        # Should prioritize abnormal biomarkers
        assert context['abnormal_count'] == 2  # Glucose and HDL are abnormal
        assert context['favorites_count'] == 2  # Glucose and HDL are favorites
    
    def test_prepare_biomarker_context_prioritization(self, chat_service, sample_chat_request):
        """Test that abnormal and favorite biomarkers are prioritized"""
        context = chat_service._prepare_biomarker_context(sample_chat_request)
        
        relevant_biomarkers = context['relevant_biomarkers']
        
        # First two should be abnormal biomarkers (Glucose and HDL)
        abnormal_markers = [b for b in relevant_biomarkers if b['is_abnormal']]
        assert len(abnormal_markers) == 2
        
        # Check that abnormal markers include Glucose and HDL
        abnormal_names = [b['name'] for b in abnormal_markers]
        assert 'Glucose' in abnormal_names
        assert 'HDL' in abnormal_names
    
    def test_prepare_biomarker_context_health_score_disabled(self, chat_service, sample_chat_request):
        """Test biomarker context when health score is disabled"""
        # Disable health score integration
        chat_service.feature_flags.health_score_integration = False
        
        context = chat_service._prepare_biomarker_context(sample_chat_request)
        
        assert context['health_score_available'] == False
        assert 'health_score' not in context
    
    def test_prepare_biomarker_context_health_score_enabled(self, chat_service, sample_chat_request):
        """Test biomarker context when health score is enabled"""
        # Enable health score integration
        chat_service.feature_flags.health_score_integration = True
        
        context = chat_service._prepare_biomarker_context(sample_chat_request)
        
        assert context['health_score_available'] == True
        assert 'health_score' in context
        assert context['health_score']['current_score'] == 72.5
    
    def test_prepare_biomarker_context_no_biomarkers(self, chat_service):
        """Test context preparation when no biomarkers are provided"""
        request = ChatRequest(
            message="General health question",
            profile_id="test-profile-123"
        )
        
        context = chat_service._prepare_biomarker_context(request)
        
        assert context['relevant_biomarkers'] == []
        assert context['abnormal_count'] == 0
        assert context['favorites_count'] == 0
        assert context['health_score_available'] == False
    
    def test_create_health_assistant_prompt_basic(self, chat_service, sample_chat_request):
        """Test prompt creation with biomarker context"""
        context = chat_service._prepare_biomarker_context(sample_chat_request)
        prompt = chat_service._create_health_assistant_prompt(sample_chat_request, context)
        
        assert isinstance(prompt, str)
        assert "Biomarker Health Assistant" in prompt
        assert "CURRENT BIOMARKER VALUES:" in prompt
        assert "Glucose: 110.0 mg/dL (ABNORMAL)" in prompt
        assert "HDL: 35.0 mg/dL (ABNORMAL)" in prompt
        assert "Cholesterol: 180.0 mg/dL (Normal)" in prompt
        
        # Check for user question
        assert "What can I do to improve my glucose levels?" in prompt
        
        # Check for medical limitations
        assert "CANNOT diagnose medical conditions" in prompt
        assert "CANNOT recommend medications" in prompt
    
    def test_create_health_assistant_prompt_with_conversation_history(self, chat_service, sample_chat_request):
        """Test prompt creation includes conversation history"""
        context = chat_service._prepare_biomarker_context(sample_chat_request)
        prompt = chat_service._create_health_assistant_prompt(sample_chat_request, context)
        
        assert "RECENT CONVERSATION:" in prompt
        assert "USER: Hello" in prompt
        assert "ASSISTANT: Hi! How can I help you with your biomarkers?" in prompt
    
    def test_create_health_assistant_prompt_with_health_score(self, chat_service, sample_chat_request):
        """Test prompt creation includes health score when enabled"""
        chat_service.feature_flags.health_score_integration = True
        context = chat_service._prepare_biomarker_context(sample_chat_request)
        prompt = chat_service._create_health_assistant_prompt(sample_chat_request, context)
        
        assert "HEALTH SCORE: 72.5/100" in prompt
        assert "declining" in prompt
        assert "glucose, hdl" in prompt
    
    def test_extract_biomarker_references(self, chat_service, sample_biomarker_context):
        """Test extraction of biomarker references from AI response"""
        ai_response = "Your glucose levels are elevated and your HDL cholesterol is below optimal range."
        
        references = chat_service._extract_biomarker_references(ai_response, sample_biomarker_context)
        
        assert len(references) >= 2  # Should find Glucose and HDL
        
        # Check that extracted references include key biomarkers
        ref_names = [ref.name for ref in references]
        assert 'Glucose' in ref_names
        assert 'HDL' in ref_names
        
        # Check reference details
        glucose_ref = next(ref for ref in references if ref.name == 'Glucose')
        assert glucose_ref.value == 110.0
        assert glucose_ref.unit == "mg/dL"
        assert glucose_ref.is_abnormal == True
    
    def test_generate_follow_up_suggestions_diet(self, chat_service, sample_biomarker_context):
        """Test follow-up suggestions generation for diet-related responses"""
        ai_response = "To improve your glucose, focus on a balanced diet with complex carbohydrates."
        
        suggestions = chat_service._generate_follow_up_suggestions(ai_response, sample_biomarker_context)
        
        assert len(suggestions) <= 3  # Should limit to 3 suggestions
        assert any("foods" in suggestion.lower() for suggestion in suggestions)
    
    def test_generate_follow_up_suggestions_exercise(self, chat_service, sample_biomarker_context):
        """Test follow-up suggestions generation for exercise-related responses"""
        ai_response = "Regular exercise can help improve your HDL cholesterol levels."
        
        suggestions = chat_service._generate_follow_up_suggestions(ai_response, sample_biomarker_context)
        
        assert any("exercise" in suggestion.lower() for suggestion in suggestions)
    
    def test_generate_follow_up_suggestions_multiple_abnormal(self, chat_service, sample_biomarker_context):
        """Test follow-up suggestions when multiple abnormal biomarkers exist"""
        ai_response = "Both your glucose and HDL need attention."
        
        suggestions = chat_service._generate_follow_up_suggestions(ai_response, sample_biomarker_context)
        
        # Should suggest asking about biomarker relationships
        assert any("related" in suggestion.lower() for suggestion in suggestions)
    
    @patch('app.services.chat_service.get_llm_response')
    @pytest.mark.asyncio
    async def test_get_chat_response_success(self, mock_llm, chat_service, sample_chat_request):
        """Test successful chat response generation"""
        # Mock the LLM response
        mock_llm.return_value = "Based on your glucose level of 110 mg/dL, I recommend reducing refined carbohydrates and increasing fiber intake."
        
        response = await chat_service.get_chat_response(sample_chat_request)
        
        assert response.response is not None
        assert response.response_id is not None
        assert response.is_from_cache == False
        assert response.token_usage > 0
        assert response.response_time_ms >= 0  # Response time should be non-negative (can be 0 for mocked calls)
        
        # Should have biomarker references
        assert len(response.biomarker_references) > 0
        
        # Should have follow-up suggestions
        assert len(response.suggested_follow_ups) > 0
        
        # Verify LLM was called with proper prompt
        mock_llm.assert_called_once()
        call_args = mock_llm.call_args[0]
        prompt = call_args[0]
        assert "Glucose: 110.0 mg/dL (ABNORMAL)" in prompt
    
    @patch('app.services.chat_service.get_llm_response')
    @pytest.mark.asyncio
    async def test_get_chat_response_llm_failure(self, mock_llm, chat_service, sample_chat_request):
        """Test chat response when LLM service fails"""
        # Mock LLM failure
        mock_llm.return_value = None
        
        response = await chat_service.get_chat_response(sample_chat_request)
        
        # Should return error response
        assert "having trouble processing your request" in response.response
        assert response.token_usage == 0
        assert response.is_from_cache == False
    
    def test_track_usage_metrics(self, chat_service):
        """Test usage metrics tracking"""
        profile_id = "test-profile-123"
        
        # Track some usage
        chat_service._track_usage(profile_id, 100, False)  # API call
        chat_service._track_usage(profile_id, 0, True)     # Cache hit
        chat_service._track_usage(profile_id, 150, False)  # Another API call
        
        # Get metrics
        metrics = chat_service.get_usage_metrics(profile_id)
        
        assert metrics is not None
        assert metrics.daily_api_calls == 2
        assert metrics.daily_tokens == 250
        assert abs(metrics.cache_hit_rate - 33.33) < 0.01  # Use approximate comparison for floats
    
    def test_get_usage_metrics_no_data(self, chat_service):
        """Test usage metrics when no data exists"""
        metrics = chat_service.get_usage_metrics("nonexistent-profile")
        assert metrics is None
    
    @pytest.mark.asyncio
    async def test_get_suggestions_basic(self, chat_service):
        """Test getting basic chat suggestions"""
        suggestions = await chat_service.get_suggestions("test-profile-123")
        
        assert suggestions.suggestions is not None
        assert len(suggestions.suggestions) > 0
        assert suggestions.welcome_message is not None
        
        # Check that suggestions have required fields
        for suggestion in suggestions.suggestions:
            assert suggestion.question is not None
            assert suggestion.category in ["abnormal", "favorites", "general", "health_score"]
            assert 1 <= suggestion.priority <= 10
    
    @pytest.mark.asyncio
    async def test_get_suggestions_with_health_score_enabled(self, chat_service):
        """Test suggestions include health score when enabled"""
        chat_service.feature_flags.health_score_integration = True
        
        suggestions = await chat_service.get_suggestions("test-profile-123")
        
        # Should include health score related suggestion
        health_score_suggestions = [s for s in suggestions.suggestions if s.category == "health_score"]
        assert len(health_score_suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_get_suggestions_with_health_score_disabled(self, chat_service):
        """Test suggestions exclude health score when disabled"""
        chat_service.feature_flags.health_score_integration = False
        
        suggestions = await chat_service.get_suggestions("test-profile-123")
        
        # Should not include health score related suggestions
        health_score_suggestions = [s for s in suggestions.suggestions if s.category == "health_score"]
        assert len(health_score_suggestions) == 0

class TestChatServiceIntegration:
    """Integration tests for chat service with real dependencies"""
    
    @pytest.fixture
    def chat_service(self):
        """Create chat service with real dependencies"""
        return ChatService()
    
    def test_biomarker_cache_integration(self, chat_service):
        """Test integration with actual biomarker cache file"""
        # This test verifies that we can load the real biomarker cache
        assert 'biomarker_patterns' in chat_service.biomarker_cache
        
        # If cache file exists, should have some patterns
        if os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'cache', 'biomarker_cache.json')):
            patterns = chat_service.biomarker_cache.get('biomarker_patterns', {})
            # Should have common biomarkers like glucose, cholesterol
            common_markers = ['glucose', 'cholesterol', 'hdl', 'ldl']
            found_markers = [marker for marker in common_markers if marker in patterns]
            assert len(found_markers) > 0, "Should find at least some common biomarkers in cache" 