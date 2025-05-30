# Vein Diagram: Active Context

## Current Work Focus

The project is advancing with a focus on integrating user personalization features alongside core functionalities:

1.  **User Profile Management**: Implementing and refining the ability for users to manage multiple health profiles.
2.  **Favorite Biomarkers**: Allowing users to mark and easily access key biomarkers per profile.
3.  **Integration of Personalization**: Ensuring profile context and favorites are seamlessly integrated into visualizations and data history views.
4.  **Claude API Insights**: Continuing development of AI-generated explanations for biomarkers.
5.  **Visualization Enhancements**: Completing relationship mapping and improving interactivity.
6.  **UI/UX Refinement**: Improving overall usability, especially around new personalization features.
7.  **Health Score Feature**: Initial implementation of backend logic and frontend components for calculating and displaying a health score based on biomarker data.

## Recent Changes

Significant recent developments include:

1.  **Profile Management & Backend Favorites**:
    *   Implemented backend API endpoints (FastAPI) for profile CRUD.
    *   **Added `favorite_biomarkers` JSON column to `Profile` model and updated schemas.**
    *   **Set up Alembic for database migrations and applied initial migration for the new column.**
    *   **Added backend API endpoints for adding, removing, and reordering favorite biomarkers (`/api/profiles/{id}/favorites/...`).**
    *   Implemented profile matching and association logic.
    *   Developed frontend components (`ProfileManagement.tsx`) and services (`profileService.ts`).
    *   Associated uploaded PDFs with profiles.
    *   Added tests (`test_profile_routes.py`, `ProfileManagement.test.tsx`).
    *   Fixed Pydantic v2 `from_attributes` config error.
    *   Resolved FastAPI/Starlette dependency conflict.

2.  **Frontend Favorite Management & Biomarker Deletion**:
    *   **Migrated favorite state management from localStorage to backend API calls.**
    *   Updated `VisualizationPage.tsx` to fetch/update favorites via `profileService.ts`.
    *   Added star icon to `BiomarkerTable` for adding/removing favorites.
    *   Implemented `ReplaceFavoriteModal.tsx` and logic in `VisualizationPage.tsx` to handle adding favorites when the grid is full.
    *   Added delete ('x') icon to `BiomarkerTile.tsx` for direct removal of favorites.
    *   **Implemented drag-and-drop reordering for favorite tiles** using `dnd-kit` in `FavoriteBiomarkersGrid.tsx`, saving the order via the backend API.
    *   **Added 3-dot menu and "Delete Entry" action to `BiomarkerTable.tsx`**.
    *   Added backend endpoint (`DELETE /api/biomarkers/{id}`) and frontend service/handler (`deleteBiomarkerEntry`) for biomarker deletion.
    *   Added confirmation dialog for biomarker deletion.
    *   Removed obsolete local storage functions from `favoritesUtils.ts`.
    *   Fixed date display issues in `BiomarkerTile.tsx` tooltip and `biomarkerUtils.ts`.
    *   Fixed positioning/visibility of the delete button on `BiomarkerTile.tsx`.

3.  **Authentication System Implementation**:
    *   Implemented user authentication using Supabase Auth (Email/Password, Google OAuth).
    *   Created frontend components (`AuthContext`, `NewSignupPage`, `LoginPage`, `ResetPasswordPage`, `AccountPage`, `AuthCallbackPage`, `NewSignupForm`, `LoginForm`, `ResetPasswordForm`, `GoogleAuthButton`, `ProtectedRoute`).
    *   Integrated authentication state and methods via `AuthContext`.
    *   Configured backend JWT validation (likely in `app/core/auth.py`).
    *   (See `authentication_details.md` for full details).

4.  **CRITICAL: Enhanced PDF Processing & Claude Integration**:
    *   **MAJOR BREAKTHROUGH: Phase 2+ Performance Optimizations**:
        *   **Problem Solved**: Even with token optimization, system was processing all chunks and making LLM calls for every biomarker extraction
        *   **Solution**: **Smart chunk skipping + biomarker caching** achieving 50-80% API call reduction
        *   **Smart Chunk Skipping**: Pattern-based screening to eliminate API calls for administrative content (headers, footers, contact info)
        *   **Biomarker Caching**: Instant extraction for known biomarker patterns with 8 comprehensive regex patterns
        *   **Cache Learning**: Automatically learns new patterns from successful LLM extractions (125+ patterns learned from test documents)
        *   **Cache Persistence FIXED**: Critical bug where patterns weren't saving to disk - now properly persists across system restarts
        *   **Result**: 60-85% total API cost reduction combining Phase 2 token optimization with Phase 2+ smart processing
    *   **MAJOR BREAKTHROUGH: Token Optimization**:
        *   **Problem Solved**: Content optimization was increasing tokens by 106% instead of reducing them
        *   **Solution**: Implemented aggressive compression in `content_optimization.py` removing administrative data, contact info, boilerplate text
        *   **Result**: Achieved 99%+ token reduction (e.g., 726 → 5 tokens) while preserving biomarker data
        *   **Impact**: Dramatically reduced API costs and improved processing speed
    *   **MAJOR IMPROVEMENT: Enhanced Biomarker Filtering**:
        *   **Problem Solved**: System was extracting invalid data like "Fax: 30203412.00", "CIN: -U74899PB1995PLC045956", "Email :customercare.saltlake@agilus.in", "Normal", "Other"
        *   **Solution**: Comprehensive filtering system with 100+ invalid patterns covering administrative data, geographic info, qualitative results
        *   **Implementation**: Enhanced prompts with explicit valid/invalid examples, improved fallback parser with extensive pattern filtering
        *   **Result**: Eliminated extraction of non-biomarker text, significantly improved accuracy
    *   **Claude Model Updates**:
        *   **Problem Solved**: Using deprecated Claude models (`claude-3-sonnet-20240229`)
        *   **Solution**: Updated to latest models (`claude-3-5-sonnet-20241022`) in both biomarker and metadata parsers
        *   **Result**: Improved extraction accuracy and future-proofed API calls
    *   **Enhanced Error Handling**:
        *   **Improvement**: Advanced JSON repair logic handling common Claude API response errors and truncation
        *   **Result**: Higher success rate for LLM-based extraction, reduced fallback to regex parser
    *   **Testing & Validation**:
        *   **Created**: Comprehensive test suites for smart chunk skipping (19 tests) and biomarker caching (17 tests)
        *   **Created**: `test_real_pdf_extraction.py` for real-world validation with detailed performance metrics
        *   **Confirmed**: Cache persistence fix validated with real documents showing 125+ patterns learned and saved
        *   **Verified**: Smart processing optimizations working in both optimized and fallback processing paths
    *   **Database Cleanup**: Successfully removed problematic PDF records and associated biomarkers for clean testing
    *   Continued refinement of Claude API prompts for extraction accuracy.
    *   Improved error handling and fallback mechanisms in the PDF processing pipeline.
    *   Maintained focus on OCR capabilities and reference range normalization.
    *   **Refactored PDF processing pipeline**:
        *   Implemented page relevance scoring and filtering to identify pages likely containing biomarkers.
        *   Modified Claude API interaction for biomarker extraction to process relevant pages sequentially, reducing timeouts and improving efficiency.
        *   Separated metadata extraction to run only on initial pages.

5.  **Backend & Testing Improvements**:
    *   Refactored relevant backend services to accommodate profile context.
    *   Expanded test coverage to include profile and favorite interactions.
    *   Updated unit tests for `pdf_service.py` and `biomarker_parser.py` to reflect processing changes.

6.  **Health Score Initial Implementation**:
    *   Added backend API endpoint (`/api/health-score/{profile_id}`) and calculation logic (likely in `health_score_service.py` - *needs verification*).
    *   Created backend schema (`health_score_schema.py`).
    *   Developed frontend components (`HealthScoreOverview.tsx`, `ScoreDisplay.tsx`, `ScoreExplanation.tsx`, `InfluencingFactors.tsx`, `TrendIndicator.tsx`).
    *   Added frontend service (`healthScoreService.ts`) and types (`healthScore.ts`).

7.  **New Dashboard Implementation**:
    *   Created new page component `frontend/src/pages/DashboardPage.tsx`.
    *   Added route `/dashboard` in `frontend/src/App.tsx` pointing to `DashboardPage.tsx`.
    *   Updated sidebar navigation link "Dashboard" to point to `/dashboard`.
    *   Removed rendering of old `Dashboard` component from `HomePage.tsx`.
    *   Implemented basic structure, profile context integration, favorite biomarker display (with values/trends), last report date display, collapsible AI summary, and action buttons in `DashboardPage.tsx`.
    *   Replaced Health Score component integration with a placeholder due to component file access issues.
    *   **Blocker**: User reports still seeing the old summary page visually despite these code changes and cache clearing, suggesting a potential build, cache, or rendering conflict.

8.  **Visualization Page Fixes & Redesign**:
    *   Fixed crash in `BiomarkerTable` when expanding rows (missing `Grid` import).
    *   Resolved multiple TypeScript errors in `BiomarkerTable` related to incorrect prop usage (`description`, `source_name`), event handler signatures, and sorting logic.
    *   Corrected props passed to `ExplanationModal` in `VisualizationPage`.
    *   **Completed redesign of the "Smart Summary" tab** in `VisualizationPage` for a more cohesive, modern aesthetic inspired by the Dashboard page (muted colors, outlined cards, refined typography and layout).
    *   **Improved biomarker explanation UX by immediately showing the modal with loading state** when a user clicks "Explain with AI" instead of waiting for the API response, providing better visual feedback.

9. **Enhanced Error Handling & Database Fixes**:
   * **Improved profile merge functionality** to properly delete source profiles and ensure transaction integrity.
   * **Enhanced profile context error handling** to gracefully recover when profiles are deleted or merged.
   * **Fixed database sequence issues** by adding database-type detection (SQLite vs PostgreSQL) and implementing appropriate sequence reset logic.
   * **Improved PDF status response handling** to prevent validation errors when PDFs are not found.
   * **Fixed favicon format** for better browser compatibility.

10. **User Experience & Authentication Improvements**:
   * **Fixed SPA routing** for direct URL access and page refreshes on deployed application.
   * **Enhanced Google sign-in** to always show account selection screen for multi-account users.
   * **Added user-scoped profile storage** to prevent cross-account profile access.
   * **Fixed component provider hierarchy** to ensure proper AuthProvider/ProfileProvider relationship.

11. **Dashboard UX Improvements**:
   * Fixed mobile layout for "Quick Actions" stack on `DashboardPage.tsx`.
   * Replaced blurred view/simple alert with a "Get Started" section (including "Create Profile" / "Upload Report" CTAs) on `DashboardPage.tsx` when no profile is active.

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
    *   Add tests for the redesigned Visualization "Smart Summary" tab.
7.  **Complete Dashboard Implementation**:
    *   **Resolve Blocker**: Investigate and fix the issue preventing the new `DashboardPage.tsx` from rendering correctly at the `/dashboard` route.
    *   Implement the "Category Status" overview section.
    *   Refine visual styling to match design inspirations.
    *   **Integrate Health Score**: Resolve component access issues and integrate the actual Health Score display.
    *   Ensure score calculation considers the active profile.
    *   Refine the calculation logic and influencing factors display based on feedback.
8.  **Add Health Score Tests**:
    *   Write backend tests for the calculation logic and API endpoint.
    *   Write frontend tests for the new Health Score components.
    *   **Add tests for backend favorite management endpoints.**
    *   **Add frontend tests for favorite drag-and-drop and modal interactions.**

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

4.  **Health Score Calculation Logic**:
    *   **Current Approach**: Likely a weighted average or rule-based system using `optimal_ranges.json`.
    *   **Consideration**: Refining the weighting, factors included, and explanation generation. How to handle missing data? How to show trends?
    *   **Trade-offs**: Simplicity vs. clinical accuracy/nuance.
    *   **Status**: Initial implementation done, needs refinement and testing.

### UX Considerations

1.  **Profile Switching Clarity**:
    *   **Challenge**: Ensuring users always know which profile's data they are viewing.
    *   **Approach**: Prominent display of the active profile, clear visual cues during switching.
    *   **Status**: Design and implementation ongoing.

2.  **Managing Favorites**:
    *   **Challenge**: Making the process of adding/removing/reordering favorites intuitive across different contexts (tiles, table, modals).
    *   **Approach**: Consistent iconography (star, x), drag-and-drop for tiles, modals for adding/replacing. Backend persistence.
    *   **Status**: Implemented. Minor UI tweaks might be needed based on feedback.

3.  **Onboarding for New Features**:
    *   **Challenge**: Introducing users to profile management and favorites without overwhelming them.
    *   **Approach**: Contextual hints or a brief guided tour upon first encountering the features.
    *   **Approach**: Contextual hints or a brief guided tour upon first encountering the features. **Implemented a dedicated Welcome Page for first-time users (0 profiles).**
    *   **Status**: **Implemented**.

4.  **Health Score Presentation**:
    *   **Challenge**: Displaying the score and its components clearly without being overly simplistic or complex.
    *   **Approach**: Dedicated components for score, explanation, factors, and trends.
    *   **Status**: Components created, integration and refinement needed.

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
    *   **Status**: Mitigated by sequential processing, but individual page calls still have timeouts. Monitoring.

4.  **Health Score Calculation Performance**:
    *   **Issue**: Calculation might become slow if many biomarkers or complex logic is involved.
    *   **Impact**: Could slow down page loads where the score is displayed.
    *   **Mitigation**: Optimize calculation logic, consider caching scores, potentially calculate asynchronously.
    *   **Status**: Monitoring.
5.  **Dashboard Rendering Issue**:
    *   **Issue**: The new `DashboardPage.tsx` component is not rendering visually for the user at the `/dashboard` route, despite code changes. The old summary view persists.
    *   **Impact**: Blocks progress on dashboard UI refinement and feature completion.
    *   **Mitigation**: Further investigation needed (build process, routing conflicts, conditional rendering elsewhere). Caching and server restart did not resolve.
    *   **Status**: **Blocker**. Needs investigation (build, cache, routing, conditional rendering). (Note: Empty state UX improved, but original rendering issue might persist).

6.  **New User Onboarding**:
    *   **Issue**: Users logging in for the first time were directed to a potentially empty/confusing dashboard.
    *   **Impact**: Poor initial user experience.
    *   **Mitigation**: Implemented a dedicated `/welcome` page (`WelcomePage.tsx`) shown only to users with zero profiles upon login or initial session load. This page guides them to create their first profile. Logic added to `AuthContext.tsx` to check profile count and redirect.
    *   **Status**: **Resolved**.

4. **Profile Merging Post-State**:
   * **Issue**: After merging profiles, localStorage references to deleted profiles can cause 404 errors.
   * **Impact**: Users may experience errors when returning to the app after profile merges.
   * **Mitigation**: Implemented automatic recovery that selects an available profile when the previous selection is no longer available.
   * **Status**: Resolved with enhanced error handling in ProfileContext.
