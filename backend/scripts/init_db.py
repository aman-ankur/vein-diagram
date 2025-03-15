#!/usr/bin/env python3
"""
Initialize the database for the Vein Diagram application.
This script creates the database and tables if they don't exist.
"""

import os
import sys
import logging

# Add the parent directory to the Python path so we can import the app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import engine, Base
from app.models.pdf_model import PDF, Biomarker
from app.db.init_db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Initialize the database."""
    logger.info("Starting database initialization...")
    
    try:
        # Create directories
        logger.info("Creating necessary directories...")
        os.makedirs("uploads", exist_ok=True)
        
        # Initialize database
        logger.info("Initializing database...")
        init_db()
        
        logger.info("Database initialization completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 