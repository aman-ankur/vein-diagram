#!/bin/bash
set -e

echo "Starting deployment process..."

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 5

# Run database migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Start the FastAPI application
echo "Starting FastAPI application..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4 