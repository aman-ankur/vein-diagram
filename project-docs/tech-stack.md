# Vein Diagram: Technology Stack

## Frontend

### React
- **Justification**: Component-based architecture enables rapid development and maintains clean separation of concerns
- **Key Features**:
  - Reusable visualization components
  - Efficient rendering with virtual DOM
  - Rich ecosystem of compatible libraries

### D3.js
- **Justification**: Powerful library for creating custom, dynamic, and interactive data visualizations. Allows fine-grained control over rendering.
- **Key Features**:
  - Data binding to the DOM.
  - Wide range of visualization techniques.
  - Control over transitions and interactions.

### Material UI
- **Justification**: Provides pre-built React components following Material Design principles, speeding up UI development for certain sections (e.g., Account page). Offers theming capabilities.
- **Key Features**:
  - Comprehensive set of UI components.
  - Theming and customization options (`styled` API).

### Tailwind CSS
- **Justification**: Utility-first CSS framework for rapid styling without custom CSS
- **Key Features**:
  - Responsive design out of the box
  - Consistent design system
  - Minimal bundle size with purging

## Backend

### Python
- **Justification**: Excellent support for data processing, scientific computing, and AI integration
- **Key Features**:
  - Rich ecosystem for PDF processing and data analysis
  - Easy integration with Tesseract OCR
  - Straightforward API access to Claude

### FastAPI
- **Justification**: Modern, high-performance Python web framework with automatic documentation
- **Key Features**:
  - Asynchronous request handling
  - Automatic OpenAPI documentation
  - Built-in validation with Pydantic models
  - Native support for Python type hints

## Data Processing & AI

### PyMuPDF (fitz)
- **Justification**: Efficient and robust library for PDF text and image extraction. Preferred over PyPDF2 for better handling of various PDF structures.
- **Key Features**:
  - Fast text extraction.
  - Image extraction capabilities.
  - Metadata access.

### Tesseract OCR (with pytesseract)
- **Justification**: Leading open-source OCR engine for extracting text from images
- **Key Features**:
  - Supports multiple languages
  - High accuracy for clean documents
  - Python integration via pytesseract

### Claude API
- **Justification**: Advanced language model for interpreting complex document structures and generating insights
- **Key Features**:
  - Natural language understanding for varied lab report formats
  - Ability to extract structured data from unstructured text
  - Research-backed insights generation

## Database & Auth

### PostgreSQL (via Supabase)
- **Justification**: Robust, production-ready relational database. Supabase provides a managed instance with a generous free tier.
- **Key Features**:
  - ACID compliant.
  - Supports complex queries and JSON data types.
  - Scalable.
  - Managed backups and extensions via Supabase.

### Supabase Auth
- **Justification**: Provides a complete authentication solution (Email/Pass, OAuth) as a service, integrating well with the Supabase database.
- **Key Features**:
  - Secure user management.
  - JWT handling.
  - Social logins (Google).
  - Row Level Security (integrates with Postgres).

## Deployment

### Docker
- **Justification**: Containerization for consistent environments and simplified deployment
- **Key Features**:
  - Encapsulate all dependencies
  - Consistent environment across development and production
  - Simple scaling for future growth

### Vercel (Frontend)
- **Justification**: Optimized platform for deploying frontend applications (React/Vite). Seamless Git integration and global CDN.
- **Key Features**:
  - Automatic CI/CD from Git.
  - Global CDN for performance.
  - Preview deployments.
  - Generous free tier.

### Render (Backend)
- **Justification**: Simplified deployment for Dockerized backend services with Git integration and managed infrastructure. Offers a suitable free tier for starting.
- **Key Features**:
  - Direct Docker deployment from Git.
  - Managed infrastructure (Web Service).
  - Environment variable management.
  - Custom start commands (for migrations).
