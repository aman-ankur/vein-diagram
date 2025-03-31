# Vein Diagram: Active Context

## Current Work Focus

The project is advancing with a focus on integrating user personalization features alongside core functionalities:

1.  **User Profile Management**: Implementing and refining the ability for users to manage multiple health profiles.
2.  **Favorite Biomarkers**: Allowing users to mark and easily access key biomarkers per profile.
3.  **Integration of Personalization**: Ensuring profile context and favorites are seamlessly integrated into visualizations and data history views.
4.  **Claude API Insights**: Continuing development of AI-generated explanations for biomarkers.
5.  **Visualization Enhancements**: Completing relationship mapping and improving interactivity.
6.  **UI/UX Refinement**: Improving overall usability, especially around new personalization features.

## Recent Changes

Significant recent developments include:

1.  **Profile Management Implementation**:
    *   Added backend API endpoints (FastAPI) for CRUD operations on user profiles.
    *   Created database models (`profile_model.py`) and schemas (`profile_schema.py`) for profiles.
    *   Developed frontend components (`ProfileManagement.tsx`) and services (`profileService.ts`) for managing profiles.
    *   Implemented logic to associate uploaded PDF reports with specific user profiles.
    *   Added tests (`test_profile_routes.py`, `ProfileManagement.test.tsx`) for the new functionality.

2.  **Favorite Biomarkers Implementation**:
    *   Added backend API endpoints to manage favorite biomarkers linked to profiles.
    *   Updated database schemas to store favorite status.
    *   Created frontend components (`FavoriteBiomarkersGrid.tsx`, `AddFavoriteModal.tsx`, `BiomarkerTile.tsx`) to display and manage favorites.
    *   Implemented utility functions (`favoritesUtils.ts`) for handling favorite logic.

3.  **Enhanced PDF Processing & Claude Integration**:
    *   Continued refinement of Claude API prompts for extraction accuracy.
    *   Improved error handling and fallback mechanisms in the PDF processing pipeline.
    *   Maintained focus on OCR capabilities and reference range normalization.

4.  **Backend & Testing Improvements**:
    *   Refactored relevant backend services to accommodate profile context.
    *   Expanded test coverage to include profile and favorite interactions.

## Next Steps

The immediate priorities are:

1.  **Integrate Profile Context**:
    *   Modify `BiomarkerHistoryPage.tsx` and `VisualizationPage.tsx` to display data based on the selected user profile.
    *   Ensure API calls fetch data filtered by the active profile.
    *   Update UI elements to clearly indicate the current profile context.

2.  **Refine Favorite Biomarkers UI**:
    *   Ensure seamless interaction for adding/removing favorites from various views (table, visualization).
    *   Optimize the display of the `FavoriteBiomarkersGrid.tsx`.

3.  **Claude API Insights Integration**:
    *   Develop frontend components to display AI-generated explanations effectively.
    *   Finalize prompts for generating insightful biomarker relationships based on user data.
    *   Implement caching for insights.

4.  **Visualization Development**:
    *   Complete the relationship mapping visualization component.
    *   Add interactive features (filtering, zooming) considering profile context.
    *   Ensure responsive design, especially for mobile views.

5.  **Frontend Enhancements**:
    *   Implement filtering and search functionality, potentially allowing filtering by profile.
    *   Enhance error handling and user feedback for profile/favorite actions.
    *   Implement loading states for asynchronous operations related to profiles/favorites.

6.  **Testing and Validation**:
    *   Conduct end-to-end testing of user flows involving profile switching, PDF uploads per profile, and favorite management.
    *   Perform usability testing focusing on the new personalization features.
    *   Validate accuracy of data display when switching between profiles.

## Active Decisions and Considerations

### Technical Decisions Under Consideration

1.  **State Management for Profile Context**:
    *   **Current Approach**: Likely using React Context or simple prop drilling for now.
    *   **Consideration**: Whether a more robust state management library (like Zustand or Redux Toolkit) is needed as complexity grows with profile switching affecting multiple components.
    *   **Trade-offs**: Simplicity vs. scalability and maintainability.
    *   **Status**: Monitoring complexity during integration.

2.  **Data Fetching Strategy**:
    *   **Current Approach**: Fetching data on component mount or user action.
    *   **Consideration**: Optimizing data fetching when switching profiles frequently. Caching strategies per profile.
    *   **Trade-offs**: Performance vs. data freshness.
    *   **Status**: Implementing basic fetching first, optimizing later based on performance testing.

3.  **Data Visualization Library**: (Ongoing)
    *   **Current Approach**: Using D3.js for custom visualizations. Recharts/Chart.js potentially for simpler charts.
    *   **Consideration**: Still evaluating the best fit for relationship mapping complexity vs. ease of integration.
    *   **Status**: Proceeding with D3 for complex views, may use others for simpler ones.

### UX Considerations

1.  **Profile Switching Clarity**:
    *   **Challenge**: Ensuring users always know which profile's data they are viewing.
    *   **Approach**: Prominent display of the active profile, clear visual cues during switching.
    *   **Status**: Design and implementation ongoing.

2.  **Managing Favorites**:
    *   **Challenge**: Making the process of adding/removing favorites intuitive across different contexts (tables, visualizations).
    *   **Approach**: Consistent iconography and interaction patterns. Modal (`AddFavoriteModal.tsx`) for adding, direct interaction on tiles/rows for removing.
    *   **Status**: Implemented, refining based on usability.

3.  **Onboarding for New Features**:
    *   **Challenge**: Introducing users to profile management and favorites without overwhelming them.
    *   **Approach**: Contextual hints or a brief guided tour upon first encountering the features.
    *   **Status**: Planning phase.

### Current Blockers

1.  **Frontend Integration Complexity**:
    *   **Issue**: Integrating the profile context deeply into existing pages (`BiomarkerHistoryPage`, `VisualizationPage`) requires significant refactoring.
    *   **Impact**: Slows down the delivery of a fully profile-aware user experience.
    *   **Mitigation**: Breaking down the integration into smaller, manageable steps. Prioritizing core data display first.
    *   **Status**: In progress, primary focus currently.

2.  **PDF Format Variability**: (Ongoing)
    *   **Issue**: While improved, new or unusual PDF formats can still pose extraction challenges.
    *   **Impact**: Affects data accuracy for some users.
    *   **Mitigation**: Continuous improvement of Claude prompts and fallback parser logic based on reported issues.
    *   **Status**: Managed, but requires ongoing attention.

3.  **Claude API Rate Limits/Costs**: (Ongoing)
    *   **Issue**: Potential bottleneck, especially if insights generation becomes heavy.
    *   **Mitigation**: Caching, prompt optimization, monitoring usage.
    *   **Status**: Monitoring.
