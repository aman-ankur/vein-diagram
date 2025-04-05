# Vein Diagram: Technical Context

## Technologies Used

### Frontend Stack
- **React**: JavaScript library for building user interfaces
- **TypeScript**: Typed superset of JavaScript for improved developer experience
- **Vite**: Modern frontend build tool and development server
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Material UI**: React component library implementing Google's Material Design (used alongside Tailwind CSS)
- **Jest**: JavaScript testing framework for unit and component testing
- **React Testing Library**: Testing utilities for React components
- **Axios**: Promise-based HTTP client for API communication
- **dnd-kit**: Library for drag-and-drop interactions (used for favorite reordering)

### Backend Stack
- **Python**: Core programming language for the backend
- **FastAPI**: Modern, high-performance web framework for building APIs
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM) library for database interaction
- **Pydantic**: Data validation and settings management using Python type annotations
- **Pytest**: Testing framework for Python code
- **PDF Processing Libraries**:
- **PyMuPDF (fitz)**: Core library for PDF parsing and text extraction (`pymupdf` in requirements).
- **pdfplumber**: Used for detailed PDF content extraction, especially tables.
- **pytesseract**: OCR capabilities via the Tesseract engine for image-based text.
- **pdf2image**: Converts PDF pages to images for OCR.
- **HTTPX**: Asynchronous HTTP client for communicating with external APIs (like Claude).
- **Alembic**: Database migration tool for SQLAlchemy.

### Data Visualization
- **D3.js**: Primary library for custom, dynamic, interactive data visualizations.
- **Recharts/Chart.js**: Potentially used for simpler, standard chart types if needed.

### External APIs
- **Claude API**: Anthropic's AI model for generating biomarker insights and explanations.
- **Supabase Auth**: Backend-as-a-Service for handling user authentication (email/password, social logins like Google). See `authentication_details.md`.

### Development Tools
- **Git**: Version control system
- **npm**: Package management for frontend dependencies
- **pip/venv**: Package management and virtual environments for Python dependencies
- **ESLint/Prettier**: Code linting and formatting for JavaScript/TypeScript
- **Black/isort**: Code formatting for Python

## Development Setup

### Local Development Environment
```
vein-diagram/
├── frontend/           # React frontend application
│   ├── src/
│   │   ├── components/ # UI Components (incl. Profile/Favorite/HealthScore/Dashboard related: FavoriteBiomarkersGrid, HealthScoreOverview, ScoreDisplay, etc.)
│   │   ├── pages/      # Page Components (ProfileManagement, VisualizationPage, BiomarkerHistoryPage, DashboardPage)
│   │   ├── services/   # API Services (profileService.ts, healthScoreService.ts, etc.)
│   │   ├── utils/      # Utility functions (favoritesUtils.ts - deprecated, biomarkerUtils.ts)
│   │   ├── contexts/   # React Contexts (e.g., for Profile state)
│   │   └── types/      # TypeScript types (Profile, Favorite, Biomarker, HealthScore, etc.)
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/            # FastAPI backend application
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/ # API Routes (biomarker_routes.py, profile_routes.py, pdf_routes.py, health_score_routes.py)
│   │   ├── models/     # DB Models (biomarker_model.py, profile_model.py, pdf_model.py)
│   │   ├── schemas/    # Pydantic Schemas (biomarker_schema.py, profile_schema.py, pdf_schema.py, health_score_schema.py)
│   │   ├── services/   # Business Logic (pdf_service.py, llm_service.py, biomarker_parser.py, metadata_parser.py, profile_matcher.py, health_score_service.py - implicit, profile_service.py - implicit)
│   │   └── config/     # Configuration files (optimal_ranges.json)
│   ├── tests/          # Test suite (incl. tests for profiles/favorites/health_score)
│   │   ├── api/        # API route tests (test_profile_routes.py, test_biomarker_routes.py, test_health_score_routes.py - potential)
│   │   └── services/   # Service layer tests (test_health_score_service.py - potential, test_pdf_service.py, test_biomarker_parser.py)
│   ├── alembic/        # Alembic migration scripts
│   ├── alembic.ini     # Alembic configuration
│   └── requirements.txt # Python dependencies
│
├── memory-bank/        # Project documentation & context
└── project-docs/       # Additional project documents
```

### Development Workflow
1. **Backend Development**:
   - Python virtual environment (`vein-d/`) setup with dependencies from `requirements.txt`.
   - FastAPI server (`uvicorn`) with hot-reloading for development.
   - Database migrations using Alembic needed for schema changes (e.g., adding profile tables, favorite column).
   - Automated tests (`pytest`) for API endpoints and services, including profile/favorite/health score logic.

2. **Frontend Development**:
   - Vite development server (`npm run dev`) with hot module replacement.
   - Component-driven development approach.
   - TypeScript for type checking during development.
   - Jest (`npm test`) for running unit and component tests, including profile/favorite/health score/dashboard components.

3. **Integration**:
   - Frontend configured (`src/config.ts`) to communicate with backend API (default: `http://localhost:8000`).
   - Vite proxy setup likely used during local development to avoid CORS issues.
   - Shared type definitions or careful interface matching between frontend (TypeScript) and backend (Pydantic).

## Technical Constraints

### PDF Processing Challenges
- **Diverse Lab Formats**: Ongoing challenge requiring robust parsing and potential lab-specific adapters or refined LLM prompts.
- **OCR Limitations**: Accuracy depends on image quality in PDFs.
- **Structure Extraction**: Complex tables or layouts can be difficult to parse reliably.
- **Reference Range Parsing**: Variations require flexible parsing logic.
- **Filtering Accuracy**: Heuristic page filtering might miss relevant pages or include irrelevant ones.

### Performance Considerations
- **PDF Processing Time**: Can be significant for large/complex PDFs, mitigated by background processing and sequential calls.
- **Visualization Rendering**: Large datasets require optimization (sampling, virtualization, efficient D3 usage).
- **API Response Times**: Database query optimization, caching (backend/frontend) are important, especially with profile filtering.
- **LLM API Latency**: Calls to Claude API add latency. Sequential processing adds per-page latency but avoids large timeouts. Caching insights is crucial.

### Security and Privacy
- **Health Data Sensitivity**: All data handling must prioritize privacy (HIPAA considerations if applicable in target market). Data stored should be minimized and secured.
- **PDF Content Security**: Uploaded files could contain risks; sanitization or isolated processing might be needed in production.
- **API Security**: Authentication/Authorization is implemented using Supabase JWTs validated by the backend (`app/core/auth.py`). See `authentication_details.md`.

### Browser Compatibility
- **Modern Browser Focus**: Targeting evergreen browsers (Chrome, Firefox, Safari, Edge).
- **Mobile Responsiveness**: Ensuring usability on various screen sizes is key.
- **SVG/Canvas Support**: Essential for D3.js visualizations.

## Dependencies

### Critical Frontend Dependencies (Illustrative - check `package.json`)
```json
{
  "dependencies": {
    "react": "^18.x",
    "react-dom": "^18.x",
    "typescript": "^5.x",
    "axios": "^1.x",
    "tailwindcss": "^3.x",
    "d3": "^7.x"
    // Potentially state management (zustand, redux toolkit)
    // Potentially routing (react-router-dom)
    // Potentially charting libraries (recharts)
  },
  "devDependencies": {
    "vite": "^4.x || ^5.x",
    "jest": "^29.x",
    "@testing-library/react": "^14.x",
    "eslint": "^8.x",
    "prettier": "^2.x || ^3.x"
  }
}
```

### Critical Backend Dependencies (Illustrative - check `requirements.txt`)
```
fastapi==0.9x.x || 0.1xx.x
uvicorn==0.2x.x
sqlalchemy==2.x.x
pydantic==1.10.x || 2.x.x
pymupdf==1.2x.x # PyMuPDF (fitz)
pdfplumber==0.x.x
pytesseract==0.3.x
pytest==7.x.x
httpx==0.2x.x
python-multipart==0.0.x
# Potentially database driver (psycopg2-binary, asyncpg)
# Potentially alembic for migrations
```

## Integration Points

### Frontend-Backend Integration
- RESTful API endpoints defined in FastAPI (`/api/...`).
- JSON data format for request/response payloads.
- Type-safe contracts using TypeScript interfaces (frontend) and Pydantic models (backend).
- Key endpoints for Profiles (`/api/profiles/...`), Favorites (`/api/profiles/{profile_id}/favorites/...`), Biomarkers (`/api/biomarkers?profile_id=...`, `/api/biomarkers/{id}`), PDFs (`/api/pdfs/...`), Health Score (`/api/health-score/{profile_id}`).

### External API Integration
- **Claude API**: Via `llm_service.py` (for insights) and `biomarker_parser.py`/`metadata_parser.py` (for extraction) using `anthropic` SDK or `httpx`. Requires API key management.

### File System Integration
- Temporary storage (`backend/uploads/`?) for PDFs during processing.
- Log files (`backend/logs/`).

## Deployment Considerations

### Hosting Requirements
- Frontend: Static site hosting (Netlify, Vercel, AWS S3/CloudFront).
- Backend: Python application hosting (e.g., Docker container on AWS ECS, Google Cloud Run, Heroku, Render) with FastAPI support (ASGI server like Uvicorn/Gunicorn).
- Database: Managed SQL database (e.g., PostgreSQL on AWS RDS, Google Cloud SQL).

### Scaling Strategy
- Horizontal scaling of backend API containers.
- Potentially separate, scalable worker processes/services for CPU-intensive PDF processing (using Celery, RQ, or cloud-native queues).
- CDN for frontend assets.
- Database read replicas if needed.

### Monitoring and Logging
- Centralized logging for backend services.
- API performance monitoring (APM tools).
- Frontend error tracking (Sentry, LogRocket).
- Infrastructure monitoring (CPU, memory, disk).

## Production Deployment Summary (Render + Supabase)

The application backend is successfully deployed as a Dockerized web service on **Render**, using the **Singapore** region for optimal performance for users in India.

-   **Database:** All application data (Profiles, PDFs, Biomarkers) is stored in the project's **Supabase PostgreSQL** database. Authentication is also handled by Supabase Auth.
-   **Deployment Configuration (Render UI):**
    -   **Service Type:** Web Service (Free Tier initially).
    *   **Environment:** Docker, using `backend/Dockerfile`.
    *   **Root Directory:** `backend`.
    *   **Region:** Singapore (Asia Pacific).
    *   **Start Command:** `sh -c 'python -m alembic upgrade head && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT'` (Ensures database schema migrations run before the application starts, using Python module execution for reliability).
    *   **Environment Variables:** All secrets (Supabase DB URL, Supabase JWT Secret, Anthropic API Key) and production settings (`DEBUG=False`, `LOG_LEVEL=INFO`) are configured securely via Render's environment variable management.
-   **Database Migration:** The initial database schema setup in Supabase Postgres is handled automatically during deployment by the `alembic upgrade head` part of the Start Command. (Note: No migration of *data* from local SQLite was performed, starting with an empty production database).
-   **Key Learnings/Gotchas:**
    *   Use environment variables for all configuration/secrets.
    *   Use a production-ready database (Supabase Postgres) instead of SQLite.
    *   Ensure the database connection string is compatible with the hosting environment (e.g., using Supabase Pooler if needed, though direct connection worked here).
    *   Automate schema migrations (Alembic via Start Command).
    *   Use `sh -c '...'` in Render's Docker Command field to correctly chain commands like migrations and server startup.
    *   Use `python -m <module>` to reliably execute installed Python tools like `alembic` and `uvicorn` within the container.
    *   Configure logging for production (typically `stdout`/`stderr` for cloud platforms).
    *   Configure CORS correctly for frontend integration.
    *   Implement health checks (`/health` endpoint) for monitoring.
