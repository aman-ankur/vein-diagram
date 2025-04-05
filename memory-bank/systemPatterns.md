# Vein Diagram: System Patterns

## System Architecture

Vein Diagram follows a modern client-server architecture with clear separation of concerns, now incorporating user profiles:

```mermaid
graph TD
    Client[Frontend Client on Vercel] <--> API[Backend API on Render]
    API <--> DB[(Supabase Postgres DB)]
    API <--> Claude[Claude AI API]
    Client --> SupabaseAuth[Supabase Auth]
    API --> SupabaseAuth

    subgraph Frontend
        direction LR
        UI[React UI Components] --> State[State Management (Profile Context)]
        UI --> Services[API Services (profile, healthScore, etc.)]
    end

    subgraph Backend on Render
        direction LR
        Routes[API Routes] --> Services[Business Logic Services]
        Services --> Models[Data Models]
        Services --> PDFProcessing[PDF Processing Engine]
        Services --> Config[Configuration]
        Models --> DB[(Supabase Postgres DB)]
        Services --> Claude[Claude AI API]
    end

    %% Authentication Note: Supabase Auth handles user management and JWT issuance.
    %% Frontend interacts directly for login/signup. Backend validates JWTs.
    %% See authentication_details.md for full flows.
```

### Frontend Architecture
- **React-based SPA**: Single-page application built with React and TypeScript.
- **Component-based structure**: Modular UI components for maintainability.
- **Client-side routing**: Navigation without full page reloads.
- **API service layer**: Centralized API communication (`profileService.ts`, etc.).
- **State Management**: Handling application state, including the **active user profile**.

### Backend Architecture
- **FastAPI framework**: Modern, high-performance Python web framework hosted on Render.
- **Service-oriented design**: Business logic encapsulated in service modules (e.g., `pdf_service.py`, `profile_service.py` - implicitly).
- **PDF processing pipeline**: Specialized components for extracting data from PDFs, now **linked to user profiles**.
- **Data persistence layer**: Uses **SQLAlchemy** ORM with **Supabase PostgreSQL** as the database. Models defined in `app/models/`. Migrations handled by **Alembic**.
- **Profile & Favorite Logic**: Specific services and routes handle profile CRUD and favorite biomarker management.

## Key Technical Decisions

### Frontend
1. **React + TypeScript**: Type safety and improved developer experience.
2. **Component Modularity**: Self-contained, reusable UI components.
3. **Responsive Design**: Mobile-friendly interface using modern CSS techniques.
4. **Data Visualization Libraries**: Specialized tools for rendering biomarker visualizations.
5. **State Management**: Using React Context API or similar for managing active profile state.

### Backend
1. **FastAPI**: High performance, easy API documentation, and modern Python features.
2. **PDF Processing Pipeline**: Specialized tools for extracting structured data from unstructured PDFs.
3. **SQLAlchemy ORM**: Type-safe database interactions with migration support.
4. **Claude API Integration**: AI-powered insights about biomarker relationships.
5. **Profile-Based Data**: Linking PDFs and favorites to user profiles.

### Cross-Cutting Concerns
1. **API-First Design**: Well-defined API contracts between frontend and backend.
2. **Type Safety**: Strong typing in both frontend (TypeScript) and backend (Pydantic).
3. **Testing Strategy**: Unit and integration tests for critical components, including profile/favorite logic.
4. **Development Workflow**: Local development environment with hot reloading.

## Design Patterns in Use

### Frontend Patterns
1. **Component Composition**: Building complex UIs from simple, reusable components (e.g., `BiomarkerTile.tsx`, `FavoriteBiomarkersGrid.tsx`).
2. **Container/Presentational Pattern**: Separating data fetching/logic (e.g., in pages like `ProfileManagement.tsx`) from presentation (e.g., reusable form components).
3. **Custom Hooks**: Encapsulating and reusing stateful logic (e.g., potentially `useProfile`, `useFavorites`).
4. **Context API (Potentially)**: For managing global state like the active user profile.
5. **Utility Functions**: Grouping reusable logic (`favoritesUtils.ts`, `biomarkerUtils.ts`).

### Backend Patterns
1. **Repository Pattern**: Abstracting data access logic.
2. **Service Layer**: Encapsulating business logic.
3. **Dependency Injection**: FastAPI's built-in DI for providing dependencies.
4. **Factory Pattern**: Creating complex objects with specific configurations.
5. **Pipeline Processing**: Sequential processing of PDF data extraction.

## Component Relationships

### Frontend Component Hierarchy (Simplified Example)
```mermaid
graph TD
    App --> Layout
    Layout --> Header(Header - incl. Profile Selector?)
    Layout --> Footer
    Layout --> MainContent

    subgraph MainContent
        direction LR
        UploadPage[Upload Page (Select Profile)]
        VisualizationPage[Visualization Page (Profile Context)]
        HistoryPage[Biomarker History Page (Profile Context)]
        ProfileMgmtPage[Profile Management Page]
    end

    MainContent --> DashboardPage[Dashboard Page (Profile Context)]

    ProfileMgmtPage --> ProfileList
    ProfileMgmtPage --> ProfileForm

    VisualizationPage --> FavoriteBiomarkersGrid
    VisualizationPage --> BiomarkerVisualization(Biomarker Visualization)
    VisualizationPage --> BiomarkerTable(Biomarker Table - Add/Remove Fav)
    VisualizationPage --> SmartSummaryTab[Smart Summary Tab (Redesigned)]

    DashboardPage --> FavoriteBiomarkersGrid
    DashboardPage --> HealthScoreOverview(Health Score Overview)
    DashboardPage --> AI_Summary[AI Summary]
    DashboardPage --> CategoryStatus[Category Status]

    FavoriteBiomarkersGrid --> BiomarkerTile(Biomarker Tile - Add/Remove Fav)
    FavoriteBiomarkersGrid --> AddBiomarkerTile --> AddFavoriteModal

    UploadPage --> PDFUploader
```

### Backend Component Relationships (Simplified Example)
```mermaid
graph TD
    subgraph API_Routes
        direction LR
        PDFRoutes[pdf_routes.py]
        BiomarkerRoutes[biomarker_routes.py]
    ProfileRoutes[profile_routes.py (incl. /favorites endpoints)]
    HealthScoreRoutes[health_score_routes.py]
    end

    subgraph Services
        direction LR
        PDFService[pdf_service.py]
        BiomarkerService[biomarker_service.py (implicit)]
        ProfileService[profile_service.py (implicit)]
        HealthScoreService[health_score_service.py]
        LLMService[llm_service.py]
        MetadataParser[metadata_parser.py]
        BiomarkerParser[biomarker_parser.py]
    end

    subgraph Parsers
        direction LR
        BiomarkerParser[biomarker_parser.py]
        MetadataParser[metadata_parser.py]
    end

    subgraph Models
        direction LR
        PDFModel[pdf_model.py]
        BiomarkerModel[biomarker_model.py]
        ProfileModel[profile_model.py (with favorite_biomarkers)]
    end

    API_Routes --> Services
    Services --> LLMService
    Services --> Models
    Models --> Database[(Database)]

    PDFRoutes --> PDFService
    BiomarkerRoutes --> BiomarkerService
    ProfileRoutes --> ProfileService
    HealthScoreRoutes --> HealthScoreService

    PDFService --> MetadataParser
    PDFService --> BiomarkerParser
    PDFService --> ProfileService # To link PDF to profile
    BiomarkerService --> LLMService # For insights
    ProfileService --> Models # Profile CRUD & Favorite management
    HealthScoreService --> Models # Needs biomarker data
    HealthScoreService --> Config # Needs optimal_ranges.json
```

## Data Flow

### PDF Processing Flow (Refactored - with Profile, Filtering, Sequential Processing)
```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant BackendAPI
    participant PDFService
    participant MetadataParser
    participant BiomarkerParser
    participant Database

    User->>Frontend: Select Profile
    User->>Frontend: Upload PDF
    Frontend->>BackendAPI: POST /api/pdfs/upload (with profile_id)
    BackendAPI->>PDFService: process_pdf_background(pdf_id, db_session)
    PDFService->>Database: Get PDF record
    PDFService->>PDFService: extract_text_from_pdf(file_path) [All Pages]
    PDFService->>Database: Save full extracted text (temp)
    PDFService->>MetadataParser: extract_metadata_with_claude(first_few_pages_text)
    MetadataParser->>Database: Update PDF metadata (patient info, date, etc.)
    PDFService->>PDFService: filter_relevant_pages(all_pages_text_dict)
    alt Relevant pages found
        PDFService->>PDFService: process_pages_sequentially(relevant_pages)
        loop For each relevant page
            PDFService->>BiomarkerParser: extract_biomarkers_with_claude(page_text)
            BiomarkerParser-->>PDFService: page_biomarkers
        end
        PDFService->>PDFService: De-duplicate biomarkers
        PDFService->>Database: Store final biomarkers (linked to pdf_id, profile_id)
        PDFService->>Database: Update PDF parsing_confidence
    else No relevant pages
        PDFService->>PDFService: Log warning, skip biomarker saving
    end
    PDFService->>Database: Update PDF status to 'processed' or 'error'
    %% Note: Frontend polls /api/pdfs/status/{file_id} separately
```

### Visualization Data Flow (with Profile)
```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant BackendAPI
    participant Database
    participant LLMService

    User->>Frontend: Select Profile
    User->>Frontend: Navigate to Visualization Page
    Frontend->>BackendAPI: GET /api/profiles/{profile_id}/biomarkers
    BackendAPI->>Database: Query biomarker data for profile_id
    Database->>BackendAPI: Return data
    BackendAPI->>Frontend: Biomarker data (filtered by profile)
    Frontend->>Frontend: Render visualization
    Frontend->>BackendAPI: GET /api/profiles/{profile_id}/favorites
    BackendAPI->>Database: Query favorite biomarkers for profile_id
    Database->>BackendAPI: Return favorites list
    BackendAPI->>Frontend: Favorite biomarkers data
    Frontend->>Frontend: Highlight/display favorites
    Frontend->>BackendAPI: GET /api/biomarkers/{biomarker_name}/insights
    BackendAPI->>LLMService: Request biomarker insights
    LLMService->>BackendAPI: Return insights
    BackendAPI->>Frontend: Biomarker insights
    Frontend->>User: Display visualization with insights & favorites
