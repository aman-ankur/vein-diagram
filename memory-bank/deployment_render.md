# Vein Diagram: Production Deployment (Render + Supabase)

This document summarizes the successful deployment of the Vein Diagram backend to Render, using Supabase for the database and authentication.

## Overview

-   **Platform:** Render (Web Service - Free Tier initially)
-   **Region:** Singapore (Asia Pacific) - Chosen for optimal latency for users in India.
-   **Database:** Supabase PostgreSQL (Handles all application data: Profiles, PDFs, Biomarkers).
-   **Authentication:** Supabase Auth.
-   **Deployment Method:** Docker container deployment via connected Git repository.
-   **Frontend:** Deployed on Vercel (see `vercel_deployment.md` for details)

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
    *   `FRONTEND_URL`: Set to the Vercel production URL to support CORS
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
-   **Health Checks:** Implemented health check endpoint (`/health`) for platform monitoring and keep-alive pinging.
-   **CORS:** Ensured Cross-Origin Resource Sharing is configured correctly in FastAPI to allow requests from the Vercel-hosted frontend domains:
    ```python
    origins = [
        # Local development URLs
        "http://localhost:3000",
        # ...
        # Production URLs
        "https://vein-diagram-m2qjunh4t-aman-ankurs-projects.vercel.app",
        "https://vein-diagram.vercel.app",
        os.getenv("FRONTEND_URL", ""),
    ]
    ```

## Integration with Vercel Frontend

-   The frontend is deployed on Vercel and connects to the Render backend (see `vercel_deployment.md`).
-   Communication is handled through RESTful API calls.
-   Environment variables in Vercel point to the Render backend URL.

## Free Tier Considerations

-   **Instance Spindown:** Render free tier spins down after periods of inactivity.
    *   **Solution:** Implemented a keep-alive strategy using GitHub Actions and client-side pinging (see `render_uptime.md`).
-   **Cold Starts:** First request after inactivity may be slow due to cold starts.
    *   **Impact:** Initial load may take 30-60 seconds after inactivity.
    *   **Mitigation:** Keep-alive pinging helps minimize cold starts during active usage hours.
-   **Resource Limits:** Free tier has CPU and memory limitations.
    *   **Consideration:** Monitor performance and consider upgrading if usage increases.

## Current Status

-   The backend API is live and accessible at its `.onrender.com` URL.
-   Successfully integrated with the Vercel-hosted frontend.
-   Keep-alive mechanisms are in place to prevent excessive spindowns.
-   Functional end-to-end system with authentication, file uploads, data visualization, and AI features working.
