# Vein Diagram: Backend Dockerization Summary

This document summarizes the steps taken to containerize the FastAPI backend application using Docker and the subsequent troubleshooting process.

## 1. Initial Dockerfile Setup (`backend/Dockerfile`)

-   Base Image: `python:3.9-slim`
-   Working Directory: `/app`
-   System Dependencies Installed (`apt-get`):
    -   `tesseract-ocr` (for OCR)
    -   `poppler-utils` (for `pdf2image`)
    -   `build-essential` (for potential C extensions during pip install)
    -   `libpq-dev` (for `psycopg2` PostgreSQL driver)
-   `.dockerignore`: Created in `backend/` to exclude `venv`, `__pycache__`, logs, etc.
-   Python Dependencies: Copied `requirements.txt` and installed using `pip install --no-cache-dir -r requirements.txt`.
-   Code Copy: Copied the rest of the application code (`COPY . .`).
-   Port Exposure: Exposed port `8000`.
-   Runtime Command (`CMD`): `["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]`

## 2. Dependency Resolution

-   **Missing Packages**: Added `PyPDF2` and `PyJWT` to `requirements.txt` to fix `ModuleNotFoundError` during container startup.
-   **Compatibility**: Pinned `numpy==1.24.4` in `requirements.txt` to resolve version conflicts with `pandas==2.0.1`.

## 3. Database Connection Configuration

-   **SQLite vs PostgreSQL**: Modified `backend/app/db/database.py` to conditionally add `connect_args={"check_same_thread": False}` to the SQLAlchemy `create_engine` call *only* if the `DATABASE_URL` starts with `sqlite`. This fixed a `psycopg2.ProgrammingError: invalid connection option "check_same_thread"` when using the PostgreSQL connection string for Supabase.

## 4. Network Connectivity Troubleshooting (Container -> Supabase)

After fixing the initial dependency and database configuration errors, the container failed to start when using the Supabase `DATABASE_URL`, citing network issues.

-   **Error**: `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server at "db.qbhopetkwddrqqlsucqi.supabase.co" (...) port 5432 failed: Network is unreachable`
-   **Diagnostics Added**: Modified `Dockerfile` to include `iputils-ping`, `curl`, and `dnsutils` via `apt-get`. Rebuilt the image multiple times.
-   **Connectivity Tests**:
    -   `ping 8.8.8.8`: **Success**. Confirmed general internet access from the container.
    -   `ping db.qbhopetkwddrqqlsucqi.supabase.co`: **Failure** ("Network is unreachable"). Container could not reach the Supabase host by name.
    -   `curl -v https://db.qbhopetkwddrqqlsucqi.supabase.co`: **Failure**. Resolved hostname to IPv6 address but failed with "Network is unreachable".
    -   `curl -4 -v https://db.qbhopetkwddrqqlsucqi.supabase.co`: **Failure**. Failed with "Could not resolve host", indicating an issue resolving the A (IPv4) record.
-   **DNS Investigation**:
    -   `cat /etc/resolv.conf`: Showed the container using Docker's internal DNS server (`192.168.65.7`).
    -   `docker run --dns 8.8.8.8 ...`: Attempted to force Google's public DNS. Still resulted in the "Network is unreachable" error, connecting via IPv6.
-   **Next Step (Interrupted)**: Attempting to use `dig +short A db.qbhopetkwddrqqlsucqi.supabase.co` inside the container to get the explicit IPv4 address, with the goal of using the IP directly in the `DATABASE_URL` as a workaround for the IPv6 routing/DNS issue.
