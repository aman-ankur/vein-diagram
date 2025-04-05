# Vein Diagram

Vein Diagram transforms blood test PDFs into insightful visualizations, helping users track biomarkers, identify trends, and understand their health data over time using AI-powered analysis.

## Key Features

*   **PDF Data Extraction:** Automatically parses biomarker data from uploaded lab reports.
*   **Profile Management:** Organizes data for multiple individuals.
*   **Time-Series Visualization:** Tracks biomarker changes over time using D3.js.
*   **Favorite Biomarkers:** Allows users to pin key biomarkers for quick access.
*   **Health Score:** Provides an at-a-glance summary of wellness based on biomarker data.
*   **AI-Powered Insights:** Uses Claude API for biomarker explanations and health summaries.
*   **Authentication:** Secure user accounts via Supabase Auth (Email/Password, Google).

## Tech Stack

*   **Frontend:** React, TypeScript, Vite, Tailwind CSS, Material UI, D3.js, Axios
*   **Backend:** Python, FastAPI, SQLAlchemy, Alembic, Pydantic
*   **Database:** PostgreSQL (via Supabase)
*   **Authentication:** Supabase Auth
*   **AI:** Anthropic Claude API
*   **PDF Processing:** PyMuPDF, pdf2image, pytesseract
*   **Deployment:** Frontend on Vercel, Backend on Render (Docker)

## Project Structure

```
vein-diagram/
├── frontend/       # React frontend (Vite + TypeScript)
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── contexts/
│   │   ├── types/
│   │   └── ...
│   └── ...
├── backend/        # FastAPI backend (Python)
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── ...
│   ├── tests/
│   ├── alembic/    # Database migrations
│   ├── scripts/
│   ├── Dockerfile
│   ├── start.sh    # Production start script
│   └── requirements.txt
├── memory-bank/    # Project documentation & context
└── README.md
```

## Getting Started

### Prerequisites

*   Node.js (v18+)
*   Python (v3.9+)
*   Tesseract OCR (ensure it's in your system's PATH or configure `TESSERACT_PATH` if needed)
*   Access to Supabase (for Auth and Database)
*   Anthropic API Key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yourusername/vein-diagram.git
    cd vein-diagram
    ```

2.  **Setup Frontend:**
    ```bash
    cd frontend
    npm install
    # Configure Vercel environment variables (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_BASE_URL)
    cd ..
    ```

3.  **Setup Backend:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    pip install -r requirements.txt
    # Configure backend environment variables (see below)
    cd ..
    ```

### Configuration (Backend)

1.  Navigate to the `backend` directory.
2.  Copy `.env.example` to `.env`.
3.  Fill in the required values in `.env`:
    *   `DATABASE_URL`: Your Supabase PostgreSQL connection string.
    *   `SUPABASE_URL`: Your Supabase project URL.
    *   `SUPABASE_SERVICE_KEY`: Your Supabase service role key.
    *   `SUPABASE_JWT_SECRET`: Your Supabase JWT secret.
    *   `ANTHROPIC_API_KEY`: Your Anthropic API key.
    *   Set `DEBUG=True` for local development.
    *   Adjust `LOG_LEVEL` if needed (e.g., `DEBUG`).
    *   Verify `TESSERACT_PATH` only if `pytesseract` cannot find the executable automatically.

**Important:** Never commit your `.env` file to version control.

### Running Locally

1.  **Run Database Migrations (if needed):**
    ```bash
    cd backend
    alembic upgrade head
    ```

2.  **Start Backend Server:**
    ```bash
    # Still in backend directory
    uvicorn app.main:app --reload --port 8000
    ```

3.  **Start Frontend Server:**
    ```bash
    cd ../frontend
    npm run dev
    ```

4.  Access the application at `http://localhost:5173` (or the port specified by Vite).

## Testing

*   **Frontend:** `cd frontend && npm test`
*   **Backend:** `cd backend && PYTHONPATH=. pytest tests/` (Ensure `PYTHONPATH` includes the backend root)

## Deployment

*   The **Frontend** is deployed via **Vercel**, connected to the Git repository. Environment variables for Supabase and the backend API URL must be configured in Vercel.
*   The **Backend** is deployed via **Render** as a Docker container, connected to the Git repository and using the Supabase database.
*   See `memory-bank/deployment_render.md` for detailed backend deployment steps and configuration.
