# Biomarker Insights Chatbot: Product Requirements Document

## 1. Feature Overview

**Feature Name:** Biomarker Insights Chatbot  

**Description:** An AI-powered conversational assistant that provides personalized health insights, recommendations, and explanations based on users' biomarker data, focusing on actionable lifestyle modifications rather than medical advice.

**Value Proposition:** Transforms static biomarker data into personalized, actionable health guidance through natural conversation, helping users understand connections between markers and implement evidence-based lifestyle changes.

## 2. User Personas & Use Cases

### Primary Personas:
- **Health Optimizers:** Users focused on optimizing wellbeing through data-driven decisions
- **Chronic Condition Managers:** Users monitoring specific markers related to ongoing health conditions

### Top Use Cases:
1. **Personalized Diet Recommendations:** "What dietary changes would help improve my cholesterol levels?"
2. **Marker Relationship Exploration:** "How does my Vitamin D level affect my calcium levels?"
3. **Improvement Strategies:** "What can I do to improve my fasting glucose?"
4. **Lifestyle Guidance:** "Based on my biomarkers, should I change my exercise routine?"
5. **Supplement Suggestions:** "Would any supplements help with my iron levels?"

## 3. Features & Functionality

### MVP (Phase 1) Features:
- Contextual awareness of user's current biomarker values
- Basic trend awareness (improved/worsened)
- Ability to answer questions about specific markers
- Personalized diet and lifestyle suggestions based on marker values
- General explanation of marker relationships
- Clear medical disclaimers and boundaries

### Future (Phase 2) Features:
- Conversation history storage and retrieval
- Integration of multimedia elements in responses (charts, images)
- More sophisticated trend analysis across all historical data
- Proactive suggestions based on significant changes in markers
- In-depth research references and citations

## 4. User Experience & Design

### Chat Interface:
- **Access Point:** Persistent chat bubble in bottom right corner of the application
  - Subtle but noticeable design (muted colors matching app theme)
  - Unobtrusive when not in use
  - Gentle pulse animation for first-time users to increase discovery

- **Chat Window:**
  - Expands to approximately 30% of screen width when activated
  - Maintains context of the current page (user can still see biomarker data)
  - Header includes clear "Health Assistant" label and disclaimer link
  - Two-column layout on desktop (chat on right, current view remains visible)
  - Full-screen modal with easy dismiss gesture on mobile

- **Conversation Elements:**
  - Welcome message explaining capabilities and limitations
  - User messages in right-aligned bubbles (app theme color)
  - Assistant responses in left-aligned bubbles (neutral color)
  - Typing indicator during response generation
  - Special formatting for biomarker references (highlight with current value)

- **Interaction Patterns:**
  - Text input field with send button
  - Suggested question chips based on abnormal biomarkers
  - "New Conversation" button to reset context
  - Simple thumbs up/down feedback after each assistant response

### Integration Points:
- **Dashboard:** Chat bubble persistent, suggested questions based on Health Score factors
- **Visualization Page:** Chat references visible biomarkers, option to ask about specific marker from visualization
- **Biomarker History:** Ability to reference historical patterns in conversation

## 5. Technical Requirements

### Data Access:
- Current profile's biomarker data (names, values, reference ranges)
- Basic trend information (improved/worsened from previous test)
- Biomarker categories and relationships
- Optimal ranges from configuration files

### API Integration:
- Claude API with appropriate context window size
- Structured prompting to include relevant biomarker data
- Response templating for consistent formatting

### Performance Considerations:
- Response time target: < 5 seconds for standard queries
- Graceful handling of API timeouts or failures
- Local caching of common response patterns

### Security & Privacy:
- No permanent storage of conversations in MVP
- Secure handling of biomarker data in prompts
- Clear session boundaries

## 6. Prompt Engineering

### System Prompt Components:
- Role definition as "Biomarker Health Assistant"
- Access to user's current biomarker values and basic trends
- Instruction to prioritize personalized responses over generic information
- Requirements to:
  1. Provide both general information and personalized insights
  2. Focus on diet, exercise, supplements, and lifestyle recommendations
  3. Avoid medical advice regarding medications or treatments
  4. Include appropriate disclaimers for health-related suggestions
  5. Recognize when a question requires medical consultation

### Guardrails:
- Explicit blocklist for medication recommendations
- Required disclaimer for serious health concerns
- Pattern detection for emergency medical questions
- Limitation acknowledgment for diagnostic questions

## 7. Implementation Plan

### Phase 1 (MVP):
1. **Basic Integration (Week 1-2):**
   - Set up UI components for chat bubble and window
   - Implement basic Claude API integration
   - Create initial prompt templates

2. **Biomarker Context (Week 3-4):**
   - Develop data preparation for including relevant biomarkers in context
   - Implement basic trend awareness (better/worse than last test)
   - Create biomarker reference highlighting in responses

3. **Refinement (Week 5-6):**
   - Add suggested questions based on abnormal markers
   - Implement feedback mechanism
   - Conduct internal testing and prompt optimization
   - Add disclaimers and safety measures

### Phase 2 (Future Enhancement):
1. Conversation history storage and management
2. Multimedia response capabilities
3. Advanced trend analysis and pattern recognition
4. Citation and reference integration
5. Personalization based on user feedback

## 8. Success Metrics

### Primary Metrics:
- **Engagement:** Percentage of users who interact with the chatbot after viewing biomarker results
- **Daily Active Users (DAU):** Tracking daily chatbot engagement
- **Session Length:** Average number of exchanges per conversation
- **User Satisfaction:** Percentage of positive feedback responses

### Secondary Metrics:
- Types of questions asked (categorized)
- Response time and quality
- Feature retention (do users return to the chatbot?)
- Impact on overall app retention and engagement

## 9. Limitations & Considerations

### Technical Limitations:
- LLM context window constraints may limit historical data inclusion
- API costs may scale with usage
- Response quality depends on the underlying model capabilities

### Ethical Considerations:
- All responses must respect medical boundaries
- Clear distinction between lifestyle guidance and medical advice
- Appropriate handling of sensitive health information

### Disclaimer Requirements:
Standard disclaimer: "This AI assistant provides general information about biomarkers and lifestyle guidance based on your test results. It is not a substitute for professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider for medical concerns."

## 10. Potential Challenges & Mitigations

| Challenge | Mitigation Strategy |
|-----------|---------------------|
| Inaccurate or harmful advice | Comprehensive prompt engineering with safety guardrails; clear disclaimers |
| User asking for out-of-scope medical advice | Pattern detection for medical questions; clear explanation of limitations |
| Context window limitations | Summarize historical data; prioritize most relevant markers |
| API costs | Implement usage limits; optimize prompt size |
| User expectations management | Clear onboarding about capabilities and limitations |

## 11. Questions & Decisions

1. **Historical Data Depth:** For MVP, include only current values and basic trend direction (improved/worsened) rather than full history. This balances personalization with technical constraints while providing sufficient context for meaningful recommendations.

2. **Chat Persistence:** The persistent chat bubble approach provides maximum accessibility while minimizing navigation disruption. The chat window should expand without navigating away from the current view to maintain context.

3. **Response Structure:** Responses will follow a consistent pattern:
   - Brief general information about the topic
   - Personalized insights based on the user's specific biomarker values
   - Actionable recommendations
   - Any necessary disclaimers