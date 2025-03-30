#!/usr/bin/env python3
"""
Migration script to add the 'date_of_birth' column to the 'pdfs' table.
"""
import os
import sys
import sqlite3
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get database path from environment or use default
script_dir = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(script_dir, "vein_diagram.db")
DATABASE_URL  = 'vein_diagram.db'


if DATABASE_URL.startswith("sqlite:////"):
    DATABASE_URL = DATABASE_URL[10:]

logger.info(f"Using database at path: {DATABASE_URL}")

def column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return column_name in columns

def main():
    """Execute migration to add date_of_birth column to pdfs table."""
    logger.info(f"Starting migration on database: {DATABASE_URL}")
    conn = None # Initialize conn to None
    try:
        # Connect to the database
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Check if pdfs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdfs'")
        pdfs_exist = cursor.fetchone() is not None
        
        if not pdfs_exist:
            logger.warning("'pdfs' table does not exist. Cannot add column. Run previous migrations first.")
            return

        # Check if 'date_of_birth' column already exists in pdfs table
        if not column_exists(cursor, "pdfs", "date_of_birth"):
            logger.info("Adding 'date_of_birth' column to pdfs table...")
            
            # Add date_of_birth column (DATETIME allows NULL by default in SQLite)
            cursor.execute("ALTER TABLE pdfs ADD COLUMN date_of_birth DATETIME")
            
            logger.info("'date_of_birth' column added successfully to pdfs table.")
        else:
            logger.info("'date_of_birth' column already exists in pdfs table. Skipping.")

        # Commit the changes
        conn.commit()
        logger.info("Migration completed successfully.")
        
    except sqlite3.Error as e:
        logger.error(f"Database error during migration: {e}")
        if conn:
            conn.rollback() # Rollback changes on error
        sys.exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        if conn:
            conn.rollback()
        sys.exit(1)
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed.")

if __name__ == "__main__":
    main() 