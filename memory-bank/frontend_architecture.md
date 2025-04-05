# Vein Diagram: Frontend Architecture

This document outlines the structure and key patterns of the Vein Diagram React frontend application.

## Overview

The frontend is a Single Page Application (SPA) built using **React** and **TypeScript**, bootstrapped with **Vite**. It communicates with the backend via a RESTful API to upload PDFs, manage profiles, fetch biomarker data, and display visualizations. Styling is primarily handled using **Tailwind CSS**.

## Core Technologies

-   **Framework/Library**: React 18+
-   **Language**: TypeScript
-   **Build Tool**: Vite
-   **Styling**: Tailwind CSS, Material UI (including Styled Components)
-   **UI Components**: Material UI
-   **Drag & Drop**: dnd-kit
-   **API Communication**: Axios (via `services/api.ts`)
-   **Testing**: Jest & React Testing Library
-   **Visualization**: D3.js (primarily), potentially others like Recharts/Chart.js for simpler charts.

## Directory Structure (`frontend/src`)

-   **`main.tsx`**: Entry point of the application, renders the root `App` component.
-   **`App.tsx`**: Root component, likely sets up routing and global layout/context providers.
-   **`components/`**: Contains reusable UI components used across different pages.
    -   Examples: `Header.tsx`, `Footer.tsx`, `Layout.tsx`, `PDFUploader.tsx`, `BiomarkerTable.tsx`, `BiomarkerVisualization.tsx`, `FavoriteBiomarkersGrid.tsx`, `ProfileSelector.tsx`, `LoadingIndicator.tsx`, `ErrorHandler.tsx`, `HealthScoreOverview.tsx`, `ScoreDisplay.tsx`, `ScoreExplanation.tsx`, `InfluencingFactors.tsx`, `TrendIndicator.tsx`, `AddBiomarkerTile.tsx`, `AddFavoriteModal.tsx`, `ReplaceFavoriteModal.tsx`.
-   **`pages/`**: Contains top-level components representing distinct application views/routes.
    -   Examples: `HomePage.tsx`, `UploadPage.tsx`, `VisualizationPage.tsx`, `BiomarkerHistoryPage.tsx`, `ProfileManagement.tsx`, `DashboardPage.tsx`.
        - `VisualizationPage.tsx`: Displays detailed biomarker data (table, charts), favorite biomarkers, and the AI-generated health summary. Includes logic for profile selection, tabbed views, biomarker explanation modals, favorite management (add/remove/reorder), and health summary generation/display.
            - **Health Summary Parsing**: Contains specific logic to parse the `health_summary` string received from the backend. It looks for section-defining emojis (💡, 📈, 👀) at the beginning of lines, ignores any potential text headers immediately following the emoji, and extracts bullet points (lines starting with •) for each section, rendering them in the correct UI structure.
        - `AccountPage.tsx`: User profile and account settings page. Uses a custom Material UI implementation with styled components:
            - **Styled Components**: Uses Material UI's `styled` API to create custom components (e.g., `StyledCard`, `GradientTypography`, `ProfileAvatar`)
            - **Layout**: Responsive design with elegant card-based sections and proper spacing
            - **UI Features**: User avatar with email initials, color gradients, hover effects, and smooth animations
            - **Organization**: Distinct sections for user information and security/privacy management
-   **`services/`**: Handles communication with the backend API.
    -   `api.ts`: Base Axios instance configuration (sets base URL, potentially headers).
    *   `pdfService.ts`: Functions for uploading PDFs, checking status.
    *   `profileService.ts`: Functions for CRUD operations on profiles, matching, association, favorites management.
    *   `healthScoreService.ts`: Functions for fetching the calculated health score.
    *   `biomarkerService.ts` (or similar): Likely handles biomarker fetching, deletion, and explanation requests (may be partially integrated into `profileService` or `VisualizationPage`).
-   **`contexts/`**: Provides global state management using React Context API.
    -   `AuthContext.tsx`: Manages authentication state (user, loading), provides auth methods (`signUp`, `signIn`, `signOut`, etc.). See `authentication_details.md`.
    -   `ProfileContext.tsx`: Manages the currently active user profile and provides it to consuming components.
-   **`hooks/`**: *(Currently empty)* Intended for custom reusable hooks encapsulating stateful logic (e.g., `useProfile`, `useFavorites`).
-   **`utils/`**: Contains utility functions used across the application.
    -   `biomarkerUtils.ts`: Helper functions related to biomarker data manipulation or display.
    *   `favoritesUtils.ts`: Helper functions for managing favorite biomarkers logic (mostly deprecated after backend migration).
-   **`types/`**: TypeScript type definitions and interfaces (e.g., for API responses, data models like `Profile`, `Biomarker`, `PDF`, `HealthScore`).
-   **`assets/`**: Static assets like images, fonts, or JSON data (`facts.json`).
-   **`styles/`**: Global styles or base Tailwind configuration.
-   **`config.ts`**: Application configuration, likely includes the backend API base URL.

## Key Architectural Patterns

-   **Component-Based Architecture**: UI is built by composing smaller, reusable components.
-   **Container/Presentational Pattern (Implicit)**: Page components (`pages/`) often act as containers, fetching data via services and managing state, while components in `components/` focus on rendering UI based on props.
-   **Service Layer**: API interactions are encapsulated within service files (`services/`), promoting separation of concerns. Components call service functions rather than making direct API calls.
-   **Context API for Global State**: `ProfileContext` is used to manage and provide the active profile state throughout the component tree, avoiding prop drilling for this essential global concern.
-   **Utility Functions**: Common, reusable logic (e.g., formatting, calculations specific to biomarkers) is extracted into utility files (`utils/`). Favorite-specific utils are less relevant now.
-   **Styled Components Pattern**: Used notably in `AccountPage.tsx` to create reusable, themeable UI components leveraging Material UI's `styled` API.

## Data Flow (Typical Page)

1.  **Routing**: A routing library (likely `react-router-dom`, configured in `App.tsx` or similar) maps URL paths to specific Page components (`pages/`).
2.  **Context**: The Page component (and its children) can access global state, like the active profile, via `useContext(ProfileContext)`.
3.  **Data Fetching**: The Page component (or child components) uses functions from the `services/` directory to make API calls (e.g., `profileService.getProfileBiomarkers(activeProfileId)`). These service functions use the configured Axios instance (`api.ts`).
4.  **State Management**: Fetched data, loading states, and error states are managed within the Page component using React hooks (`useState`, `useEffect`).
5.  **Rendering**: Data is passed down as props to presentational components (`components/`) which render the UI.
6.  **User Interaction**: User actions (e.g., button clicks, form submissions) trigger event handlers in components, which might update local state, call service functions to interact with the API, or update global context (e.g., changing the active profile).

## State Management Approach

-   **Local Component State**: `useState` and `useReducer` are used for state confined to individual components or closely related ones.
-   **Global State**: React's Context API is used for broader state concerns:
    -   `AuthContext.tsx`: Manages authentication status, user object, and provides auth methods.
    -   `ProfileContext.tsx`: Manages the currently selected user profile.
-   **Server Cache/Data Fetching State**: While not explicitly listed, libraries like React Query or SWR *could* be used to manage the state related to data fetching (caching, loading/error states, re-fetching), but currently, it seems likely handled manually within components using `useState`/`useEffect` and service calls.

## Styling

-   **Primary Framework**: **Tailwind CSS** is used for utility-first styling, applied directly via class names in JSX.
-   **Component Library & Theming**: **Material UI** is used for pre-built components (like Cards, Lists, Avatars, especially in `AccountPage.tsx`) and provides a theming layer (`useTheme`).
-   **Custom Styling**: Material UI's **Styled Components API** (`styled`) is used in specific areas (`AccountPage.tsx`) to create highly customized, reusable, theme-aware components.
-   **Responsive Design**: Achieved using both Tailwind's responsive prefixes (e.g., `md:flex`) and Material UI's `sx` prop with breakpoint objects (e.g., `sx={{ flexDirection: { xs: 'column', md: 'row' } }}`).
-   **Global Styles**: A base stylesheet (`styles/`) might define global resets or base Tailwind configurations.

### Styling Integration Considerations

-   **Tailwind vs. Material UI**: Using both requires careful management. Material UI's component styles (via `sx` prop or `styled`) often take precedence over Tailwind utility classes applied to the same element.
-   **Consistency**: When creating new components, adopt the dominant styling approach of the surrounding context (Tailwind or Material UI/Styled Components) to maintain consistency. The `AccountPage.tsx` serves as an example of a Material UI-centric approach.

## Testing

-   **Unit/Component Tests**: Jest and React Testing Library are used (`*.test.tsx` files). Tests likely focus on rendering components correctly based on props and simulating user interactions.
-   **Mocking**: API calls made by services are likely mocked during testing.
