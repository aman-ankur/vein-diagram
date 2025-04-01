# Vein Diagram: Frontend Architecture

This document outlines the structure and key patterns of the Vein Diagram React frontend application.

## Overview

The frontend is a Single Page Application (SPA) built using **React** and **TypeScript**, bootstrapped with **Vite**. It communicates with the backend via a RESTful API to upload PDFs, manage profiles, fetch biomarker data, and display visualizations. Styling is primarily handled using **Tailwind CSS**.

## Core Technologies

-   **Framework/Library**: React 18+
-   **Language**: TypeScript
-   **Build Tool**: Vite
-   **Styling**: Tailwind CSS
-   **API Communication**: Axios (via `services/api.ts`)
-   **Testing**: Jest & React Testing Library
-   **Visualization**: D3.js (primarily), potentially others like Recharts/Chart.js for simpler charts.

## Directory Structure (`frontend/src`)

-   **`main.tsx`**: Entry point of the application, renders the root `App` component.
-   **`App.tsx`**: Root component, likely sets up routing and global layout/context providers.
-   **`components/`**: Contains reusable UI components used across different pages.
    -   Examples: `Header.tsx`, `Footer.tsx`, `Layout.tsx`, `PDFUploader.tsx`, `BiomarkerTable.tsx`, `BiomarkerVisualization.tsx`, `FavoriteBiomarkersGrid.tsx`, `ProfileSelector.tsx`, `LoadingIndicator.tsx`, `ErrorHandler.tsx`, **`HealthScoreOverview.tsx`**, **`ScoreDisplay.tsx`**, **`ScoreExplanation.tsx`**, **`InfluencingFactors.tsx`**, **`TrendIndicator.tsx`**.
-   **`pages/`**: Contains top-level components representing distinct application views/routes.
    -   Examples: `HomePage.tsx`, `UploadPage.tsx`, `VisualizationPage.tsx`, `BiomarkerHistoryPage.tsx`, `ProfileManagement.tsx`. *(Note: Health Score might be displayed within these pages, e.g., VisualizationPage)*.
-   **`services/`**: Handles communication with the backend API.
    -   `api.ts`: Base Axios instance configuration (sets base URL, potentially headers).
    *   `pdfService.ts`: Functions for uploading PDFs, checking status.
    *   `profileService.ts`: Functions for CRUD operations on profiles, matching, association.
    *   **`healthScoreService.ts`**: Functions for fetching the calculated health score.
    *   *(Note: Biomarker fetching/explanation service might be missing or integrated elsewhere)*.
-   **`contexts/`**: Provides global state management using React Context API.
    -   `ProfileContext.tsx`: Manages the currently active user profile and provides it to consuming components.
-   **`hooks/`**: *(Currently empty)* Intended for custom reusable hooks encapsulating stateful logic.
-   **`utils/`**: Contains utility functions used across the application.
    -   `biomarkerUtils.ts`: Helper functions related to biomarker data manipulation or display.
    *   `favoritesUtils.ts`: Helper functions for managing favorite biomarkers logic.
-   **`types/`**: TypeScript type definitions and interfaces (e.g., for API responses, data models like `Profile`, `Biomarker`, `PDF`, **`HealthScore`**).
-   **`assets/`**: Static assets like images, fonts, or JSON data (`facts.json`).
-   **`styles/`**: Global styles or base Tailwind configuration.
-   **`config.ts`**: Application configuration, likely includes the backend API base URL.

## Key Architectural Patterns

-   **Component-Based Architecture**: UI is built by composing smaller, reusable components.
-   **Container/Presentational Pattern (Implicit)**: Page components (`pages/`) often act as containers, fetching data via services and managing state, while components in `components/` focus on rendering UI based on props.
-   **Service Layer**: API interactions are encapsulated within service files (`services/`), promoting separation of concerns. Components call service functions rather than making direct API calls.
-   **Context API for Global State**: `ProfileContext` is used to manage and provide the active profile state throughout the component tree, avoiding prop drilling for this global concern.
-   **Utility Functions**: Common, reusable logic (e.g., formatting, calculations specific to biomarkers or favorites) is extracted into utility files (`utils/`).

## Data Flow (Typical Page)

1.  **Routing**: A routing library (likely `react-router-dom`, configured in `App.tsx` or similar) maps URL paths to specific Page components (`pages/`).
2.  **Context**: The Page component (and its children) can access global state, like the active profile, via `useContext(ProfileContext)`.
3.  **Data Fetching**: The Page component (or child components) uses functions from the `services/` directory to make API calls (e.g., `profileService.getProfileBiomarkers(activeProfileId)`). These service functions use the configured Axios instance (`api.ts`).
4.  **State Management**: Fetched data, loading states, and error states are managed within the Page component using React hooks (`useState`, `useEffect`).
5.  **Rendering**: Data is passed down as props to presentational components (`components/`) which render the UI.
6.  **User Interaction**: User actions (e.g., button clicks, form submissions) trigger event handlers in components, which might update local state, call service functions to interact with the API, or update global context (e.g., changing the active profile).

## State Management Approach

-   **Local Component State**: `useState` and `useReducer` are used for state confined to individual components or closely related ones.
-   **Global State (Profile)**: React's Context API (`ProfileContext.tsx`) is used to manage and distribute the currently selected user profile across the application. This avoids prop drilling for this essential piece of global state.
-   **Server Cache/Data Fetching State**: While not explicitly listed, libraries like React Query or SWR *could* be used to manage the state related to data fetching (caching, loading/error states, re-fetching), but currently, it seems likely handled manually within components using `useState`/`useEffect` and service calls.

## Styling

-   **Tailwind CSS**: Utility-first CSS framework is the primary method for styling. Class names are applied directly in the JSX.
-   **Global Styles**: A base stylesheet (`styles/`) might define global resets, base styles, or custom Tailwind configurations.

## Testing

-   **Unit/Component Tests**: Jest and React Testing Library are used (`*.test.tsx` files). Tests likely focus on rendering components correctly based on props and simulating user interactions.
-   **Mocking**: API calls made by services are likely mocked during testing.
