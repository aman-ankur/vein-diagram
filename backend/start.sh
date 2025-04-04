#!/bin/bash
set -e

echo "Starting deployment process..."

# Function to test database connection
test_db_connection() {
    python << END
import os
from sqlalchemy import create_engine
from urllib.parse import urlparse, urlunparse
import time

# Get database URL
db_url = os.getenv("DATABASE_URL", "")
if not db_url:
    raise Exception("DATABASE_URL not set")

# Modify URL for Supabase if needed
if 'supabase' in db_url:
    parsed = urlparse(db_url)
    # Only remove 'db.' from hostname if it exists, keep the original port
    host = parsed.hostname.replace('db.', '')
    # Reconstruct the URL maintaining the original port and query parameters
    netloc = f"{parsed.username}:{parsed.password}@{host}:{parsed.port}"
    db_url = urlunparse((
        parsed.scheme,
        netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))

# Try to connect
max_retries = 5
retry_count = 0
while retry_count < max_retries:
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        print("Database connection successful!")
        break
    except Exception as e:
        retry_count += 1
        if retry_count == max_retries:
            raise Exception(f"Failed to connect to database after {max_retries} attempts: {str(e)}")
        print(f"Database connection attempt {retry_count} failed, retrying in 5 seconds...")
        time.sleep(5)
END
}

# Wait for database to be ready
echo "Testing database connection..."
test_db_connection

# Initialize Alembic if needed
echo "Checking Alembic status..."
if ! python -m alembic current 2>/dev/null; then
    echo "Initializing Alembic version control..."
    python -m alembic stamp head
    echo "Alembic initialized successfully."
fi

# Check current migration status
echo "Checking current migration status..."
CURRENT_REV=$(python -m alembic current 2>/dev/null | grep "Current revision" | cut -d: -f2 | tr -d ' ')
if [ -z "$CURRENT_REV" ]; then
    echo "No current revision found, marking as head..."
    python -m alembic stamp head
else
    echo "Current revision is: $CURRENT_REV"
fi

# Try to run migrations
echo "Attempting to apply any pending migrations..."
if ! python -m alembic upgrade head; then
    echo "Migration failed. This might be because:"
    echo "1. The migrations were already applied"
    echo "2. There was a genuine error"
    echo "Checking database schema..."
    
    # Verify database schema
    python << END
import sys
from sqlalchemy import create_engine, inspect
from app.db.database import Base
import os
from urllib.parse import urlparse, urlunparse

# Get database URL
db_url = os.getenv("DATABASE_URL", "")
if 'supabase' in db_url:
    parsed = urlparse(db_url)
    # Only remove 'db.' from hostname if it exists, keep the original port
    host = parsed.hostname.replace('db.', '')
    # Reconstruct the URL maintaining the original port and query parameters
    netloc = f"{parsed.username}:{parsed.password}@{host}:{parsed.port}"
    db_url = urlunparse((
        parsed.scheme,
        netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))

engine = create_engine(db_url)
inspector = inspect(engine)

# Get all expected tables from SQLAlchemy models
expected_tables = set(Base.metadata.tables.keys())
actual_tables = set(inspector.get_table_names())

# Compare
missing_tables = expected_tables - actual_tables
if missing_tables:
    print(f"Missing tables: {missing_tables}")
    sys.exit(1)
else:
    print("All expected tables exist in the database.")
    sys.exit(0)
END
    
    if [ $? -eq 0 ]; then
        echo "Database schema verification passed, proceeding with application start"
    else
        echo "Database schema verification failed"
        exit 1
    fi
fi

# Start the FastAPI application
echo "Starting FastAPI application..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 4 