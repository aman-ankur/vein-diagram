# Technical Specification: Biomarker Insights Chatbot

## Overview
This document outlines the technical implementation plan for the Biomarker Insights Chatbot feature. The chatbot will provide personalized health insights and recommendations based on users' biomarker data, presented through a conversational interface.

## Architecture
**[Diagram/Description of Architecture - e.g., Client -> Backend API -> Claude API]**

### Component Structure
frontend/src/
├── components/
│   ├── chat/
│   │   ├── ChatBubble.tsx             # Persistent bubble UI
│   │   ├── ChatWindow.tsx             # Expandable chat interface
│   │   ├── ChatMessage.tsx            # Individual message component
│   │   ├── BiomarkerReference.tsx     # Highlighted biomarker mentions
│   │   ├── SuggestedQuestions.tsx     # Quick-access question buttons
│   │   └── ChatFeedback.tsx           # Thumbs up/down component
│   └── ...
├── services/
│   ├── chatService.ts                 # API interaction for chat
│   └── ...
├── contexts/
│   ├── ChatContext.tsx                # Manages chat state (if needed)
│   └── ...
├── pages/
│   └── ... (existing pages)
└── utils/
├── chatUtils.ts                   # Chat-related helper functions
└── biomarkerTrendUtils.ts         # Trend detection for biomarkers

### Backend Structure
backend/app/
├── api/
│   └── routes/
│       └── chat_routes.py             # Chat API endpoints
├── services/
│   └── chat_service.py                # Chat business logic
└── schemas/
    └── chat_schema.py                 # Pydantic models for chat


## Data Flow

1.  **Chat Initialization**:
    * User clicks chat bubble
    * Frontend fetches active profile's biomarker data via existing `profileService`
    * Chat window opens with welcome message

2.  **Message Exchange**:
    * User submits a question
    * Frontend sends request to `/api/chat` endpoint with:
        * User message
        * Relevant biomarker data
        * Active profile ID
        * Chat history context (if needed)
    * Backend processes request:
        * Formats prompt with biomarker context
        * Calls Claude API
        * Parses and formats response
        * Returns formatted response to frontend
    * Frontend displays the response with appropriate formatting

3.  **Feedback Flow**:
    * User provides thumbs up/down feedback
    * Feedback is sent to backend for potential future improvements
    * No immediate response processing changes (in MVP)

## API Endpoints

### Frontend-to-Backend

**POST /api/chat**
* Request:
    ```typescript
    {
      message: string;              // User's question
      profileId: string;            // Active profile UUID
      biomarkerContext?: {          // Pre-filtered relevant biomarkers
        biomarkers: Array<{
          name: string;
          value: number;
          unit: string;
          reference_range: string;
          is_abnormal: boolean;
          trend?: "improved" | "worsened" | "stable";
        }>;
      };
      conversationId?: string;      // For future history tracking (Phase 2)
    }
    ```
* Response:
    ```typescript
    {
      response: string;             // Formatted assistant response
      references?: Array<{          // Biomarker references in response (for highlighting)
        biomarker: string;
        value: number;
        unit: string;
      }>;
      suggestedQuestions?: string[]; // Follow-up question suggestions
    }
    ```

**POST /api/chat/feedback**
* Request:
    ```typescript
    {
      messageId: string;            // Specific message ID
      isPositive: boolean;          // Thumbs up (true) or down (false)
      comment?: string;             // Optional feedback comment (Phase 2)
    }
    ```
* Response: `{ success: boolean }`

### Backend-to-Claude API
The backend will use the existing Claude API integration, constructing prompts that include:

* System prompt with health assistant role definition and guardrails
* User biomarker context in structured format
* User query
* Limited conversation history (if needed)

## State Management
### Frontend State

* Chat visibility state
* Messages array
* Loading states
* Error states
* Feedback states

No need for global state management - component-level state (React hooks) should be sufficient for MVP.

## Technical Considerations
### Performance Optimizations

* Fetch only relevant biomarkers for context (limit to abnormal or mentioned)
* Implement debounce for user input
* Use loading indicators for long-running requests
* Consider caching common responses client-side

### API Cost Management

* Optimize prompt size to reduce token usage
* Track token usage per request for monitoring
* Set reasonable rate limits to prevent abuse

### Security & Privacy

* No sensitive biomarker data stored in logs
* Session-scoped conversations (no persistent storage in MVP)
* Validate all user inputs

### Integration Points

* Profile Context: Access the current active profile via the existing ProfileContext
* Biomarker Services: Use existing biomarkerService to fetch relevant data
* UI/Theme Integration: Leverage existing UI components and theming
* Authentication: Use existing auth context to ensure secure access

## Technical Risks & Mitigations
| Risk                   | Mitigation                                                    |
| :--------------------- | :------------------------------------------------------------ |
| Claude API latency     | Implement appropriate loading states and timeout handling       |
| Context window limits  | Summarize biomarker data, prioritize abnormal values          |
| Browser compatibility  | Use well-supported web standards, test across browsers        |
| Mobile responsiveness  | Design mobile-first, test on multiple screen sizes            |
| API cost overruns      | Implement usage monitoring, rate limits, and optimized prompts |

## Testing Approach

### Unit Tests:

* ChatBubble/ChatWindow component rendering
* Message formatting logic
* Biomarker trend detection utilities

### Integration Tests:

* API interaction flow
* Context passing between components
* Proper biomarker highlighting

### End-to-End Tests:

* Full conversation flow
* Error state handling
* Mobile vs. desktop behavior

## Phase 1 Implementation Plan
### Week 1-2: Core UI Components

* Create ChatBubble, ChatWindow, and message components
* Implement basic styling and animations
* Add placeholder functionality (no real API connection)

### Week 3-4: Data Integration

* Connect to biomarker data services
* Implement backend chat endpoint and Claude integration
* Create biomarker context preparation logic
* Test end-to-end with simple questions

### Week 5-6: Refinement

* Add suggested questions feature
* Implement feedback mechanism
* Add biomarker reference highlighting
* Add disclaimers and safety measures
* Conduct thorough testing across devices

## Development Guidelines

* Favor composability over complexity
* Reuse existing patterns and services where possible
* Maintain clean separation between UI, data fetching, and business logic
* Document all Claude prompt engineering details for future reference
* Use feature flags to enable incremental rollout
* Consider accessibility from the beginning

## Dependencies

* Claude API (existing integration)
* Profile and Biomarker services (existing)
* UI component library (existing)
* D3.js (potentially for future data visualization within chat)