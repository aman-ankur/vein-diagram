#!/usr/bin/env python3
"""
Migration script to add profiles feature to the database.
This script:
1. Creates a new profiles table
2. Adds profile_id fields to biomarkers and pdfs tables (or creates them if they don't exist)
3. Creates foreign key relationships
"""
import os
import sys
import sqlite3
import uuid
import logging
from datetime import datetime
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
DATABASE_URL = os.environ.get("DATABASE_URL", DEFAULT_DB_PATH)

if DATABASE_URL.startswith("sqlite:///"):
    DATABASE_URL = DATABASE_URL[10:]

logger.info(f"Using database at path: {DATABASE_URL}")

def table_exists(cursor, table_name):
    """Check if a table exists in the database."""
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
    return cursor.fetchone() is not None

def create_biomarkers_table(cursor):
    """Create the biomarkers table with profile_id column."""
    logger.info("Creating biomarkers table...")
    cursor.execute("""
    CREATE TABLE biomarkers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pdf_id INTEGER,
        profile_id TEXT,
        name TEXT,
        original_name TEXT,
        original_value TEXT,
        original_unit TEXT,
        value REAL,
        unit TEXT,
        reference_range_low REAL,
        reference_range_high REAL,
        reference_range_text TEXT,
        category TEXT,
        is_abnormal BOOLEAN,
        importance INTEGER DEFAULT 1,
        extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        validated BOOLEAN DEFAULT 0,
        validated_by TEXT,
        validated_date TIMESTAMP,
        notes TEXT
    )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_biomarkers_name ON biomarkers(name)")
    cursor.execute("CREATE INDEX idx_biomarkers_pdf_id ON biomarkers(pdf_id)")
    cursor.execute("CREATE INDEX idx_biomarkers_profile_id ON biomarkers(profile_id)")
    logger.info("Biomarkers table created successfully.")

def create_pdfs_table(cursor):
    """Create the pdfs table with profile_id column."""
    logger.info("Creating pdfs table...")
    cursor.execute("""
    CREATE TABLE pdfs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT UNIQUE,
        filename TEXT,
        file_path TEXT,
        upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_date TIMESTAMP,
        report_date TIMESTAMP,
        extracted_text TEXT,
        status TEXT DEFAULT 'pending',
        error_message TEXT,
        profile_id TEXT,
        lab_name TEXT,
        patient_name TEXT,
        patient_id TEXT,
        patient_age INTEGER,
        patient_gender TEXT,
        processing_details TEXT,
        parsing_confidence REAL
    )
    """)
    
    # Create indexes
    cursor.execute("CREATE INDEX idx_pdfs_file_id ON pdfs(file_id)")
    cursor.execute("CREATE INDEX idx_pdfs_profile_id ON pdfs(profile_id)")
    logger.info("PDFs table created successfully.")

def main():
    """Execute migration to add profiles functionality."""
    logger.info(f"Starting migration on database: {DATABASE_URL}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DATABASE_URL)
        cursor = conn.cursor()
        
        # Enable foreign keys in SQLite
        cursor.execute("PRAGMA foreign_keys = ON")
        
        # Check if profiles table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='profiles'")
        profile_exists = cursor.fetchone() is not None
        
        if not profile_exists:
            logger.info("Creating profiles table...")
            
            # Create profiles table
            cursor.execute("""
            CREATE TABLE profiles (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                date_of_birth TIMESTAMP,
                gender TEXT,
                patient_id TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_modified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """)
            
            # Create indexes for profiles table
            cursor.execute("CREATE INDEX idx_profiles_name ON profiles(name)")
            cursor.execute("CREATE INDEX idx_profiles_patient_id ON profiles(patient_id)")
            
            logger.info("Profiles table created successfully.")
        else:
            logger.info("Profiles table already exists. Skipping creation.")
        
        # Check if biomarkers table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='biomarkers'")
        biomarkers_exist = cursor.fetchone() is not None
        
        if not biomarkers_exist:
            logger.info("Creating biomarkers table...")
            # Create biomarkers table with profile_id column
            cursor.execute("""
            CREATE TABLE biomarkers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_id INTEGER,
                profile_id TEXT,
                name TEXT,
                original_name TEXT,
                original_value TEXT,
                original_unit TEXT,
                value REAL,
                unit TEXT,
                reference_range_low REAL,
                reference_range_high REAL,
                reference_range_text TEXT,
                category TEXT,
                is_abnormal BOOLEAN,
                importance INTEGER DEFAULT 1,
                extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated BOOLEAN DEFAULT 0,
                validated_by TEXT,
                validated_date TIMESTAMP,
                notes TEXT
            )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX idx_biomarkers_name ON biomarkers(name)")
            cursor.execute("CREATE INDEX idx_biomarkers_pdf_id ON biomarkers(pdf_id)")
            cursor.execute("CREATE INDEX idx_biomarkers_profile_id ON biomarkers(profile_id)")
            logger.info("Biomarkers table created successfully.")
        else:
            # Check if biomarkers table has profile_id column
            cursor.execute("PRAGMA table_info(biomarkers)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if "profile_id" not in columns:
                logger.info("Adding profile_id column to biomarkers table...")
                
                # Add profile_id column to biomarkers table
                cursor.execute("ALTER TABLE biomarkers ADD COLUMN profile_id TEXT")
                
                # Create index for profile_id
                cursor.execute("CREATE INDEX idx_biomarkers_profile_id ON biomarkers(profile_id)")
                
                logger.info("Added profile_id column to biomarkers table.")
            else:
                logger.info("profile_id column already exists in biomarkers table. Skipping.")
        
        # Check if pdfs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pdfs'")
        pdfs_exist = cursor.fetchone() is not None
        
        if not pdfs_exist:
            logger.info("Creating pdfs table...")
            # Create pdfs table with profile_id column
            cursor.execute("""
            CREATE TABLE pdfs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT UNIQUE,
                filename TEXT,
                file_path TEXT,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_date TIMESTAMP,
                report_date TIMESTAMP,
                extracted_text TEXT,
                status TEXT DEFAULT 'pending',
                error_message TEXT,
                profile_id TEXT,
                lab_name TEXT,
                patient_name TEXT,
                patient_id TEXT,
                patient_age INTEGER,
                patient_gender TEXT,
                processing_details TEXT,
                parsing_confidence REAL
            )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX idx_pdfs_file_id ON pdfs(file_id)")
            cursor.execute("CREATE INDEX idx_pdfs_profile_id ON pdfs(profile_id)")
            logger.info("PDFs table created successfully.")
        else:
            # Check if pdfs table has profile_id column
            cursor.execute("PRAGMA table_info(pdfs)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if "profile_id" not in columns:
                logger.info("Adding profile_id column to pdfs table...")
                
                # Add profile_id column to pdfs table
                cursor.execute("ALTER TABLE pdfs ADD COLUMN profile_id TEXT")
                
                # Create index for profile_id
                cursor.execute("CREATE INDEX idx_pdfs_profile_id ON pdfs(profile_id)")
                
                logger.info("Added profile_id column to pdfs table.")
            else:
                logger.info("profile_id column already exists in pdfs table. Skipping.")
        
        # Create a default profile for existing data if there are existing biomarkers
        if biomarkers_exist:
            cursor.execute("SELECT COUNT(*) FROM biomarkers")
            biomarker_count = cursor.fetchone()[0]
            
            if biomarker_count > 0:
                logger.info("Creating a default profile for existing biomarkers...")
                
                # Generate a UUID for the default profile
                default_profile_id = str(uuid.uuid4())
                
                # Create a default profile
                cursor.execute("""
                INSERT INTO profiles (id, name, created_at, last_modified)
                VALUES (?, ?, ?, ?)
                """, (default_profile_id, "Default Profile", datetime.now(), datetime.now()))
                
                # Update all biomarkers to belong to the default profile
                cursor.execute("""
                UPDATE biomarkers SET profile_id = ? WHERE profile_id IS NULL
                """, (default_profile_id,))
                
                if pdfs_exist:
                    # Update all PDFs to belong to the default profile
                    cursor.execute("""
                    UPDATE pdfs SET profile_id = ? WHERE profile_id IS NULL
                    """, (default_profile_id,))
                
                logger.info(f"Created default profile with ID {default_profile_id} and assigned it to existing data.")
            else:
                logger.info("No existing biomarkers found. Skipping default profile creation.")
        
        # Commit the changes
        conn.commit()
        logger.info("Migration completed successfully.")
    
    except Exception as e:
        # Roll back any changes if something goes wrong
        conn.rollback()
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)
    
    finally:
        # Close the database connection
        conn.close()

if __name__ == "__main__":
    main() 