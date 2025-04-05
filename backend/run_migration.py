#!/usr/bin/env python3
"""
Script to run the new migration to fix the pdfs sequence issue.
"""
import os
import subprocess
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Run the migration to fix the pdfs sequence"""
    try:
        logger.info("Running database migration to fix pdfs sequence...")
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Run the migration command
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=current_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        logger.info(f"Migration output:\n{result.stdout}")
        
        if result.stderr:
            logger.warning(f"Migration warnings:\n{result.stderr}")
            
        logger.info("Migration completed successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed with exit code {e.returncode}")
        logger.error(f"Error output:\n{e.stderr}")
        raise
    except Exception as e:
        logger.error(f"Error running migration: {str(e)}")
        raise

if __name__ == "__main__":
    run_migration() 