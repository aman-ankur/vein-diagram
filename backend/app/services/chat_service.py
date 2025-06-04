"""
Core chat service for the Biomarker Insights Chatbot.
Integrates with existing LLM service and biomarker cache for cost-optimized responses.
"""
import os
import json
import uuid
import time
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta, timezone
import logging

from ..schemas.chat_schema import (
    ChatRequest, ChatResponse, BiomarkerReference, 
    SuggestedQuestion, ChatSuggestionsResponse,
    UsageMetrics, ChatFeatureFlags
)
from .llm_service import get_llm_response

logger = logging.getLogger(__name__)

class ChatService:
    """
    Core chat service with cost optimization and biomarker intelligence.
    """
    
    def __init__(self):
        self.feature_flags = self._load_feature_flags()
        self.biomarker_cache = self._load_biomarker_cache()
        self.usage_metrics = {}  # Simple in-memory tracking for MVP
        
    def _load_feature_flags(self) -> ChatFeatureFlags:
        """Load feature flags from environment variables"""
        return ChatFeatureFlags(
            health_score_integration=os.getenv("CHAT_HEALTH_SCORE_ENABLED", "false").lower() == "true",
            usage_limits_enabled=os.getenv("CHAT_USAGE_LIMITS_ENABLED", "false").lower() == "true",
            advanced_caching=os.getenv("CHAT_ADVANCED_CACHING", "true").lower() == "true",
            feedback_collection=os.getenv("CHAT_FEEDBACK_ENABLED", "true").lower() == "true"
        )
    
    def _load_biomarker_cache(self) -> Dict[str, Any]:
        """Load existing biomarker cache for pattern matching"""
        try:
            cache_path = os.path.join(os.path.dirname(__file__), '..', 'cache', 'biomarker_cache.json')
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load biomarker cache: {e}")
            return {"biomarker_patterns": {}}
    
    async def get_chat_response(self, request: ChatRequest) -> ChatResponse:
        """
        Main chat endpoint - processes user message and returns AI response.
        Implements cache-first strategy and cost monitoring.
        """
        start_time = time.time()
        response_id = str(uuid.uuid4())
        
        try:
            # Step 1: Prepare biomarker context
            context = self._prepare_biomarker_context(request)
            
            # Step 2: Check cache for instant responses (future enhancement)
            cached_response = self._check_response_cache(request.message, context)
            if cached_response:
                return self._format_cached_response(cached_response, response_id, start_time)
            
            # Step 3: Generate AI response using existing LLM service
            prompt = self._create_health_assistant_prompt(request, context)
            ai_response = await get_llm_response(prompt, max_tokens=350)
            
            if not ai_response:
                raise Exception("Failed to get response from AI service")
            
            # Step 3.5: Optimize response length if needed
            ai_response = self._optimize_response_length(ai_response)
            
            # Step 4: Process and format response
            response = self._process_ai_response(ai_response, request, response_id, start_time)
            
            # Step 5: Track usage metrics
            self._track_usage(request.profile_id, response.token_usage, False)
            
            return response
            
        except Exception as e:
            logger.error(f"Chat service error: {str(e)}")
            return self._create_error_response(response_id, str(e), start_time)
    
    def _prepare_biomarker_context(self, request: ChatRequest) -> Dict[str, Any]:
        """
        Prepare optimized biomarker context using existing patterns.
        Applies Phase 2+ optimization for token reduction.
        """
        context = {
            "relevant_biomarkers": [],
            "abnormal_count": 0,
            "favorites_count": 0,
            "health_score_available": False
        }
        
        if not request.biomarker_context:
            return context
        
        # Filter and prioritize biomarkers
        for biomarker in request.biomarker_context.relevant_biomarkers:
            biomarker_dict = biomarker.model_dump()  # Use model_dump instead of dict()
            
            # Include abnormal biomarkers (highest priority)
            if biomarker.is_abnormal:
                context["relevant_biomarkers"].append(biomarker_dict)
                context["abnormal_count"] += 1
                # Also count if it's a favorite
                if biomarker.is_favorite:
                    context["favorites_count"] += 1
            # Include favorites (medium priority)
            elif biomarker.is_favorite:
                context["relevant_biomarkers"].append(biomarker_dict)
                context["favorites_count"] += 1
            # Include up to 5 normal biomarkers for context
            elif len(context["relevant_biomarkers"]) < 15:
                context["relevant_biomarkers"].append(biomarker_dict)
        
        # Optional Health Score context
        if (self.feature_flags.health_score_integration and 
            request.biomarker_context.health_score_context):
            context["health_score"] = request.biomarker_context.health_score_context.model_dump()
            context["health_score_available"] = True
        
        return context
    
    def _create_health_assistant_prompt(self, request: ChatRequest, context: Dict[str, Any]) -> str:
        """
        Create optimized prompt for Claude API with biomarker context.
        Implements medical guidelines and cost optimization.
        """
        system_prompt = """You are a Biomarker Health Assistant. Give direct, personalized health advice.

CRITICAL RULES:
- NEVER start with "Here is..." or "This is..." or similar meta-commentary
- Go straight to answering the user's question
- Use proper formatting with line breaks and bullet points
- Reference the user's specific biomarker values when relevant
- Keep under 150 words total

RESPONSE FORMAT:
[Brief personalized explanation based on their values]

Key recommendations:
• [Specific action 1]
• [Specific action 2] 
• [Specific action 3]

Note: Consult your healthcare provider for personalized medical advice.

CAPABILITIES:
- Explain biomarker values and significance
- Provide targeted diet, exercise, and lifestyle recommendations
- Reference user's specific values and trends

LIMITATIONS:
- NO medical diagnoses or medication recommendations
- Always include healthcare provider disclaimer"""

        # Optimize biomarker context (reduce verbosity)
        biomarker_context = ""
        if context["relevant_biomarkers"]:
            # Limit to top 5 most relevant biomarkers
            relevant_markers = context["relevant_biomarkers"][:5]
            biomarker_context = "\n\nYOUR BIOMARKER VALUES:\n"
            for biomarker in relevant_markers:
                status = "ABNORMAL" if biomarker["is_abnormal"] else "Normal"
                ref_range = f" (Normal: {biomarker.get('reference_range', 'N/A')})" if biomarker.get('reference_range') else ""
                trend = f" - {biomarker.get('trend', '')}" if biomarker.get('trend') else ""
                favorite = " ⭐" if biomarker.get("is_favorite") else ""
                biomarker_context += f"• {biomarker['name']}: {biomarker['value']} {biomarker['unit']} ({status}){ref_range}{trend}{favorite}\n"
        
        # Simplified Health Score context
        health_score_context = ""
        if context.get("health_score_available") and context.get("health_score"):
            hs = context["health_score"]
            health_score_context = f"\nHealth Score: {hs['current_score']}/100\n"
        
        # Minimal conversation context (last 2 messages only)
        conversation_context = ""
        if request.conversation_history:
            recent_messages = request.conversation_history[-2:]
            conversation_context = "\n\nContext:\n"
            for msg in recent_messages:
                # Truncate long messages for context
                content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                conversation_context += f"{msg.role}: {content}\n"
        
        # Combine with optimization
        full_prompt = f"""{system_prompt}
{biomarker_context}
{health_score_context}
{conversation_context}

USER QUESTION: {request.message}

Answer directly with personalized advice based on their specific biomarker values. Use proper formatting with bullet points. NO meta-commentary."""

        return full_prompt
    
    def _optimize_response_length(self, response: str) -> str:
        """
        Optimize response length for cost efficiency while maintaining quality.
        """
        # Clean up the response first
        response = response.strip()
        
        # Remove any meta-commentary that might have slipped through
        meta_phrases = [
            "Here is a concise response",
            "Here is some advice",
            "This is a response",
            "I'll provide",
            "Let me help you"
        ]
        
        for phrase in meta_phrases:
            if response.lower().startswith(phrase.lower()):
                # Find the first colon or period and start from there
                colon_pos = response.find(':')
                period_pos = response.find('.')
                start_pos = min([pos for pos in [colon_pos, period_pos] if pos > 0], default=len(phrase))
                response = response[start_pos + 1:].strip()
        
        # Ensure proper formatting by adding line breaks if missing
        if '•' in response and '\n' not in response:
            response = response.replace('•', '\n•')
        
        # If response is too long, intelligently truncate
        max_chars = 800  # Increased from 600 to allow full responses
        if len(response) > max_chars:
            # Check if we have important endings like disclaimers
            important_phrases = ["Note:", "Consult", "healthcare provider", "medical advice"]
            has_important_ending = any(phrase.lower() in response.lower()[-200:] for phrase in important_phrases)
            
            if has_important_ending:
                # Don't truncate if there's important disclaimer content
                max_chars = min(len(response), 1000)  # Allow longer for complete disclaimers
            
            if len(response) > max_chars:
                # Find the last complete sentence within limit
                truncated = response[:max_chars]
                last_period = truncated.rfind('.')
                last_exclamation = truncated.rfind('!')
                last_question = truncated.rfind('?')
                
                # Find the latest sentence ending
                last_sentence_end = max(last_period, last_exclamation, last_question)
                
                if last_sentence_end > max_chars * 0.7:  # If we have at least 70% of content
                    response = response[:last_sentence_end + 1]
                else:
                    # Fallback: truncate and add ellipsis
                    response = response[:max_chars - 3] + "..."
        
        return response.strip()
    
    def _process_ai_response(self, ai_response: str, request: ChatRequest, 
                           response_id: str, start_time: float) -> ChatResponse:
        """Process AI response and extract biomarker references"""
        
        # Extract biomarker references mentioned in response
        biomarker_refs = self._extract_biomarker_references(ai_response, request.biomarker_context)
        
        # Generate follow-up suggestions
        follow_ups = self._generate_follow_up_suggestions(ai_response, request.biomarker_context)
        
        # Calculate response time and estimate token usage
        response_time_ms = int((time.time() - start_time) * 1000)
        estimated_tokens = self._estimate_token_usage(ai_response)
        
        return ChatResponse(
            response=ai_response,
            biomarker_references=biomarker_refs,
            suggested_follow_ups=follow_ups,
            sources=["Evidence-based health recommendations"],
            response_id=response_id,
            is_from_cache=False,
            token_usage=int(estimated_tokens),
            response_time_ms=response_time_ms
        )
    
    def _extract_biomarker_references(self, response: str, biomarker_context) -> List[BiomarkerReference]:
        """Extract biomarker references mentioned in the AI response"""
        references = []
        
        if not biomarker_context:
            return references
        
        response_lower = response.lower()
        for biomarker in biomarker_context.relevant_biomarkers:
            biomarker_name_lower = biomarker.name.lower()
            if biomarker_name_lower in response_lower:
                references.append(BiomarkerReference(
                    name=biomarker.name,
                    value=biomarker.value,
                    unit=biomarker.unit,
                    is_abnormal=biomarker.is_abnormal,
                    reference_range=biomarker.reference_range
                ))
        
        return references
    
    def _generate_follow_up_suggestions(self, response: str, biomarker_context) -> List[str]:
        """Generate contextual follow-up questions"""
        suggestions = []
        
        # Basic follow-up suggestions based on content
        if "diet" in response.lower() or "nutrition" in response.lower():
            suggestions.append("What specific foods should I focus on?")
        
        if "exercise" in response.lower():
            suggestions.append("What type of exercise routine would you recommend?")
        
        if biomarker_context and biomarker_context.relevant_biomarkers:
            # Add biomarker-specific follow-ups
            abnormal_markers = [b for b in biomarker_context.relevant_biomarkers if b.is_abnormal]
            if abnormal_markers and len(abnormal_markers) > 1:
                suggestions.append("How are my abnormal biomarkers related to each other?")
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _check_response_cache(self, message: str, context: Dict[str, Any]) -> Optional[str]:
        """
        Check for cached responses (future enhancement).
        Currently returns None - implement when cache patterns are established.
        """
        # Future implementation: check biomarker cache for common question patterns
        return None
    
    def _format_cached_response(self, cached_response: str, response_id: str, start_time: float) -> ChatResponse:
        """Format cached response (future enhancement)"""
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            response=cached_response,
            biomarker_references=[],
            suggested_follow_ups=[],
            sources=["Cached health information"],
            response_id=response_id,
            is_from_cache=True,
            token_usage=0,
            response_time_ms=response_time_ms
        )
    
    def _create_error_response(self, response_id: str, error_msg: str, start_time: float) -> ChatResponse:
        """Create user-friendly error response"""
        response_time_ms = int((time.time() - start_time) * 1000)
        
        return ChatResponse(
            response="I'm sorry, I'm having trouble processing your request right now. Please try again in a moment. If the issue persists, you may want to consult with a healthcare professional about your biomarker questions.",
            biomarker_references=[],
            suggested_follow_ups=["Can you rephrase your question?", "Try asking about a specific biomarker"],
            sources=[],
            response_id=response_id,
            is_from_cache=False,
            token_usage=0,
            response_time_ms=response_time_ms
        )
    
    def _track_usage(self, profile_id: str, tokens: int, from_cache: bool):
        """Track usage metrics for cost monitoring with enhanced tracking"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if profile_id not in self.usage_metrics:
            self.usage_metrics[profile_id] = {}
        
        if today not in self.usage_metrics[profile_id]:
            self.usage_metrics[profile_id][today] = {
                "api_calls": 0,
                "tokens": 0,
                "cache_hits": 0,
                "total_requests": 0,
                "estimated_cost_usd": 0.0
            }
        
        metrics = self.usage_metrics[profile_id][today]
        metrics["total_requests"] += 1
        
        if from_cache:
            metrics["cache_hits"] += 1
        else:
            metrics["api_calls"] += 1
            metrics["tokens"] += tokens
            
            # Estimate cost (Claude 3 Sonnet pricing: ~$15/1M input + $75/1M output tokens)
            # Assuming 50/50 split, average ~$45/1M tokens
            cost_per_token = 45.0 / 1_000_000
            metrics["estimated_cost_usd"] += tokens * cost_per_token
        
        # Log usage if approaching limits
        daily_tokens = metrics["tokens"]
        daily_cost = metrics["estimated_cost_usd"]
        
        # Warning thresholds
        if daily_tokens > 10000:  # 10K tokens per day
            logger.warning(f"High token usage for profile {profile_id}: {daily_tokens} tokens, ${daily_cost:.4f}")
        
        if daily_cost > 1.0:  # $1 per day
            logger.warning(f"High cost for profile {profile_id}: ${daily_cost:.2f}")
            
        logger.info(f"Chat usage - Profile: {profile_id}, Today: {daily_tokens} tokens, ${daily_cost:.4f}")
    
    async def get_suggestions(self, profile_id: str) -> ChatSuggestionsResponse:
        """Generate contextual question suggestions based on user's biomarker profile"""
        
        # Get user's biomarker data (simplified for MVP)
        suggestions = []
        
        # Add general suggestions from biomarker cache patterns
        general_questions = [
            SuggestedQuestion(question="What do my abnormal biomarkers mean?", category="abnormal", priority=1),
            SuggestedQuestion(question="How can I improve my cholesterol levels?", category="general", priority=2),
            SuggestedQuestion(question="What dietary changes would help my biomarkers?", category="general", priority=3),
            SuggestedQuestion(question="Are my biomarker trends improving?", category="general", priority=4),
        ]
        
        # Add Health Score suggestions if enabled
        if self.feature_flags.health_score_integration:
            general_questions.append(
                SuggestedQuestion(question="How can I improve my overall health score?", category="health_score", priority=2)
            )
        
        suggestions.extend(general_questions)
        
        welcome_message = "Hi! I'm your biomarker health assistant. I can help you understand your lab results and suggest lifestyle improvements. What would you like to know?"
        
        return ChatSuggestionsResponse(
            suggestions=suggestions,
            welcome_message=welcome_message
        )
    
    def get_usage_metrics(self, profile_id: str) -> Optional[UsageMetrics]:
        """Get usage metrics for cost monitoring"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        if profile_id not in self.usage_metrics or today not in self.usage_metrics[profile_id]:
            return None
        
        metrics = self.usage_metrics[profile_id][today]
        cache_hit_rate = (metrics["cache_hits"] / metrics["total_requests"]) * 100 if metrics["total_requests"] > 0 else 0
        
        return UsageMetrics(
            daily_api_calls=metrics["api_calls"],
            daily_tokens=metrics["tokens"],
            cache_hit_rate=cache_hit_rate,
            average_response_time=0.0,  # Calculate if needed
            estimated_daily_cost_usd=metrics.get("estimated_cost_usd", 0.0),
            date=today
        )
    
    def _estimate_token_usage(self, text: str) -> int:
        """
        Estimate token usage for cost tracking.
        More accurate estimation than simple word count.
        """
        # Claude tokenization approximation:
        # - Average 3.5 characters per token
        # - Punctuation and spaces count as tokens
        # - Scientific terms and numbers may use more tokens
        
        char_count = len(text)
        word_count = len(text.split())
        
        # Base estimation: ~0.75 tokens per word (more accurate than 1.3)
        base_tokens = word_count * 0.75
        
        # Add tokens for punctuation and special characters
        punctuation_tokens = text.count('.') + text.count(',') + text.count('!') + text.count('?')
        
        # Medical/scientific terms tend to use more tokens
        scientific_indicators = text.lower().count('mg/dl') + text.lower().count('cholesterol') + text.lower().count('glucose')
        scientific_bonus = scientific_indicators * 0.5
        
        total_tokens = base_tokens + punctuation_tokens + scientific_bonus
        
        return max(int(total_tokens), 1)  # Minimum 1 token

# Global chat service instance
chat_service = ChatService() 