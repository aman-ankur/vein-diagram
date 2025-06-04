"""
Pydantic schemas for the chat API endpoints.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class BiomarkerReference(BaseModel):
    """Reference to a biomarker mentioned in responses"""
    name: str
    value: float
    unit: str
    is_abnormal: bool
    reference_range: Optional[str] = None

class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    response_id: Optional[str] = Field(None, alias="responseId")
    biomarker_references: Optional[List[BiomarkerReference]] = Field(None, alias="biomarkerReferences")
    suggested_follow_ups: Optional[List[str]] = Field(None, alias="suggestedFollowUps")

    class Config:
        allow_population_by_field_name = True

class BiomarkerContextItem(BaseModel):
    """Individual biomarker for context"""
    name: str
    value: float
    unit: str
    reference_range: str = Field(..., alias="referenceRange")
    is_abnormal: bool = Field(..., alias="isAbnormal")
    trend: Optional[str] = Field(None, pattern="^(improved|worsened|stable)$")
    is_favorite: Optional[bool] = Field(False, alias="isFavorite")

    class Config:
        allow_population_by_field_name = True

class HealthScoreContext(BaseModel):
    """Optional Health Score context"""
    current_score: float = Field(..., alias="currentScore")
    influencing_factors: List[str] = Field(..., alias="influencingFactors")
    trend: str

    class Config:
        allow_population_by_field_name = True

class BiomarkerContext(BaseModel):
    """Biomarker context for chat requests"""
    relevant_biomarkers: List[BiomarkerContextItem] = Field(..., alias="relevantBiomarkers")
    health_score_context: Optional[HealthScoreContext] = Field(None, alias="healthScoreContext")

    class Config:
        allow_population_by_field_name = True

class ChatRequest(BaseModel):
    """Chat request payload"""
    message: str = Field(..., min_length=1, max_length=1000)
    profile_id: str = Field(..., alias="profileId")
    conversation_history: Optional[List[ChatMessage]] = Field(default=[], alias="conversationHistory")
    biomarker_context: Optional[BiomarkerContext] = Field(default=None, alias="biomarkerContext")

    class Config:
        allow_population_by_field_name = True  # Allow both field name and alias

class ChatResponse(BaseModel):
    """Chat response payload"""
    response: str
    biomarker_references: Optional[List[BiomarkerReference]] = []
    suggested_follow_ups: Optional[List[str]] = []
    sources: Optional[List[str]] = []
    response_id: str
    is_from_cache: bool = False
    token_usage: int = 0
    response_time_ms: int = 0

class SuggestedQuestion(BaseModel):
    """Suggested question for users"""
    question: str
    category: str = Field(..., pattern="^(abnormal|favorites|general|health_score)$")
    priority: int = Field(..., ge=1, le=10)

class ChatSuggestionsRequest(BaseModel):
    """Request for chat suggestions"""
    profile_id: str = Field(..., alias="profileId")

    class Config:
        allow_population_by_field_name = True  # Allow both field name and alias

class ChatSuggestionsResponse(BaseModel):
    """Response with suggested questions"""
    suggestions: List[SuggestedQuestion]
    welcome_message: str

class FeedbackRequest(BaseModel):
    """Feedback submission request"""
    response_id: str = Field(..., min_length=1)
    is_helpful: bool
    feedback_type: Optional[str] = Field(None, pattern="^(accuracy|clarity|completeness|actionability)$")
    comment: Optional[str] = Field(None, max_length=500)

class ChatFeedbackResponse(BaseModel):
    """Feedback submission response"""
    success: bool
    message: str

class UsageMetrics(BaseModel):
    """Usage metrics for cost monitoring"""
    daily_api_calls: int
    daily_tokens: int
    cache_hit_rate: float
    average_response_time: float
    estimated_daily_cost_usd: float = 0.0
    date: str

class ChatError(BaseModel):
    """Error response for chat endpoints"""
    error_type: str
    message: str
    retryable: bool = False
    details: Optional[Dict[str, Any]] = None

# Feature flag configuration
class ChatFeatureFlags(BaseModel):
    """Feature flags for optional chat functionality"""
    health_score_integration: bool = False
    usage_limits_enabled: bool = False
    advanced_caching: bool = True
    feedback_collection: bool = True

# Validation helpers
class ChatValidation:
    """Validation helpers for chat functionality"""
    
    MAX_MESSAGE_LENGTH = 1000
    MAX_CONVERSATION_HISTORY = 15
    MAX_BIOMARKERS_IN_CONTEXT = 20
    
    @staticmethod
    def validate_message_length(message: str) -> bool:
        """Validate message length"""
        return 1 <= len(message.strip()) <= ChatValidation.MAX_MESSAGE_LENGTH
    
    @staticmethod
    def validate_conversation_history(history: List[ChatMessage]) -> bool:
        """Validate conversation history length"""
        return len(history) <= ChatValidation.MAX_CONVERSATION_HISTORY
    
    @staticmethod
    def validate_biomarker_context(context: Optional[BiomarkerContext]) -> bool:
        """Validate biomarker context size"""
        if not context:
            return True
        return len(context.relevant_biomarkers) <= ChatValidation.MAX_BIOMARKERS_IN_CONTEXT 