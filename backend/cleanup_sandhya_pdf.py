#!/usr/bin/env python3
"""
Cleanup script to remove sandhya_13_05.pdf and associated data from database
"""

import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal
from app.models.pdf_model import PDF
from app.models.biomarker_model import Biomarker
from app.models.profile_model import Profile  # Import Profile to resolve relationship

def cleanup_sandhya_pdf():
    """Clean up sandhya PDF and associated biomarkers from database"""
    db = SessionLocal()
    try:
        # Find the sandhya PDF
        pdf = db.query(PDF).filter(PDF.filename.like('%sandhya_13_05%')).first()
        if pdf:
            print(f'Found PDF: ID={pdf.id}, filename={pdf.filename}, status={pdf.status}')
            
            # Count associated biomarkers
            biomarker_count = db.query(Biomarker).filter(Biomarker.pdf_id == pdf.id).count()
            print(f'Associated biomarkers: {biomarker_count}')
            
            # Delete biomarkers first (cascade should handle this, but let's be explicit)
            if biomarker_count > 0:
                deleted_biomarkers = db.query(Biomarker).filter(Biomarker.pdf_id == pdf.id).delete()
                print(f'Deleted {deleted_biomarkers} biomarkers')
            
            # Delete the PDF
            db.delete(pdf)
            db.commit()
            print(f'✅ Successfully deleted PDF and associated data')
        else:
            print('❌ No sandhya_13_05.pdf found in database')
            
        # Show remaining PDFs
        remaining_pdfs = db.query(PDF).all()
        print(f'\\nRemaining PDFs in database: {len(remaining_pdfs)}')
        for p in remaining_pdfs:
            biomarker_count = db.query(Biomarker).filter(Biomarker.pdf_id == p.id).count()
            print(f'  - ID={p.id}, filename={p.filename}, biomarkers={biomarker_count}')
            
    except Exception as e:
        print(f'Error: {e}')
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_sandhya_pdf() 