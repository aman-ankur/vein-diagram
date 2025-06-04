# Technical Specification: Biomarker Insights Chatbot

## Overview
This document outlines the technical implementation plan for the Biomarker Insights Chatbot feature. The chatbot will provide personalized health insights and recommendations based on users' biomarker data, presented through a conversational interface.

## Architecture
graph TD
    User[User] --> ChatUI[Chat Interface]
    ChatUI --> ChatService[Chat Service]
    ChatService --> ContextPrep[Context Preparation]
    ContextPrep --> ClaudeAPI[Claude API]
    ClaudeAPI --> ResponseFormat[Response Formatting]
    ResponseFormat --> ChatUI
    
    ContextPrep --> ProfileData[Profile & Biomarkers]
    ContextPrep --> HealthScore[Health Score - Optional]
    
    ChatService --> SimpleCache[Simple Response Cache]
    SimpleCache --> CommonResponses[Common Q&A Cache]

### Component Structure
frontend/src/
├── components/
│   ├── chat/
│   │   ├── ChatBubble.tsx             # Persistent bubble UI
│   │   ├── ChatWindow.tsx             # Main chat interface
│   │   ├── ConversationView.tsx       # Message history display
│   │   ├── MessageInput.tsx           # User input handling
│   │   ├── TypingIndicator.tsx        # Loading state
│   │   ├── BiomarkerMention.tsx       # Highlight biomarker references
│   │   ├── QuickQuestions.tsx         # Suggested questions
│   │   └── FeedbackButtons.tsx        # Simple thumbs up/down
│   └── ...
├── services/
│   ├── chatService.ts                 # Primary chat API service
│   └── conversationUtils.ts           # Chat helper functions
├── hooks/
│   ├── useChat.ts                     # Main chat state management
│   ├── useBiomarkerContext.ts         # Biomarker data for chat
│   └── useConversationHistory.ts      # Simple conversation memory
└── types/
    ├── chat.ts                        # Chat-specific types
    └── conversation.ts                # Conversation flow types

### Backend Structure
backend/app/
├── api/routes/
│   └── chat_routes.py                 # Single chat endpoint
├── services/
│   ├── chat_service.py                # Core chat logic
│   ├── biomarker_context_service.py   # Context preparation
│   └── response_cache_service.py      # Simple caching (optional)
├── schemas/
│   └── chat_schema.py                 # Request/response models
└── prompts/
    ├── system_prompts.py              # Health assistant prompts
    └── context_templates.py           # Biomarker context formatting


# Data Flow

---

## Chat Initialization

* User clicks chat bubble
* Frontend fetches active profile's **biomarker data** via existing `profileService`
* Frontend generates **suggested questions** based on abnormal biomarkers and user favorites
* Chat window opens with personalized welcome message and contextual question suggestions
* Display typing indicator while loading initial context

---

## Message Exchange

* User submits a question through message input
* Frontend sends request to `/api/chat` endpoint with:
    * User message
    * Active profile ID
    * Relevant biomarkers (abnormal + favorites + query-mentioned)
    * Simple conversation history (last 5-10 messages for context)
    * Optional Health Score context (if query relates to overall health)
* Backend processes request:
    * **Step 1:** Prepare biomarker context from user's profile data
    * **Step 2:** Optional - Check simple response cache for common questions
    * **Step 3:** Create health assistant prompt with biomarker context
    * **Step 4:** Call Claude API with structured prompt
    * **Step 5:** Format response and identify biomarker references
    * **Step 6:** Optional - Cache response if it's a common question pattern
* Frontend receives response and displays formatted message
* Frontend highlights mentioned biomarkers in the response
* Frontend shows suggested follow-up questions based on response content

---

## Conversation Continuity

* Frontend maintains conversation history in **session/localStorage** for persistence across browser sessions
* Each new message includes recent conversation context for Claude
* User can reference previous parts of conversation naturally
* Clear conversation button allows users to reset context when needed
* **Session Management**: Conversations persist until user explicitly clears or session expires
* **Storage Strategy**: Use sessionStorage for current session, localStorage for longer persistence
* **Context Limits**: Maintain last 10-15 messages for API context, store full history locally

---

## Feedback Flow

* User provides thumbs up/down feedback on assistant responses
* Feedback is sent to backend with message context for quality tracking
* Backend logs feedback for future prompt improvements
* No immediate response changes in MVP (feedback used for analysis)

---

## Error Handling

* API timeout or failure shows user-friendly error message
* Retry mechanism for failed requests
* Graceful degradation when biomarker context is unavailable
* Clear error states with option to try again

# API Endpoints

---

## Frontend-to-Backend

### `POST /api/chat` (Primary endpoint)

* **Purpose**: Main chat interaction endpoint for sending user messages and receiving AI responses.

* **Request**:

    ```typescript
    {
      message: string;                    // User's question or message
      profileId: string;                  // Active profile UUID
      conversationHistory?: Array<{       // Recent conversation context
        role: "user" | "assistant";
        content: string;
        timestamp: string;
      }>;
      biomarkerContext?: {                // Relevant biomarker data
        relevantBiomarkers: Array<{
          name: string;
          value: number;
          unit: string;
          reference_range: string;
          is_abnormal: boolean;
          trend?: "improved" | "worsened" | "stable";
          isFavorite?: boolean;           // User's favorite markers
        }>;
        healthScoreContext?: {            // Optional health score integration
          currentScore: number;
          influencingFactors: string[];
          trend: string;
        };
      };
    }
    ```

* **Response**:

    ```typescript
    {
      response: string;                   // AI assistant's response
      biomarkerReferences?: Array<{       // Biomarkers mentioned in response
        name: string;
        value: number;
        unit: string;
        isAbnormal: boolean;
      }>;
      suggestedFollowUps?: string[];      // Natural follow-up questions
      sources?: string[];                 // General health information sources
      responseId: string;                 // For feedback tracking
    }
    ```

---

### `GET /api/chat/suggestions/{profileId}`

* **Purpose**: Generate contextual question suggestions based on the user's biomarker profile.

* **Response**:

    ```typescript
    {
      suggestions: Array<{
        question: string;
        category: "abnormal" | "favorites" | "general" | "health_score";
        priority: number;                 // Display order priority
      }>;
      welcomeMessage: string;             // Personalized greeting
    }
    ```

---

### `POST /api/chat/feedback`

* **Purpose**: Collect user feedback on assistant responses for quality improvement.

* **Request**:

    ```typescript
    {
      responseId: string;                 // Links to specific response
      isHelpful: boolean;                 // Simple thumbs up/down
      feedbackType?: "accuracy" | "clarity" | "completeness" | "actionability";
      comment?: string;                   // Optional detailed feedback
    }
    ```

* **Response**:

    ```typescript
    {
      success: boolean,
      message: string
    }
    ```

---

## Backend-to-Claude API

The backend uses the existing Claude API integration with health-specific prompting:

* **System Prompt Structure**: Health assistant role with biomarker expertise and clear medical disclaimers.
* **Context Inclusion**: User's relevant biomarker data formatted for Claude understanding.
* **Response Guidelines**: Focus on lifestyle recommendations, avoid medical advice, provide actionable insights.
* **Safety Guardrails**: Detect and redirect medical questions requiring professional consultation.

---

## Optional Enhancement Endpoints (Future)

### `GET /api/chat/common-questions`

* **Purpose**: Retrieve frequently asked questions for quick access.

* **Response**: Array of common biomarker-related questions with categories.

---

### `POST /api/chat/clear-history/{profileId}`

* **Purpose**: Clear conversation history for privacy or context reset.

* **Response**:

    ```typescript
    {
      success: boolean
    }
    ```

### Backend-to-Claude API Integration

The backend integrates with the Claude API using existing health assistant patterns, prioritizing simplicity and a user-focused approach.

---

### Core Chat Service Architecture

* **Primary Service**: `ChatService` class handles all chat interactions.
* **Dependencies**: `HealthScoreService` (existing), `SimpleResponseCache` (optional lightweight caching).
* **Cache Strategy**: Optional simple cache for common questions only (if they occur with >20% user frequency).
* **Context Preparation**: Straightforward biomarker filtering focused on abnormal, favorites, and recently mentioned biomarkers.
* **Prompt Creation**: Health assistant role with biomarker context and conversation history.
* **Response Processing**: Formats the Claude response and identifies biomarker references for highlighting on the frontend.

---

### Claude API Integration Pattern

* **System Prompt Structure**:
    * Defines the health assistant role with biomarker expertise.
    * Includes clear **medical disclaimers** and boundaries (e.g., no medication advice).
    * Focuses on lifestyle recommendations and actionable insights.
    * Implements **safety guardrails** for detecting medical questions that require professional consultation.

* **Context Inclusion Strategy**:
    * User's **relevant biomarker data** (abnormal, favorites, and conversation-mentioned).
    * Optional **Health Score context** (if the query relates to overall health).
    * Recent **conversation history** (last 10 messages for continuity).
    * User profile context (age, gender, if relevant to biomarker interpretation).

* **Response Guidelines**:
    * Provides both general biomarker information and **personalized insights**.
    * Focuses on **diet, exercise, supplements, and lifestyle modifications**.
    * Includes appropriate disclaimers for health-related suggestions.
    * Identifies biomarker names mentioned for frontend highlighting.

---

### State Management

### Frontend State Architecture

* **Core Chat State**:
    * Chat visibility toggle and UI state management.
    * Message array with user/assistant conversations.
    * Loading states with typing indicators.
    * Error handling with user-friendly messages.
    * Simple feedback tracking (which messages received thumbs up/down).

* **Context State Management**:
    * Active profile integration via existing `ProfileContext`.
    * Health Score context when available and relevant.
    * User's favorite biomarkers for prioritized context.
    * Suggested questions based on the current biomarker profile.

* **State Management Approach**:
    * **Component-level state** using React hooks (no global state needed for MVP).
    * Custom `useChat` hook for main chat functionality.
    * Integration hooks for profile, health score, and favorites data.
    * Simple conversation history maintained in component state.

---

### Chat Context Preparation Strategy

* **Biomarker Filtering Logic**:
    * Always includes **abnormal biomarkers** (out of reference range).
    * Includes the user's **favorite biomarkers** (marked in profile).
    * Includes biomarkers **recently mentioned** in the conversation.
    * Excludes biomarkers not relevant to the current conversation.

* **Health Score Integration**:
    * Includes Health Score context **only when the query relates to overall health**.
    * Limits context to current score, top 3 influencing factors, and trend direction.
    * Avoids overwhelming context with full Health Score details.

* **Conversation Memory**:
    * Maintains the last 10 messages for context continuity.
    * Includes message roles (user/assistant) and timestamps.
    * Resets context when the user explicitly starts a new conversation.

---

### Technical Considerations

### Performance Optimizations (Selective Implementation)

* **Simple Response Caching**:
    * Leverages existing biomarker cache (125+ patterns) for instant responses
    * Profile-agnostic caching for general biomarker information
    * **No Additional Caching**: Use existing cache infrastructure
    * **Future Enhancement**: Cache expansion ready for user-specific patterns

* **Context Efficiency**:
    * Uses existing biomarker filtering from Phase 2+ optimizations
    * Limits conversation history to essential recent messages (stored in localStorage)
    * **Health Score Context**: Conditionally included when feature enabled
    * **Local Storage Management**: Efficient storage with automatic cleanup

* **Conversation Persistence**:
    * **SessionStorage**: Current conversation for immediate context
    * **LocalStorage**: Longer-term conversation history with size limits
    * **Automatic Cleanup**: Remove old conversations based on age/size
    * **Privacy Controls**: User option to clear stored conversations

---

### API Cost Management (Minimal & Practical)

* **Usage Monitoring**:
    * Simple daily API call tracking per user (monitoring only)
    * Token usage tracking for monitoring purposes (background metrics)
    * **Future-Ready Architecture**: Code structure supports easy addition of hard limits
    * Cost alerting for administrative monitoring only
    * **Limit Implementation Ready**: Service layer designed for easy rate limiting addition

* **Efficient Context Preparation**:
    * Includes only essential biomarker information (name, value, unit, normal/abnormal status)
    * Avoids redundant context data in sequential messages
    * Compresses conversation history to key exchanges
    * Optional content optimization (only if costs become significant)

* **Budget Controls (Future-Ready)**:
    * **Architecture Prepared**: Service layer supports configurable daily/monthly limits
    * **Graceful Degradation**: Framework ready for limit-based fallbacks
    * **Queue System Ready**: Infrastructure supports request queuing
    * **Premium Features**: Architecture supports usage-based feature tiers

---

### Security & Privacy (Straightforward Approach)

* **Data Handling**:
    * No permanent conversation storage (session-only chat history).
    * Minimal biomarker data transmission (relevant subset only).
    * Input sanitization and validation before API calls.
    * Generic error messages without internal system details.

* **User Privacy**:
    * Chat sessions tied to user profiles but not permanently stored.
    * Biomarker data included only for active conversation context.
    * Feedback data anonymized for quality improvement.
    * Clear user controls for conversation reset and privacy.

---

### Integration Points (Natural & Simple)

* **Health Score Integration (Optional)**:
    * **MVP Approach**: Health Score integration disabled by default
    * **Architecture Ready**: Code structure supports easy Health Score activation
    * **Future Implementation**: Context preparation includes Health Score when enabled
    * **Progressive Enhancement**: Chat suggestions can include Health Score factors when available
    * **Feature Flag**: Environment variable controls Health Score integration

* **Biomarker Visualization Integration**:
    * Click-to-chat from biomarker visualizations and tables.
    * Context-aware questions based on currently viewed biomarkers.
    * Seamless transition from visual data exploration to conversational insights.
    * Suggested questions generated from abnormal biomarker patterns.

* **Profile Context Integration**:
    * Automatic profile context switching when the user changes active profile.
    * Profile-specific conversation suggestions and welcome messages.
    * Integration with existing favorite biomarkers functionality.
    * Natural multi-profile support for family health management.

---

### Optional Enhancement Strategy (Future Implementation)

* **Advanced Caching** (implement only if usage patterns justify complexity):
    * Biomarker pattern matching for similar user contexts.
    * Learning algorithms for improving response quality over time.
    * Advanced token optimization using existing Phase 2+ infrastructure.
    * Predictive caching based on user behavior patterns.

* **Enhanced Analytics** (implement based on user feedback needs):
    * Conversation quality metrics and user satisfaction tracking.
    * Biomarker mention frequency for improving suggestion algorithms.
    * Response accuracy validation through user feedback analysis.
    * Cost optimization opportunities identification through usage analysis.

## Technical Risks & Mitigations
| Risk                   | Mitigation                                                    |
| :--------------------- | :------------------------------------------------------------ |
| Claude API latency     | Implement appropriate loading states and timeout handling       |
| Context window limits  | Summarize biomarker data, prioritize abnormal values          |
| Browser compatibility  | Use well-supported web standards, test across browsers        |
| Mobile responsiveness  | Design mobile-first, test on multiple screen sizes            |
| API cost overruns      | Implement usage monitoring, rate limits, and optimized prompts |

# Testing Approach

---

## Priority 1: Core Functionality Testing

### Unit Tests (Essential)

* **Chat message handling** and state management with **mocked Claude API responses**
* **Biomarker context preparation** and filtering logic using existing cache data
* **Conversation history management** with localStorage/sessionStorage
* **Error handling** for API failures and network issues with mock scenarios
* **Input validation** and sanitization with test cases

### Component Tests (Critical)

* **ChatBubble activation** and visibility states with mock data
* **ChatWindow rendering** with different message types and mock responses
* **Message input handling** and submission with mocked API calls
* **Biomarker reference highlighting** in mock responses
* **Suggested questions** generation from existing biomarker cache

### Integration Tests (Important)

* **End-to-end message flow** with **mocked Claude API** for consistent testing
* **Profile context switching** and data consistency with existing ProfileService
* **Health Score integration** (when enabled) with mock Health Score data
* **Conversation continuity** across multiple exchanges with localStorage
* **Error recovery** and retry mechanisms with simulated failures

### API Testing Strategy

* **Primary Approach**: Mock Claude API responses for consistent, fast testing
* **Fallback**: Test API key for integration validation if mocking insufficient
* **Mock Response Library**: Create comprehensive mock responses covering edge cases
* **Real API Validation**: Periodic integration tests with actual Claude API

---

## Priority 2: User Experience Testing

### Usability Testing

* **Chat discovery** and initial user interaction.
* **Conversation flow naturalness** and clarity.
* **Mobile vs. desktop** chat experience.
* **Accessibility compliance** (screen readers, keyboard navigation).
* **User feedback mechanism** effectiveness.

### Cross-Browser Testing

* **Chat functionality** across major browsers (Chrome, Firefox, Safari, Edge).
* **Mobile browser compatibility** and responsive design.
* **Chat window positioning** and overlay behavior.
* **Message rendering** and formatting consistency.

### Performance Testing

* **Response time measurement** under normal load.
* **Chat window opening** and closing performance.
* **Message history loading** and scrolling behavior.
* **Memory usage** during extended conversations.

---

## Priority 3: Integration Testing

### API Integration Testing

* **Claude API call formatting** and response handling.
* **Biomarker context preparation** accuracy.
* **Conversation history inclusion** in API calls.
* **Error handling** for API timeout and failure scenarios.

### Service Integration Testing

* **ProfileService integration** and data consistency.
* **HealthScoreService integration** when applicable.
* Existing **authentication and authorization** flow.
* **Data privacy and security** compliance.

### Data Flow Testing

* **Biomarker data accuracy** in chat context.
* **Profile switching impact** on conversation context.
* **Favorite biomarkers prioritization** in responses.
* **Health Score factor explanation** accuracy.

---

## Priority 4: Optional Feature Testing (Only if Implemented)

### Caching Testing (if enabled)

* **Cache hit/miss scenarios** for common questions.
* **Cache invalidation** and data freshness.
* **Performance impact** of caching layer.
* **Cache storage and retrieval** accuracy.

### Cost Optimization Testing (if implemented)

* **Token usage measurement** and optimization effectiveness.
* **Budget limit enforcement** and fallback behavior.
* **Context compression accuracy** and information preservation.
* **Rate limiting functionality** and user experience.

## Implementation Plan (Feature-First)

---

### Week 1: Core Chat Experience

* Build **chat UI components** with localStorage conversation persistence
* Implement basic **message exchange** with mocked Claude responses for testing
* Create **Claude API integration** with monitoring-only cost tracking
* Add **conversation history** with session/localStorage storage

---

### Week 2: Biomarker Intelligence

* Integrate **biomarker context** using existing 125+ cache patterns
* Implement smart **question suggestions** from cache data
* Add **biomarker highlighting** in responses
* Test **conversation quality** with comprehensive mock scenarios

---

### Week 3: Polish & Integration

* Add **optional Health Score integration** (feature-flagged)
* Implement **feedback mechanism** with localStorage tracking
* Improve **error handling** with graceful degradation
* Conduct **user testing** with mock and real API responses

---

### Week 4-5: Production Readiness

* **Testing Suite**: Comprehensive unit/integration tests with mocks
* **Performance Optimization**: Validate cost monitoring and response times
* **Accessibility Compliance**: Screen reader and keyboard navigation testing
* **Future-Ready Architecture**: Validate easy addition of usage limits and Health Score

---

## Success Metrics (User-Focused)

---

## Primary Metrics

* **User Satisfaction**: Conversation quality ratings.
* **Engagement**: Messages per session, return usage.
* **Utility**: Users report implementing suggestions.
* **Adoption**: Percentage of users who try the chat feature.

---

## Secondary Metrics

* **Response Accuracy**: Biomarker context correctness.
* **Conversation Flow**: Natural dialogue progression.
* **Error Rate**: Failed responses or confusion.

---

## Optimization Metrics (Only if Implemented)

* **Cost Efficiency**: Monthly API costs per active user.
* **Response Speed**: Average response time.

# Development Guidelines

---

## Core Principles

* **User Experience First**: Prioritize conversation quality and health insights over technical optimizations.
* **Start Simple**: Build essential chat functionality before adding any optimization layers.
* **Progressive Enhancement**: Add features based on user feedback and demonstrated need, not theoretical requirements.
* **Reuse Existing Patterns**: Leverage established services (`ProfileService`, `HealthScoreService`) and UI components.
* **Maintainable Code**: Favor readable, straightforward implementations over clever optimizations.

---

## Implementation Approach

* **Component Modularity**: Build self-contained chat components that integrate cleanly with existing UI.
* **Service Integration**: Use existing API patterns and service layers rather than creating parallel infrastructure.
* **State Management**: Keep chat state simple with React hooks; avoid complex global state management.
* **Error Boundaries**: Implement graceful error handling that doesn't break the main application flow.
* **Accessibility**: Ensure chat interface works with screen readers and keyboard navigation.

---

## Code Quality Standards

* **Type Safety**: Use TypeScript interfaces for all chat-related data structures.
* **Testing First**: Write tests for core chat functionality before implementing optimizations.
* **Documentation**: Document prompt engineering decisions and biomarker context preparation logic.
* **Feature Flags**: Use environment variables to enable/disable optional features (caching, optimizations).
* **Performance Monitoring**: Track basic metrics (response time, error rate) but avoid premature optimization.

---

## Integration Standards

* **Consistent UI**: Match existing design patterns and component styling.
* **Theme Integration**: Use existing color schemes and typography from the main application.
* **Navigation Flow**: Ensure chat doesn't disrupt existing user workflows or page navigation.
* **Data Consistency**: Maintain data integrity with existing profile and biomarker services.
* **Security Alignment**: Follow existing authentication and data privacy patterns.

## Dependencies

* Claude API (existing integration)
* Profile and Biomarker services (existing)
* UI component library (existing)
* D3.js (potentially for future data visualization within chat)