# Vein Diagram: Technical Context

## Technologies Used

### Frontend Stack
- **React**: JavaScript library for building user interfaces
- **TypeScript**: Typed superset of JavaScript for improved developer experience
- **Vite**: Modern frontend build tool and development server
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Jest**: JavaScript testing framework for unit and component testing
- **React Testing Library**: Testing utilities for React components
- **Axios**: Promise-based HTTP client for API communication

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
- **HTTPX**: Asynchronous HTTP client for communicating with external APIs (like Claude).

### Data Visualization
- **D3.js**: Primary library for custom, dynamic, interactive data visualizations.
- **Recharts/Chart.js**: Potentially used for simpler, standard chart types if needed.

### External APIs
- **Claude API**: Anthropic's AI model for generating biomarker insights and explanations.

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
│   │   ├── components/ # UI Components (incl. Profile/Favorite related: FavoriteBiomarkersGrid, BiomarkerTile, AddFavoriteModal)
│   │   ├── pages/      # Page Components (ProfileManagement, VisualizationPage, BiomarkerHistoryPage)
│   │   ├── services/   # API Services (profileService.ts, biomarkerService.ts)
│   │   ├── utils/      # Utility functions (favoritesUtils.ts, biomarkerUtils.ts)
│   │   ├── contexts/   # React Contexts (e.g., for Profile state)
│   │   └── types/      # TypeScript types (Profile, Favorite, Biomarker, etc.)
│   ├── public/
│   ├── package.json
│   └── vite.config.ts
│
├── backend/            # FastAPI backend application
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/ # API Routes (biomarker_routes.py, profile_routes.py, pdf_routes.py)
│   │   ├── models/     # DB Models (biomarker_model.py, profile_model.py, pdf_model.py)
│   │   ├── schemas/    # Pydantic Schemas (biomarker_schema.py, profile_schema.py, pdf_schema.py)
│   │   └── services/   # Business Logic (pdf_service.py, llm_service.py, biomarker_parser.py, profile_matcher.py)
│   ├── tests/          # Test suite (incl. tests for profiles/favorites)
│   │   ├── api/        # API route tests (test_profile_routes.py, test_biomarker_routes.py)
│   │   └── services/   # Service layer tests
│   └── requirements.txt # Python dependencies
│
├── memory-bank/        # Project documentation & context
└── project-docs/       # Additional project documents
```

### Development Workflow
1. **Backend Development**:
   - Python virtual environment (`vein-d/`) setup with dependencies from `requirements.txt`.
   - FastAPI server (`uvicorn`) with hot-reloading for development.
   - Database migrations potentially needed for schema changes (e.g., adding profile tables).
   - Automated tests (`pytest`) for API endpoints and services, including profile/favorite logic.

2. **Frontend Development**:
   - Vite development server (`npm run dev`) with hot module replacement.
   - Component-driven development approach.
   - TypeScript for type checking during development.
   - Jest (`npm test`) for running unit and component tests, including profile/favorite components.

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

### Performance Considerations
- **PDF Processing Time**: Can be significant for large/complex PDFs, mitigated by background processing.
- **Visualization Rendering**: Large datasets require optimization (sampling, virtualization, efficient D3 usage).
- **API Response Times**: Database query optimization, caching (backend/frontend) are important, especially with profile filtering.
- **LLM API Latency**: Calls to Claude API add latency; caching insights is crucial.

### Security and Privacy
- **Health Data Sensitivity**: All data handling must prioritize privacy (HIPAA considerations if applicable in target market). Data stored should be minimized and secured.
- **PDF Content Security**: Uploaded files could contain risks; sanitization or isolated processing might be needed in production.
- **API Security**: Authentication/Authorization will be needed post-MVP to protect profile data.

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
- Key endpoints for Profiles (`/api/profiles/...`), Favorites (`/api/profiles/{profile_id}/favorites/...`), Biomarkers (`/api/profiles/{profile_id}/biomarkers/...`), PDFs (`/api/pdfs/...`).

### External API Integration
- **Claude API**: Via `llm_service.py` using `httpx` to send prompts and receive text for extraction and insights. Requires API key management.

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
