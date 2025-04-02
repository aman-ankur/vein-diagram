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

### Environment Variables

The application requires several environment variables to function properly:

#### Backend Environment Variables
- `DATABASE_URL`: Connection string for the database (default: SQLite)
- `API_HOST`: Host for the API server (default: 0.0.0.0)
- `API_PORT`: Port for the API server (default: 8000)
- `ANTHROPIC_API_KEY`: Your Anthropic API key for Claude AI integration
- `TESSERACT_PATH`: Path to Tesseract OCR executable

To set up your environment:
1. Copy `.env.example` to `.env` in the backend directory
2. Fill in your actual API keys and configuration values
3. Never commit your `.env` file to version control

### Security Notes

This project uses the Anthropic Claude API for biomarker analysis. To keep your API keys secure:

1. Never hardcode API keys in your source code
2. Always use environment variables for sensitive information
3. Use the provided pre-commit hook to check for accidentally committed secrets:
   ```
   chmod +x check_secrets.sh
   chmod +x .git/hooks/pre-commit
   ```
4. If you accidentally commit a secret, rotate your API keys immediately

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


## Database Cleanup

   To delete all existing data related to biomarkers and PDFs in the database, you can use the provided cleanup script. This script will create a backup of the database before performing the deletion.

   ### Steps to Run the Cleanup Script

   1. **Navigate to the Backend Directory**: Open your terminal and navigate to the backend directory of your project:
      ```bash
      cd /path/to/your/project/backend
      ```

   2. **Run the Cleanup Script**: Execute the following command to run the cleanup script:
      ```bash
      python3 db_cleanup.py
      ```

   3. **Confirm the Operation**: The script will prompt you for confirmation before proceeding with the deletion. Type `y` and press Enter to confirm.

   **Note**: This operation will permanently delete all data from the database, so ensure you have a backup if needed.

## Health Analysis Dashboard Redesign

Our health analysis dashboard has been redesigned with a modern, elegant dark mode aesthetic inspired by contemporary reading apps. The new design provides a calm, professional, and medically authoritative interface while being visually appealing and easy to understand.

### Design Features

#### Color Scheme
- **Dark Mode Foundation**: Deep blue-black background (#0f172a) with subtle gradients for visual depth
- **Muted Color Palette**: Soft indigo primary color (#6366f1) with pink accents (#ec4899)
- **Intuitive Health Indicators**: Neutral colors for normal values, subtle red for concerning metrics, and green for healthy ranges

#### Typography
- **Clean Font Hierarchy**: Uses Inter as the primary font with clear visual hierarchy
- **Improved Readability**: Optimized letter spacing and line heights for better text legibility
- **Consistent Text Sizing**: Standardized font sizes across components

#### Layout Improvements
- **Card-Based Organization**: Biomarker data is organized in expandable/collapsible card sections by category
- **Proper Whitespace**: Generous spacing between elements for better visual breathing room
- **Category Filtering**: Easy filtering system with visual chips for different biomarker categories

#### Visual Elements
- **Data Visualizations**: Small charts and visual indicators for key metrics
- **Subtle Animations**: Smooth transitions and hover effects for interactive elements
- **Soft Shadows & Rounded Corners**: Cards and buttons with subtle elevation and rounded borders for a modern feel

#### UI Components
- **Redesigned Smart Summary**: More visually appealing "Generate Smart Summary" button
- **Consistent Navigation**: Improved toggle between current report and history views
- **Progress Indicators**: Subtle loading states and completion indicators

### Components

The redesign includes updates to the following components:
- **BiomarkerPage**: Main dashboard layout with improved header and filtering
- **BiomarkerTable**: Enhanced data table with better typography and visual indicators
- **ExplanationModal**: Redesigned AI explanation modal with intuitive data visualization
- **ViewToggle**: Updated toggle component for switching between current and history views
- **Theme**: New dark mode theme with improved color scheme and typography

### Screenshots

[Screenshots will be added when available]