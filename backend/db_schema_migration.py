import os
import sqlite3
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """
    Run a database schema migration to update the biomarkers table.
    Changes the original_value column from float to string.
    """
    db_file = os.path.join(os.path.dirname(__file__), 'vein_diagram.db')
    
    if not os.path.exists(db_file):
        logger.error(f"Database file not found: {db_file}")
        return False
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        logger.info("Starting migration to update biomarkers table schema...")
        
        # Begin a transaction
        cursor.execute("BEGIN TRANSACTION")
        
        # Create a backup of the biomarkers table
        logger.info("Creating a backup of the biomarkers table...")
        cursor.execute("""
            CREATE TABLE biomarkers_backup AS 
            SELECT * FROM biomarkers
        """)
        
        # Get the existing data as a backup
        cursor.execute("SELECT * FROM biomarkers")
        existing_data = cursor.fetchall()
        
        # Get the column names
        cursor.execute("PRAGMA table_info(biomarkers)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Drop the original table
        logger.info("Dropping the original biomarkers table...")
        cursor.execute("DROP TABLE biomarkers")
        
        # Create a new table with the updated schema
        logger.info("Creating new biomarkers table with string original_value...")
        cursor.execute("""
            CREATE TABLE biomarkers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pdf_id INTEGER REFERENCES pdfs(id),
                name VARCHAR,
                original_name VARCHAR,
                original_value VARCHAR,  -- Changed from FLOAT to VARCHAR
                original_unit VARCHAR,
                value FLOAT,
                unit VARCHAR,
                reference_range_low FLOAT,
                reference_range_high FLOAT,
                reference_range_text VARCHAR,
                category VARCHAR,
                is_abnormal BOOLEAN,
                importance INTEGER DEFAULT 1,
                extracted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validated BOOLEAN DEFAULT 0,
                validated_by VARCHAR,
                validated_date TIMESTAMP,
                notes TEXT
            )
        """)
        
        # Create an index on the name field
        cursor.execute("CREATE INDEX idx_biomarkers_name ON biomarkers(name)")
        
        # Reinsert data from the backup
        if existing_data:
            logger.info(f"Restoring {len(existing_data)} biomarker records...")
            
            # Generate placeholders for the VALUES clause
            placeholders = ",".join(["?" for _ in range(len(column_names))])
            
            insert_sql = f"INSERT INTO biomarkers ({','.join(column_names)}) VALUES ({placeholders})"
            
            # Before inserting, convert all original_value entries to strings
            updated_data = []
            for row in existing_data:
                updated_row = list(row)
                # Find the index of original_value in the columns
                original_value_index = column_names.index('original_value')
                # Convert the original value to string
                if updated_row[original_value_index] is not None:
                    updated_row[original_value_index] = str(updated_row[original_value_index])
                updated_data.append(tuple(updated_row))
            
            cursor.executemany(insert_sql, updated_data)
        
        # Drop the backup table
        logger.info("Dropping the backup table...")
        cursor.execute("DROP TABLE biomarkers_backup")
        
        # Commit the transaction
        conn.commit()
        logger.info("Migration completed successfully")
        
        # Verify the update
        cursor.execute("PRAGMA table_info(biomarkers)")
        updated_columns = cursor.fetchall()
        for col in updated_columns:
            if col[1] == 'original_value':
                logger.info(f"original_value column type: {col[2]}")
        
        return True
    except Exception as e:
        # Rollback on error
        conn.rollback()
        logger.error(f"Migration failed: {str(e)}")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("Migration completed successfully")
    else:
        print("Migration failed, see logs for details") 