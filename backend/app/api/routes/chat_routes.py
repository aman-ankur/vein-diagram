"""
Chat API routes for the Biomarker Insights Chatbot.
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any
import logging

from ...schemas.chat_schema import (
    ChatRequest, ChatResponse, ChatSuggestionsRequest, 
    ChatSuggestionsResponse, FeedbackRequest, ChatFeedbackResponse,
    UsageMetrics, ChatValidation
)
from ...services.chat_service import chat_service
from ...core.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChatResponse:
    """
    Main chat endpoint for sending messages and receiving AI responses.
    
    - **message**: User's question or message (1-1000 characters)
    - **profile_id**: Active profile UUID
    - **conversation_history**: Recent conversation context (optional, max 15 messages)
    - **biomarker_context**: Relevant biomarker data (optional, max 20 biomarkers)
    
    Returns AI-generated response with biomarker insights and suggestions.
    """
    try:
        # Validate request
        if not ChatValidation.validate_message_length(request.message):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Message must be between 1 and {ChatValidation.MAX_MESSAGE_LENGTH} characters"
            )
        
        if request.conversation_history and not ChatValidation.validate_conversation_history(request.conversation_history):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Conversation history cannot exceed {ChatValidation.MAX_CONVERSATION_HISTORY} messages"
            )
        
        if not ChatValidation.validate_biomarker_context(request.biomarker_context):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Biomarker context cannot exceed {ChatValidation.MAX_BIOMARKERS_IN_CONTEXT} biomarkers"
            )
        
        # TODO: Add profile ownership validation
        # Ensure the profile belongs to the current user
        
        # Process chat request
        response = await chat_service.get_chat_response(request)
        
        logger.info(f"Chat response generated for profile {request.profile_id}, "
                   f"tokens: {response.token_usage}, cached: {response.is_from_cache}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing chat request"
        )

@router.get("/suggestions/{profile_id}", response_model=ChatSuggestionsResponse)
async def get_chat_suggestions(
    profile_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChatSuggestionsResponse:
    """
    Get contextual question suggestions based on user's biomarker profile.
    
    - **profile_id**: Profile UUID to generate suggestions for
    
    Returns welcome message and suggested questions prioritized by biomarker status.
    """
    try:
        # TODO: Add profile ownership validation
        
        suggestions = await chat_service.get_suggestions(profile_id)
        
        logger.info(f"Generated {len(suggestions.suggestions)} suggestions for profile {profile_id}")
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Chat suggestions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating chat suggestions"
        )

@router.post("/feedback", response_model=ChatFeedbackResponse)
async def submit_chat_feedback(
    request: FeedbackRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> ChatFeedbackResponse:
    """
    Submit feedback on chat responses for quality improvement.
    
    - **response_id**: ID of the response being rated
    - **is_helpful**: Simple thumbs up/down rating
    - **feedback_type**: Optional category of feedback
    - **comment**: Optional detailed feedback (max 500 characters)
    
    Returns confirmation of feedback submission.
    """
    try:
        # Store feedback for analysis (simple logging for MVP)
        feedback_data = {
            "response_id": request.response_id,
            "is_helpful": request.is_helpful,
            "feedback_type": request.feedback_type,
            "comment": request.comment,
            "user_id": current_user.get("sub"),
            "timestamp": logger.info.__self__.handlers[0].formatter.formatTime(logger.info.__self__.handlers[0].emit.__defaults__[0] if logger.info.__self__.handlers else None) if logger.info.__self__.handlers else None
        }
        
        logger.info(f"Chat feedback received: {feedback_data}")
        
        return ChatFeedbackResponse(
            success=True,
            message="Thank you for your feedback! It helps us improve the chat experience."
        )
        
    except Exception as e:
        logger.error(f"Chat feedback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing feedback"
        )

@router.get("/usage/{profile_id}", response_model=UsageMetrics)
async def get_usage_metrics(
    profile_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> UsageMetrics:
    """
    Get usage metrics for cost monitoring (admin/development use).
    
    - **profile_id**: Profile UUID to get metrics for
    
    Returns daily usage statistics including API calls, tokens, and cache hit rate.
    """
    try:
        # TODO: Add profile ownership validation and admin permission check
        
        metrics = chat_service.get_usage_metrics(profile_id)
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No usage data available for this profile today"
            )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Usage metrics error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving usage metrics"
        )

@router.delete("/history/{profile_id}")
async def clear_conversation_history(
    profile_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Clear conversation history for privacy (future implementation).
    
    - **profile_id**: Profile UUID to clear history for
    
    Currently returns success as conversation history is stored client-side.
    """
    try:
        # TODO: Add profile ownership validation
        
        # For MVP, conversation history is stored client-side
        # This endpoint confirms the clear action for consistency
        
        logger.info(f"Conversation history clear requested for profile {profile_id}")
        
        return {
            "success": True,
            "message": "Conversation history cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Clear history error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error clearing conversation history"
        )

# Health check endpoint for chat service
@router.get("/health")
async def chat_health_check() -> Dict[str, Any]:
    """
    Health check endpoint for chat service status.
    """
    try:
        # Basic health check - verify service initialization
        if chat_service.feature_flags:
            from datetime import datetime
            return {
                "status": "healthy",
                "chat_service": {
                    "health_score_enabled": chat_service.feature_flags.health_score_integration,
                    "caching_enabled": chat_service.feature_flags.advanced_caching,
                    "feedback_enabled": chat_service.feature_flags.feedback_collection
                },
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise Exception("Chat service not properly initialized")
            
    except Exception as e:
        logger.error(f"Chat health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service unavailable"
        ) 