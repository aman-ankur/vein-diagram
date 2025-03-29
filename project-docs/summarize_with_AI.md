I need to implement a "Summarize with AI" feature for our lab report analyzer application. This feature will allow users to get detailed, personalized explanations of each biomarker by clicking an AI button next to each biomarker entry.

## Feature Overview
When a user clicks on an AI icon next to a biomarker, the app should:
1. Send the biomarker name, value, reference range, and status to our backend
2. The backend calls an LLM (like Claude) to generate two explanations:
   - A general explanation of what the biomarker measures and its significance
   - A personalized interpretation of the user's specific value and what it might indicate
3. Display this information in an elegant overlay/modal on the same screen

## UI/UX Implementation
1. Add an AI icon button next to each biomarker row:
   - Use a subtle AI icon (brain, sparkle, or similar icon) that doesn't crowd the interface
   - Position it consistently at the end of each row, before or after the Category column
   - Add a hover tooltip that says "Explain with AI"

2. Create an overlay modal for displaying AI explanations:
   - Design a clean, accessible modal that appears centered on screen
   - Include clear sections for "About this Biomarker" and "Your Results Explained"
   - Use appropriate typography with headers and readable body text
   - Add a loading state with an elegant spinner while waiting for the AI response
   - Include a close button and allow closing by clicking outside the modal or pressing ESC

3. UI Improvements to existing biomarker display:
   - Add subtle hover effects to each biomarker row to improve interactivity
   - Consider a more visually distinct status indicator (current Normal tags look a bit flat)
   - Add the ability to "star" or "bookmark" important biomarkers for quick reference
   - Consider adding a subtle icon indicating trend (up/down arrow) if we have historical data

## Backend Implementation
1. Create a new API endpoint:
POST /api/biomarkers/{biomarker_id}/explain
- This endpoint should accept a payload with biomarker details
- It should call the LLM with an appropriate prompt
- Return the formatted explanation

2. Implement the LLM prompt engineering:
- Create a template that structures how we ask the LLM for explanations
- Include clear instructions to provide both general information and personalized insights
- Ensure medical accuracy with appropriate disclaimers
- Structure the response format for consistent frontend rendering

3. Add caching for biomarker explanations:
- Store general biomarker explanations to avoid redundant LLM calls
- Only request personalized interpretations for specific values
- Implement TTL on cache entries to refresh explanations periodically

## Sample LLM Prompt Template
You are a helpful medical assistant explaining lab results to patients.
Please provide information about the biomarker {biomarker_name} with:

A brief, clear explanation of what this biomarker measures and why it's important (2-3 sentences)
What typical values indicate (1 sentence)
An analysis of the patient's value: {value} {unit} (Reference Range: {reference_range}, Status: {status})
What this specific result might indicate (2-3 sentences)
When someone might want to discuss this result with their doctor (1-2 sentences)

Format your response with two clearly labeled sections:
ABOUT_THIS_BIOMARKER: [general explanation]
YOUR_RESULTS: [personalized analysis]
Keep language accessible to non-medical professionals while being accurate.

## Implementation Steps

1. Frontend Changes:
   - Modify the BiomarkerRow component to include the AI explanation button
   - Create a new ExplanationModal component for displaying the results
   - Add state management for tracking which biomarker is being explained
   - Implement the API service call to fetch explanations
   - Add loading states and error handling

2. Backend Changes:
   - Create the new API endpoint in the FastAPI router
   - Implement the LLM service connection
   - Design the prompt template and response parser
   - Add caching logic for previously explained biomarkers
   - Implement error handling and logging

3. Testing:
   - Test the UI components in isolation
   - Test API endpoints with mock data
   - Test the end-to-end flow with real biomarker data
   - Verify the modal behavior on different screen sizes
   - Test keyboard accessibility

## Specific Files to Update

1. Frontend:
   - src/components/BiomarkerTable/BiomarkerRow.tsx (add AI button)
   - src/components/Modals/ExplanationModal.tsx (new component)
   - src/services/api.ts (add new API method)
   - src/hooks/useBiomarkerExplanation.ts (optional new hook)
   - src/styles/components/modal.css (styling for modal)

2. Backend:
   - app/routers/biomarkers.py (add new endpoint)
   - app/services/llm_service.py (handle LLM interactions) [ maybe change name]
   - app/models/schemas.py (add explanation request/response models)

Before implementing, please review the project structure and existing components to ensure consistency. Test each change thoroughly and make sure the UI is responsive across different device sizes.

Think carefully about error states and edge cases, such as:
- What happens if the LLM service is unavailable?
- How do we handle biomarkers with incomplete information?
- How do we ensure medical information is presented with appropriate disclaimers?

Provide a working implementation with thorough testing and clear documentation.