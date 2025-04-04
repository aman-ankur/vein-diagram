#!/bin/bash
set -e

# Run database migrations
python -m alembic upgrade head

# Start the FastAPI application
python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} 