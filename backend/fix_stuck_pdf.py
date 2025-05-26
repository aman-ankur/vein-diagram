#!/usr/bin/env python3
"""
Script to fix stuck PDFs that are in 'processing' status
"""

import sys
import os
import sqlite3
from datetime import datetime

def fix_stuck_pdfs():
    """Fix PDFs that are stuck in processing status"""
    
    # Connect to the database
    db_path = "vein_diagram.db"
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Find PDFs stuck in processing status
        cursor.execute("SELECT id, file_id, filename, upload_date FROM pdfs WHERE status = 'processing'")
        stuck_pdfs = cursor.fetchall()
        
        if not stuck_pdfs:
            print("✅ No stuck PDFs found")
            return
        
        print(f"Found {len(stuck_pdfs)} stuck PDFs:")
        for pdf_id, file_id, filename, upload_date in stuck_pdfs:
            print(f"  - ID: {pdf_id}, File: {filename}, Upload: {upload_date}")
        
        # Ask for confirmation
        response = input("\nReset these PDFs to 'pending' status? (y/N): ")
        if response.lower() != 'y':
            print("Operation cancelled")
            return
        
        # Reset status to pending and clear error messages
        cursor.execute("""
            UPDATE pdfs 
            SET status = 'pending', 
                error_message = NULL, 
                processed_date = NULL 
            WHERE status = 'processing'
        """)
        
        affected_rows = cursor.rowcount
        conn.commit()
        
        print(f"✅ Reset {affected_rows} PDFs to pending status")
        print("You can now restart the server and the PDFs will be reprocessed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_stuck_pdfs() 