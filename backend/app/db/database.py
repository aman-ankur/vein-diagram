from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
import os
from urllib.parse import urlparse, parse_qs, urlunparse
import logging
from typing import Generator
from fastapi import Depends

# Set up logging
logger = logging.getLogger(__name__)

# Get the database URL from environment variables or use a default SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vein_diagram.db")

# If using Supabase, modify the URL to maintain the pooler configuration
if 'supabase' in DATABASE_URL:
    # Parse the original URL
    parsed = urlparse(DATABASE_URL)
    # Only remove 'db.' from hostname if it exists
    host = parsed.hostname.replace('db.', '')
    # Reconstruct the URL maintaining the original port and query parameters
    netloc = f"{parsed.username}:{parsed.password}@{host}:{parsed.port}"
    DATABASE_URL = urlunparse((
        parsed.scheme,
        netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment
    ))

logger.info(f"Database type: {'SQLite' if DATABASE_URL.startswith('sqlite') else 'PostgreSQL'}")

# Base configuration for both SQLite and PostgreSQL
engine_args = {
    "pool_pre_ping": True,  # Enable connection health checks
    "pool_recycle": 300,    # Recycle connections every 5 minutes
    "pool_size": 20,        # Maximum number of connections in the pool
    "max_overflow": 10,     # Maximum number of connections that can be created beyond pool_size
    "echo": False          # Set to True to log all SQL statements
}

# Configure database-specific settings
if DATABASE_URL.startswith("sqlite"):
    logger.info("Configuring SQLite-specific parameters")
    engine_args.update({
        "connect_args": {"check_same_thread": False},
        # SQLite-specific optimizations
        "isolation_level": "SERIALIZABLE"  # SQLite supported isolation level
    })
    
    # Enable SQLite foreign key support and other optimizations
    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
        cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes with reasonable safety
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache size
        cursor.close()
else:
    logger.info("Configuring PostgreSQL-specific parameters")
    engine_args.update({
        "connect_args": {
            "connect_timeout": 30,        # Connection timeout in seconds
            "keepalives": 1,             # Enable TCP keepalive
            "keepalives_idle": 30,       # Seconds between TCP keepalive probes
            "keepalives_interval": 10,    # Seconds between TCP keepalive probes when the connection is idle
            "keepalives_count": 5,       # Failed keepalive probes before dropping connection
            "application_name": "vein-diagram-backend"  # Help identify connection in logs
        },
        # PostgreSQL-specific optimizations
        "isolation_level": "READ COMMITTED",  # Standard isolation level for web apps
        "pool_timeout": 30,  # Seconds to wait for a connection from the pool
        "max_identifier_length": 63  # PostgreSQL's identifier length limit
    })

# Create the SQLAlchemy engine with error handling
try:
    engine = create_engine(DATABASE_URL, **engine_args)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {str(e)}")
    raise

# Create a SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base class
Base = declarative_base()

def get_db() -> Generator:
    """
    FastAPI dependency that provides a database session.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        # Log the error but don't reraise for certain exceptions to allow graceful API responses
        error_message = str(e)
        logger.error(f"Database session error: {error_message}")
        
        # Only rollback if it's an active transaction error
        # but not for "not found" type errors that might be handled gracefully by the API
        if "not found" not in error_message.lower() and "404" not in error_message:
            try:
                db.rollback()
            except Exception as rollback_error:
                logger.error(f"Error during session rollback: {str(rollback_error)}")
        
        # Reraise the exception for proper error handling
        raise
    finally:
        try:
            db.close()
        except Exception as close_error:
            logger.error(f"Error closing database session: {str(close_error)}")

def init_db() -> None:
    """
    Initialize the database by creating all tables.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def dispose_engine() -> None:
    """
    Properly dispose of the database engine.
    Call this when shutting down the application.
    """
    try:
        engine.dispose()
        logger.info("Database engine disposed successfully")
    except Exception as e:
        logger.error(f"Error disposing database engine: {str(e)}")
        raise
