# Vein Diagram: Backend Dockerization Summary

This document summarizes the containerization process for the FastAPI backend application.

## 1. Dockerfile Configuration

-   Base Image: `python:3.9-slim`
-   Key Dependencies:
    -   `tesseract-ocr` (OCR functionality)
    -   `poppler-utils` (PDF processing)
    -   `libpq-dev` (PostgreSQL driver)
-   Port: `8000`
-   Runtime: `uvicorn app.main:app --host 0.0.0.0 --port 8000`

## 2. Key Dependency Resolutions

-   Added missing `PyPDF2` and `PyJWT` packages
-   Pinned `numpy==1.24.4` to resolve conflicts with `pandas==2.0.1`
-   Modified `database.py` to conditionally use SQLite-specific parameters only when needed

## 3. Supabase Connection Issue & Solution

### Issue Identified
Docker containers by default use IPv4, while Supabase's direct database connection requires IPv6 connectivity, resulting in "Network unreachable" errors.

### Available Connection Options
Supabase provides three connection methods:
1. **Direct Connection**: Not IPv4 compatible
2. **Transaction Pooler**: IPv4 compatible, ideal for stateless applications
3. **Session Pooler**: IPv4 compatible, alternative to Direct Connection

### Solution
Used the Transaction Pooler connection format with IPv4 support:

```bash
# Format of working DATABASE_URL (sensitive details removed)
postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require
```

### Production Configuration
```bash
docker run -p 8000:8000 \
  --network=vein-diagram-net \
  --dns 8.8.8.8 \
  -e DATABASE_URL="postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require" \
  -e SUPABASE_JWT_SECRET="[REDACTED]" \
  -e SUPABASE_URL="https://[PROJECT_ID].supabase.co" \
  -e SUPABASE_SERVICE_KEY="[REDACTED]" \
  -e ANTHROPIC_API_KEY="[REDACTED]" \
  --name vein-diagram-backend \
  vein-diagram-backend
```

## 4. Key Learnings

1. Always check database provider documentation for different connection methods
2. Consider network compatibility (IPv4 vs IPv6) when dockerizing applications
3. Connection poolers provide better stability for containerized applications
4. Use Docker Compose or Kubernetes for production to manage environment variables securely
