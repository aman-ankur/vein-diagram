# Vein Diagram: Testing Strategy

This document outlines the testing approach for the Vein Diagram application, covering both frontend and backend components.

## Philosophy

The goal is to maintain a high level of confidence in the application's correctness, reliability, and performance through a multi-layered testing strategy. We aim for a balance between fast unit tests and more comprehensive integration/end-to-end tests.

## Testing Levels & Tools

### 1. Backend Testing (`backend/`)

-   **Tool**: `pytest`
-   **Runner**: `backend/run_tests.sh` script executes tests category by category.
-   **Coverage**: `pytest-cov` generates HTML coverage reports (output to `htmlcov/`).
-   **Environment**: Tests run with `PYTHONPATH=.` and a dummy `ANTHROPIC_API_KEY`.
-   **Categories**:
    -   **Unit Tests (`tests/services/`)**: Focus on testing individual functions and classes within the service layer (e.g., `biomarker_parser.py`, `pdf_service.py`, `health_score_service.py`, `startup_recovery_service.py`) in isolation. Dependencies like database sessions or external APIs (Claude) are typically mocked.
    -   **API Tests (`tests/api/`)**: Test the FastAPI application's API endpoints. Uses `pytest` fixtures (likely from `conftest.py`) and FastAPI's `TestClient` to send HTTP requests to the API and assert responses without running a live server. Database interactions might be mocked or use a test database. Includes tests for profiles, favorites, biomarkers (incl. deletion), PDFs, and Health Score endpoints.
    -   **Integration Tests (`tests/integration/`)**: Test the interaction between different components of the backend, such as the flow from API endpoint through services to the database. May involve a test database setup. Tests focus on data flow and component collaboration (e.g., `test_pdf_biomarkers_flow.py`).
    -   **End-to-End Tests (`tests/end_to_end/`)**: Simulate complete user scenarios from the backend perspective, potentially involving multiple API calls and verifying the overall outcome and data state. These might be slower and require more setup (e.g., test database seeding). *(Note: The presence of this directory suggests intent, but specific implementation details aren't fully known without examining the tests themselves).*

### 2. Frontend Testing (`frontend/`)

-   **Tools**: `Jest` (Test Runner), `React Testing Library` (Component Testing Utilities)
-   **Runner**: `npm test` (Standard command defined in `package.json`).
-   **Coverage**: Jest includes built-in coverage reporting capabilities (configuration likely in `jest.config.js` or `package.json`).
-   **Types**:
    -   **Unit Tests**: Testing individual utility functions (`utils/`) or simple, non-rendering logic.
    -   **Component Tests (`*.test.tsx`)**: Focus on testing React components in isolation. Uses React Testing Library to render components, simulate user interactions (clicks, typing, drag-and-drop using libraries compatible with `dnd-kit` testing), and assert the rendered output or component state changes. API calls made via services (`services/`) are typically mocked using Jest's mocking features (`jest.mock`). Tests exist for presentational components (`components/` - incl. Health Score, Favorites, Modals), page-level components (`pages/` - incl. Dashboard, Vis page with redesigned summary), and interactions like favorite management and biomarker deletion.

### 3. Manual Testing

-   Performed periodically during development and before releases to catch issues not covered by automated tests, assess usability, and verify visual consistency across browsers.
-   Focus areas include the PDF upload and processing flow, visualization interactions, profile management, and favorite biomarker functionality.

## Key Areas & Focus

-   **PDF Processing**: Critical area requiring thorough testing due to complexity and variability. Includes testing text extraction (all pages), OCR fallback, metadata extraction (initial pages), page relevance filtering, sequential biomarker extraction (mocked Claude calls per page), fallback parser logic, de-duplication, and data standardization. Sample PDFs (`backend/sample_reports/`) are used.
-   **System Recovery**: Testing the startup recovery service and smart status endpoint functionality. Includes 15 comprehensive unit tests covering detection of inconsistent PDFs, fixing stuck PDFs, confidence calculation, error handling, and health monitoring. Integration tests verify real-world scenarios with actual database interactions.
-   **API Endpoints**: Ensuring API contracts are met, request validation works, correct responses/status codes are returned, and background tasks are initiated correctly (e.g., PDF processing).
-   **Profile Management**: Testing CRUD operations, profile matching logic, and correct association of PDFs/biomarkers with profiles.
-   **Favorite Management**: Testing backend API endpoints for adding, removing, and reordering favorites. Testing frontend logic for toggling, replacing (when full), deleting, and drag-and-drop reordering (`dnd-kit` interactions).
-   **Biomarker Deletion**: Testing backend API endpoint and frontend confirmation/deletion flow.
-   **Health Score Calculation**: Testing the backend logic for score calculation, including handling of optimal ranges, different biomarker values, and edge cases (e.g., missing data).
-   **Health Score API**: Testing the `/api/health-score/{profile_id}` endpoint for correctness and performance.
-   **Health Score Frontend Components**: Testing the rendering and display logic of `HealthScoreOverview.tsx` and related components.
-   **Dashboard Page**: Testing data fetching, component integration (Favorites, Health Score placeholder, AI Summary, etc.), and rendering logic (once blocker resolved).
-   **Visualization Page Redesign**: Testing the rendering and interaction of the redesigned "Smart Summary" tab components.
-   **Data Integrity**: Verifying correct data storage, retrieval, and relationships in the database (primarily via integration tests).
-   **Component Rendering & Interaction**: Ensuring UI components render correctly based on props/state and respond appropriately to user interactions.
-   **State Management (Frontend)**: Verifying that global state (like `ProfileContext`) is updated and consumed correctly.

## Running Tests

-   **Backend**: Execute `PYTHONPATH=backend pytest backend/tests/...` from the project root (or specific test file/directory). Setting `PYTHONPATH` is required. Alternatively, use `bash backend/run_tests.sh` if it handles the path correctly.
-   **Frontend**: Execute `npm test` within the `frontend/` directory.

## Future Considerations

-   **E2E Testing Framework**: Consider implementing a browser automation framework (e.g., Cypress, Playwright) for true end-to-end testing that simulates user flows through the actual UI in a browser.
-   **Performance Testing**: Implement specific performance tests for critical paths like PDF processing and large dataset visualization rendering.
-   **CI/CD Integration**: Integrate automated tests into a Continuous Integration pipeline to run on every commit/pull request.
