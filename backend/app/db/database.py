from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from urllib.parse import urlparse, parse_qs

# Get the database URL from environment variables or use a default SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vein_diagram.db")

# If using Supabase, modify the URL to use the transaction pooler
if 'supabase' in DATABASE_URL:
    # Parse the original URL
    parsed = urlparse(DATABASE_URL)
    # Remove 'db.' prefix if it exists and use transaction pooler port
    host = parsed.hostname.replace('db.', '')
    # Reconstruct the URL with transaction pooler settings
    DATABASE_URL = f"postgresql://{parsed.username}:{parsed.password}@{host}:6543/{parsed.path[1:]}?sslmode=require"

# Conditionally add connect_args only for SQLite
engine_args = {
    "pool_pre_ping": True,  # Enable connection health checks
    "pool_recycle": 300,    # Recycle connections every 5 minutes
}

if DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}
else:
    # For PostgreSQL, add specific connection parameters
    engine_args["connect_args"] = {
        "connect_timeout": 30,        # Increased timeout
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        "application_name": "vein-diagram-backend"  # Help identify connection in logs
    }

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, **engine_args)

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
