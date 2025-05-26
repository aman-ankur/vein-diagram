#!/usr/bin/env python3
"""
Migration to add processing_started_at column to pdfs table
"""

import sys
import os
import sqlite3
from datetime import datetime

def migrate_sqlite():
    """Add processing_started_at column to SQLite database"""
    db_path = "vein_diagram.db"
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(pdfs)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'processing_started_at' in columns:
            print("✅ Column 'processing_started_at' already exists")
            return True
        
        # Add the new column
        cursor.execute("""
            ALTER TABLE pdfs 
            ADD COLUMN processing_started_at DATETIME
        """)
        
        conn.commit()
        print("✅ Successfully added 'processing_started_at' column to pdfs table")
        return True
        
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def migrate_postgresql():
    """Add processing_started_at column to PostgreSQL database"""
    try:
        from sqlalchemy import create_engine, text
        import os
        
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("❌ DATABASE_URL not found")
            return False
        
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'pdfs' AND column_name = 'processing_started_at'
            """))
            
            if result.fetchone():
                print("✅ Column 'processing_started_at' already exists")
                return True
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE pdfs 
                ADD COLUMN processing_started_at TIMESTAMP
            """))
            
            conn.commit()
            print("✅ Successfully added 'processing_started_at' column to pdfs table")
            return True
            
    except Exception as e:
        print(f"❌ Error adding column: {e}")
        return False

def main():
    """Run the migration"""
    print("🔄 Adding processing_started_at column to pdfs table...")
    
    # Check if we're using SQLite or PostgreSQL
    database_url = os.getenv("DATABASE_URL", "sqlite:///./vein_diagram.db")
    
    if database_url.startswith("sqlite"):
        success = migrate_sqlite()
    else:
        success = migrate_postgresql()
    
    if success:
        print("✅ Migration completed successfully")
        return 0
    else:
        print("❌ Migration failed")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 