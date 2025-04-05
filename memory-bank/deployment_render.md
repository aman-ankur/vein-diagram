# Vein Diagram: Production Deployment (Render + Supabase)

This document summarizes the successful deployment of the Vein Diagram backend to Render, using Supabase for the database and authentication.

## Overview

-   **Platform:** Render (Web Service - Free Tier initially)
-   **Region:** Singapore (Asia Pacific) - Chosen for optimal latency for users in India.
-   **Database:** Supabase PostgreSQL (Handles all application data: Profiles, PDFs, Biomarkers).
-   **Authentication:** Supabase Auth.
-   **Deployment Method:** Docker container deployment via connected Git repository.

## Deployment Configuration (Render UI)

-   **Service Type:** Web Service.
-   **Environment:** Docker, using `backend/Dockerfile`.
-   **Root Directory:** `backend`.
-   **Start Command:** `./start.sh` (or similar command specified in Render UI to execute the custom start script).
    *   A custom script (`backend/start.sh`) is used to manage the startup sequence reliably.
    *   The script handles waiting for the database, running Alembic migrations (`alembic upgrade head`) with retries and error handling, and then starting the Uvicorn server (`uvicorn app.main:app --host 0.0.0.0 --port $PORT`).
    *   The `Dockerfile` copies `start.sh` and makes it executable (`RUN chmod +x start.sh`).
-   **Environment Variables:** Configured securely via Render's environment settings:
    *   `DATABASE_URL`: Supabase PostgreSQL connection string.
    *   `SUPABASE_JWT_SECRET`: Supabase JWT secret for token validation.
    *   `ANTHROPIC_API_KEY`: Anthropic API key.
    *   `DEBUG`: `False`
    *   `LOG_LEVEL`: `INFO`
    *   (Other necessary Supabase variables like `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` if used directly).

## Database Migration

-   **Schema:** Handled automatically on deployment by `alembic upgrade head` in the Start Command, targeting the Supabase Postgres DB.
-   **Data:** No data migration from local SQLite was performed; the production database started empty.

## Key Learnings & Troubleshooting

-   **Database Choice:** SQLite is unsuitable for production on platforms like Render due to ephemeral filesystems; a managed database like Supabase Postgres is required.
-   **Startup Reliability:** Directly chaining commands (`&&`) in Render's "Docker Command" field proved unreliable for migrations and server startup.
    *   **Solution:** A custom `start.sh` script was implemented within the `backend` directory. This script includes logic to wait for the database, run `alembic upgrade head` with retries/error handling, and then execute `uvicorn`. The Render "Docker Command" was updated to simply execute this script (e.g., `./start.sh`). This provides robust control over the startup sequence.
-   **Configuration:** Always use environment variables for secrets and configuration.
-   **Logging:** Configure application logging to output to `stdout`/`stderr` for collection by the platform (Render).
-   **Health Checks:** Implement health check endpoints (e.g., `/health`) for platform monitoring.
-   **CORS:** Ensure Cross-Origin Resource Sharing is configured correctly in FastAPI to allow requests from the Vercel-hosted frontend domain.

## Current Status

-   The backend API is live and accessible at its `.onrender.com` URL.
-   The frontend (on Vercel) needs its API base URL environment variable updated to point to the live Render backend URL.
