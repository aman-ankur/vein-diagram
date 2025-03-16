# Vein Diagram: Technical Context

## Technologies Used

### Frontend Stack
- **React**: JavaScript library for building user interfaces
- **TypeScript**: Typed superset of JavaScript for improved developer experience
- **Vite**: Modern frontend build tool and development server
- **Tailwind CSS**: Utility-first CSS framework for rapid UI development
- **Jest**: JavaScript testing framework for unit and component testing
- **React Testing Library**: Testing utilities for React components

### Backend Stack
- **Python**: Core programming language for the backend
- **FastAPI**: Modern, high-performance web framework for building APIs
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM) library
- **Pydantic**: Data validation and settings management using Python type annotations
- **Pytest**: Testing framework for Python code
- **PDF Processing Libraries**:
  - **PyPDF2/PyMuPDF**: PDF parsing and text extraction
  - **pdfplumber**: More detailed PDF content extraction
  - **pytesseract**: OCR capabilities for image-based text in PDFs

### Data Visualization
- **D3.js**: JavaScript library for producing dynamic, interactive data visualizations
- **Chart.js/Recharts**: React-friendly charting libraries for time-series data

### External APIs
- **Claude API**: Anthropic's AI model for generating biomarker insights and explanations

### Development Tools
- **Git**: Version control system
- **npm/yarn**: Package management for frontend dependencies
- **pip/venv**: Package management for Python dependencies
- **ESLint/Prettier**: Code linting and formatting for JavaScript/TypeScript
- **Black/isort**: Code formatting for Python

## Development Setup

### Local Development Environment
```
vein-diagram/
├── frontend/           # React frontend application
│   ├── src/            # Source code
│   ├── public/         # Static assets
│   ├── package.json    # Dependencies and scripts
│   └── vite.config.ts  # Vite configuration
│
├── backend/            # FastAPI backend application
│   ├── app/            # Application code
│   │   ├── api/        # API routes
│   │   ├── models/     # Database models
│   │   ├── schemas/    # Pydantic schemas
│   │   └── services/   # Business logic
│   ├── tests/          # Test suite
│   └── requirements.txt # Python dependencies
│
├── memory-bank/        # Project documentation
└── project-docs/       # Additional documentation
```

### Development Workflow
1. **Backend Development**:
   - Python virtual environment setup with required dependencies
   - FastAPI server with hot-reloading for development
   - Database migrations for schema changes
   - Automated tests for API endpoints and services

2. **Frontend Development**:
   - Vite development server with hot module replacement
   - Component-driven development approach
   - TypeScript for type checking during development
   - Jest for running unit and component tests

3. **Integration**:
   - Frontend configured to communicate with backend API
   - Proxy setup for local development to avoid CORS issues
   - Shared type definitions between frontend and backend

## Technical Constraints

### PDF Processing Challenges
- **Diverse Lab Formats**: Different lab providers use varying PDF formats
- **OCR Limitations**: Text extraction from image-based PDFs may have accuracy issues
- **Structure Extraction**: Identifying the structure of tables and data in PDFs
- **Reference Range Parsing**: Extracting and normalizing reference ranges across different formats

### Performance Considerations
- **PDF Processing Time**: Extracting data from PDFs can be computationally intensive
- **Visualization Rendering**: Complex visualizations with large datasets may impact frontend performance
- **API Response Times**: Ensuring fast response times for data-heavy API endpoints

### Security and Privacy
- **Health Data Sensitivity**: Blood test data is sensitive personal health information
- **PDF Content Security**: Ensuring uploaded PDFs don't contain malicious content
- **API Security**: Protecting API endpoints from unauthorized access

### Browser Compatibility
- **Modern Browser Focus**: Targeting modern browsers with good support for ES6+ features
- **Mobile Responsiveness**: Ensuring good user experience on various device sizes
- **SVG/Canvas Support**: Required for data visualizations

## Dependencies

### Critical Frontend Dependencies
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "d3": "^7.8.0",
    "axios": "^1.3.0",
    "tailwindcss": "^3.3.0"
  },
  "devDependencies": {
    "vite": "^4.3.0",
    "jest": "^29.5.0",
    "@testing-library/react": "^14.0.0",
    "eslint": "^8.38.0",
    "prettier": "^2.8.0"
  }
}
```

### Critical Backend Dependencies
```
fastapi==0.95.0
uvicorn==0.21.0
sqlalchemy==2.0.0
pydantic==1.10.0
pymupdf==1.21.0
pdfplumber==0.7.0
pytesseract==0.3.10
pytest==7.3.0
httpx==0.24.0
python-multipart==0.0.6
```

## Integration Points

### Frontend-Backend Integration
- RESTful API endpoints for communication
- JSON data format for request/response payloads
- Type-safe API contracts using TypeScript interfaces and Pydantic models

### External API Integration
- Claude API for biomarker insights and explanations
- Potential future integrations with health data platforms

### File System Integration
- Temporary storage for uploaded PDFs during processing
- Potential persistent storage for processed data

## Deployment Considerations

### Hosting Requirements
- Frontend: Static site hosting (Netlify, Vercel, etc.)
- Backend: Python application hosting with FastAPI support
- Database: SQL database for structured data storage

### Scaling Strategy
- Horizontal scaling for API servers
- Separate worker processes for CPU-intensive PDF processing
- CDN for static assets and frontend distribution

### Monitoring and Logging
- API performance monitoring
- Error tracking and reporting
- Usage analytics for feature optimization
