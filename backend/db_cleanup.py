#!/usr/bin/env python3
"""
Database cleanup script.
This script creates a backup of the database and then deletes all files, biomarkers,
extraction, and storage data to start fresh.
"""

import os
import sys
import shutil
import logging
import sqlite3
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("db_cleanup")

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import models
from app.db.database import Base
from app.models.pdf_model import PDF
from app.models.biomarker_model import Biomarker
from app.db.session import engine, get_db

# Database file location - update the path to the actual location
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vein_diagram.db")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db_backups")

def create_backup():
    """
    Create a backup of the database before deletion.
    
    Returns:
        str: Path to the backup file
    """
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}")
        return None
        
    # Create backup directory if it doesn't exist
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        logger.info(f"Created backup directory at {BACKUP_DIR}")
    
    # Generate backup filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"app_backup_{timestamp}.db"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        # Copy the database file to backup location
        shutil.copy2(DB_PATH, backup_path)
        logger.info(f"Database backup created at {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create database backup: {str(e)}")
        return None

def delete_all_data():
    """
    Delete all data from the PDFs and biomarkers tables.
    
    Returns:
        tuple: (bool success, str message)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get record counts before deletion
        cursor.execute("SELECT COUNT(*) FROM biomarkers")
        biomarker_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pdfs")
        pdf_count = cursor.fetchone()[0]
        
        logger.info(f"Found {biomarker_count} biomarkers and {pdf_count} PDFs to delete")
        
        # Delete all records from biomarkers table (child table first due to foreign key constraints)
        cursor.execute("DELETE FROM biomarkers")
        
        # Delete all records from pdfs table
        cursor.execute("DELETE FROM pdfs")
        
        # Commit the changes
        conn.commit()
        
        # Check if deletion was successful
        cursor.execute("SELECT COUNT(*) FROM biomarkers")
        new_biomarker_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pdfs")
        new_pdf_count = cursor.fetchone()[0]
        
        logger.info(f"After deletion: {new_biomarker_count} biomarkers and {new_pdf_count} PDFs remaining")
        
        conn.close()
        return True, f"Successfully deleted {biomarker_count} biomarkers and {pdf_count} PDFs"
    except Exception as e:
        logger.error(f"Error deleting data: {str(e)}")
        return False, f"Failed to delete data: {str(e)}"

def main():
    """
    Main function to backup and delete all data.
    """
    logger.info("Starting database cleanup process")
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        logger.error(f"Database file not found at {DB_PATH}")
        return
    
    # Confirm with user before proceeding
    confirm = input(f"This will DELETE ALL DATA from the database at {DB_PATH}. A backup will be created first. Continue? (y/n): ")
    
    if confirm.lower() != 'y':
        logger.info("Operation cancelled by user")
        return
    
    # Create backup
    backup_path = create_backup()
    if not backup_path:
        logger.error("Backup failed, aborting deletion")
        return
    
    # Delete data
    success, message = delete_all_data()
    if success:
        logger.info(message)
        logger.info(f"Database cleanup completed successfully. Backup available at {backup_path}")
    else:
        logger.error(message)
        logger.error("Database cleanup failed")

if __name__ == "__main__":
    main() 