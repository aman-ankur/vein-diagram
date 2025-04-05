import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
from datetime import datetime
import json

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.profile_model import Profile
from app.models.pdf_model import PDF
from app.models.biomarker_model import Biomarker, BiomarkerDictionary
from app.db.database import Base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_sqlite_engine():
    """Create SQLite engine."""
    sqlite_url = "sqlite:///vein_diagram.db"
    return create_engine(sqlite_url)

def get_postgres_engine():
    """Create PostgreSQL engine."""
    postgres_url = os.getenv("DATABASE_URL")
    if not postgres_url:
        raise ValueError("DATABASE_URL environment variable not set")
    return create_engine(postgres_url)

def copy_table_data(source_session, dest_session, model):
    """Copy data from one table to another."""
    table_name = model.__tablename__
    logger.info(f"Copying data for table: {table_name}")
    
    # Get all records from source
    records = source_session.query(model).all()
    logger.info(f"Found {len(records)} records in {table_name}")
    
    # Insert into destination
    for record in records:
        # Create a new instance of the model
        new_record = model()
        
        # Copy all attributes
        for column in model.__table__.columns:
            value = getattr(record, column.name)
            setattr(new_record, column.name, value)
        
        dest_session.add(new_record)
    
    try:
        dest_session.commit()
        logger.info(f"Successfully copied {len(records)} records to {table_name}")
    except Exception as e:
        dest_session.rollback()
        logger.error(f"Error copying data for {table_name}: {str(e)}")
        raise

def migrate_data():
    """Main migration function."""
    try:
        # Create engines
        sqlite_engine = get_sqlite_engine()
        postgres_engine = get_postgres_engine()
        
        # Create sessions
        SQLiteSession = sessionmaker(bind=sqlite_engine)
        PostgresSession = sessionmaker(bind=postgres_engine)
        
        sqlite_session = SQLiteSession()
        postgres_session = PostgresSession()
        
        # Create all tables in PostgreSQL
        Base.metadata.create_all(postgres_engine)
        
        # Migrate data table by table in the correct order
        try:
            # 1. Profiles (no foreign key dependencies)
            copy_table_data(sqlite_session, postgres_session, Profile)
            
            # 2. PDFs (depends on profiles)
            copy_table_data(sqlite_session, postgres_session, PDF)
            
            # 3. Biomarker Dictionary
            copy_table_data(sqlite_session, postgres_session, BiomarkerDictionary)
            
            # 4. Biomarkers (depends on pdfs and profiles)
            copy_table_data(sqlite_session, postgres_session, Biomarker)
            
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            raise
        
        finally:
            sqlite_session.close()
            postgres_session.close()
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting migration...")
    migrate_data()
    logger.info("Migration process completed.") 