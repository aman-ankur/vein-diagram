#!/usr/bin/env python3
"""
Script to identify and clean up duplicate biomarkers in the database.
Run this script to deduplicate biomarkers that have the same name, value, and unit.
"""
import logging
import sys
import os
from sqlalchemy import func, create_engine
from sqlalchemy.orm import sessionmaker, Session

# Set up the Python path to find the app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("cleanup_duplicates.log")
    ]
)
logger = logging.getLogger(__name__)

def get_db_session():
    """Create a new database session."""
    # Use the SQLite database file path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vein_diagram.db")
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at: {db_path}")
        raise FileNotFoundError(f"Database file not found at: {db_path}")
    
    logger.info(f"Connecting to database at: {db_path}")
    engine = create_engine(f"sqlite:///{db_path}")
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()

def identify_duplicates(db: Session):
    """Identify duplicate biomarkers based on name, value, and unit."""
    logger.info("Identifying duplicate biomarkers...")
    
    # Import inside function to avoid circular imports
    # These imports assume models have been defined correctly
    from app.models.biomarker_model import Biomarker
    
    # List tables to debug
    from sqlalchemy import inspect
    inspector = inspect(db.bind)
    tables = inspector.get_table_names()
    logger.info(f"Tables in database: {tables}")
    
    # Query for biomarkers with the same name, value, and unit
    try:
        duplicate_query = (
            db.query(
                Biomarker.name,
                Biomarker.value,
                Biomarker.unit,
                func.count('*').label('count'),
                func.min(Biomarker.id).label('keep_id')
            )
            .group_by(Biomarker.name, Biomarker.value, Biomarker.unit)
            .having(func.count('*') > 1)
        )
        
        duplicates = duplicate_query.all()
        logger.info(f"Found {len(duplicates)} groups of duplicate biomarkers")
        
        return duplicates
    except Exception as e:
        logger.error(f"Error identifying duplicates: {e}")
        raise

def cleanup_duplicates(db: Session, duplicates):
    """Remove duplicate biomarkers, keeping one of each group."""
    logger.info("Cleaning up duplicate biomarkers...")
    
    # Import inside function to avoid circular imports
    from app.models.biomarker_model import Biomarker
    
    total_removed = 0
    
    for dup in duplicates:
        name, value, unit, count, keep_id = dup
        logger.info(f"Processing duplicate group: {name} ({value} {unit}), count: {count}, keeping ID: {keep_id}")
        
        try:
            # Get all IDs for this combination except the one to keep
            all_ids = db.query(Biomarker.id).filter(
                Biomarker.name == name,
                Biomarker.value == value,
                Biomarker.unit == unit,
                Biomarker.id != keep_id
            ).all()
            
            ids_to_remove = [id[0] for id in all_ids]
            
            if ids_to_remove:
                logger.info(f"Removing {len(ids_to_remove)} duplicates for '{name}' (value: {value} {unit})")
                
                deleted = db.query(Biomarker).filter(Biomarker.id.in_(ids_to_remove)).delete(synchronize_session=False)
                total_removed += deleted
                logger.info(f"Deleted {deleted} duplicate biomarkers")
            else:
                logger.info(f"No duplicate IDs found to remove for {name}")
        except Exception as e:
            logger.error(f"Error processing duplicate '{name}': {e}")
            db.rollback()
            continue
    
    # Commit the changes
    try:
        db.commit()
        logger.info(f"Successfully removed {total_removed} duplicate biomarkers")
    except Exception as e:
        logger.error(f"Error committing changes: {e}")
        db.rollback()
        raise

def main():
    """Main function to run the cleanup."""
    logger.info("Starting duplicate biomarker cleanup")
    
    try:
        # Get database session
        db = get_db_session()
        
        # Check database connection
        from app.models.biomarker_model import Biomarker
        
        try:
            # Get biomarker count before cleanup
            biomarker_count = db.query(Biomarker).count()
            logger.info(f"Total biomarkers before cleanup: {biomarker_count}")
            
            # Identify duplicates
            duplicates = identify_duplicates(db)
            
            if duplicates:
                confirm = input(f"Found {len(duplicates)} groups of duplicate biomarkers. Proceed with cleanup? (y/n): ")
                if confirm.lower() == 'y':
                    cleanup_duplicates(db, duplicates)
                    
                    # Get biomarker count after cleanup
                    biomarker_count_after = db.query(Biomarker).count()
                    logger.info(f"Total biomarkers after cleanup: {biomarker_count_after}")
                    logger.info(f"Removed {biomarker_count - biomarker_count_after} duplicate biomarkers")
                else:
                    logger.info("Cleanup canceled by user")
            else:
                logger.info("No duplicate biomarkers found")
        except Exception as e:
            logger.error(f"Database operation failed: {e}")
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
    
    logger.info("Duplicate biomarker cleanup completed")

if __name__ == "__main__":
    main() 