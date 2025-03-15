# Vein Diagram

Vein Diagram is a specialized web application that transforms blood test PDFs into insightful visualizations, enabling users to track biomarkers over time, identify trends, and understand relationships between different health indicators.

## Project Overview

The platform bridges the gap between raw lab data and meaningful health insights by leveraging modern data visualization techniques and AI-powered analysis. Users can upload their blood test PDFs, and the application will extract, parse, and visualize the biomarker data.

## Features

- PDF upload and text extraction
- Biomarker data parsing and categorization
- Time-series visualizations of biomarker trends
- Correlation network graphs showing relationships between biomarkers
- Research-backed insights on biomarker relationships using Claude API

## Tech Stack

### Frontend
- React with TypeScript
- Plotly.js for visualizations
- Tailwind CSS for styling

### Backend
- Python with FastAPI
- PyPDF2 for text extraction
- Tesseract OCR for image-based PDFs
- Claude API for insights generation
- SQLite for data storage

## Project Structure

```
vein-diagram/
├── frontend/                # React frontend
│   ├── src/                 # Source code
│   │   ├── components/      # Reusable components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   ├── utils/           # Utility functions
│   │   ├── hooks/           # Custom React hooks
│   │   ├── types/           # TypeScript type definitions
│   │   ├── assets/          # Static assets
│   │   └── styles/          # CSS styles
│   ├── public/              # Public assets
│   ├── package.json         # Dependencies
│   └── tsconfig.json        # TypeScript configuration
├── backend/                 # Python backend
│   ├── app/                 # Application code
│   │   ├── api/             # API routes
│   │   ├── core/            # Core functionality
│   │   ├── db/              # Database models and setup
│   │   ├── models/          # Data models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── utils/           # Utility functions
│   ├── tests/               # Test files
│   ├── scripts/             # Utility scripts
│   └── requirements.txt     # Python dependencies
└── project-docs/            # Project documentation
```

## Getting Started

### Prerequisites

- Node.js (v18+)
- Python (v3.9+)
- Tesseract OCR

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/vein-diagram.git
   cd vein-diagram
   ```

2. Set up the frontend:
   ```
   cd frontend
   npm install
   ```

3. Set up the backend:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the backend directory (copy from `.env.example`).

### Running the Application

1. Start the backend:
   ```
   cd backend
   python -m app.main
   ```

2. Start the frontend:
   ```
   cd frontend
   npm run dev
   ```

3. Open your browser and navigate to `http://localhost:3000`.

## Testing

### Frontend Tests
```
cd frontend
npm test
```

### Backend Tests
```
cd backend
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 