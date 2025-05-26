#!/usr/bin/env python3
"""
Startup Recovery Service for PDF Processing

This service detects and fixes inconsistent PDF processing states that can occur
due to server restarts, crashes, or other interruptions during processing.
"""

import logging
from datetime import datetime
from typing import List, Tuple
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.pdf_model import PDF
from app.models.biomarker_model import Biomarker
from app.models.profile_model import Profile  # Import Profile to resolve relationship

# Configure logging
logger = logging.getLogger(__name__)

def detect_inconsistent_pdfs(db: Session) -> List[Tuple[PDF, int]]:
    """
    Detect PDFs with inconsistent status (pending/processing but have biomarkers).
    
    Args:
        db: Database session
        
    Returns:
        List of tuples (PDF, biomarker_count) for inconsistent PDFs
    """
    inconsistent_pdfs = []
    
    # Find PDFs that are stuck in pending/processing status
    stuck_pdfs = db.query(PDF).filter(
        PDF.status.in_(["pending", "processing"])
    ).all()
    
    logger.info(f"🔍 Checking {len(stuck_pdfs)} PDFs with pending/processing status")
    
    for pdf in stuck_pdfs:
        # Count biomarkers for this PDF
        biomarker_count = db.query(Biomarker).filter(
            Biomarker.pdf_id == pdf.id
        ).count()
        
        if biomarker_count > 0:
            # This PDF has biomarkers but wrong status - it's inconsistent
            inconsistent_pdfs.append((pdf, biomarker_count))
            logger.warning(
                f"📋 Found inconsistent PDF: {pdf.filename} (ID: {pdf.id}) "
                f"has {biomarker_count} biomarkers but status is '{pdf.status}'"
            )
    
    return inconsistent_pdfs

def fix_inconsistent_pdf(db: Session, pdf: PDF, biomarker_count: int) -> bool:
    """
    Fix a single inconsistent PDF by updating its status and metadata.
    
    Args:
        db: Database session
        pdf: The PDF to fix
        biomarker_count: Number of biomarkers found for this PDF
        
    Returns:
        bool: True if successfully fixed, False otherwise
    """
    try:
        # Update status to processed
        pdf.status = "processed"
        
        # Set processed_date if missing
        if not pdf.processed_date:
            pdf.processed_date = datetime.utcnow()
        
        # Calculate parsing confidence if missing
        if not pdf.parsing_confidence and biomarker_count > 0:
            # Simple confidence calculation: base 50% + 5% per biomarker, max 95%
            pdf.parsing_confidence = min(0.95, 0.5 + (biomarker_count * 0.05))
        
        # Commit the changes
        db.commit()
        db.refresh(pdf)
        
        logger.info(
            f"✅ Fixed PDF: {pdf.filename} (ID: {pdf.id}) "
            f"→ status: 'processed', biomarkers: {biomarker_count}, "
            f"confidence: {pdf.parsing_confidence:.2f}"
        )
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to fix PDF {pdf.id}: {str(e)}")
        db.rollback()
        return False

def run_startup_recovery() -> dict:
    """
    Run the complete startup recovery process.
    
    Returns:
        dict: Summary of recovery results
    """
    logger.info("🚀 Starting PDF status recovery process...")
    
    db = SessionLocal()
    results = {
        "total_checked": 0,
        "inconsistent_found": 0,
        "successfully_fixed": 0,
        "failed_to_fix": 0,
        "fixed_pdfs": []
    }
    
    try:
        # Detect inconsistent PDFs
        inconsistent_pdfs = detect_inconsistent_pdfs(db)
        results["inconsistent_found"] = len(inconsistent_pdfs)
        
        if not inconsistent_pdfs:
            logger.info("✨ No inconsistent PDFs found - all good!")
            return results
        
        logger.info(f"🔧 Found {len(inconsistent_pdfs)} inconsistent PDFs to fix")
        
        # Fix each inconsistent PDF
        for pdf, biomarker_count in inconsistent_pdfs:
            if fix_inconsistent_pdf(db, pdf, biomarker_count):
                results["successfully_fixed"] += 1
                results["fixed_pdfs"].append({
                    "id": pdf.id,
                    "filename": pdf.filename,
                    "biomarker_count": biomarker_count
                })
            else:
                results["failed_to_fix"] += 1
        
        # Log summary
        logger.info(
            f"📊 Recovery Summary: "
            f"Found {results['inconsistent_found']} inconsistent PDFs, "
            f"Fixed {results['successfully_fixed']}, "
            f"Failed {results['failed_to_fix']}"
        )
        
        if results["successfully_fixed"] > 0:
            logger.info("🎉 Startup recovery completed successfully!")
        
    except Exception as e:
        logger.error(f"💥 Startup recovery failed: {str(e)}")
        results["error"] = str(e)
        
    finally:
        db.close()
    
    return results

def check_processing_health() -> dict:
    """
    Check the overall health of PDF processing without making changes.
    
    Returns:
        dict: Health check results
    """
    db = SessionLocal()
    health = {
        "total_pdfs": 0,
        "pending": 0,
        "processing": 0,
        "processed": 0,
        "error": 0,
        "inconsistent": 0
    }
    
    try:
        # Count PDFs by status
        all_pdfs = db.query(PDF).all()
        health["total_pdfs"] = len(all_pdfs)
        
        for pdf in all_pdfs:
            health[pdf.status] = health.get(pdf.status, 0) + 1
        
        # Check for inconsistencies
        inconsistent_pdfs = detect_inconsistent_pdfs(db)
        health["inconsistent"] = len(inconsistent_pdfs)
        
        logger.info(f"📈 PDF Processing Health: {health}")
        
    except Exception as e:
        logger.error(f"❌ Health check failed: {str(e)}")
        health["error_message"] = str(e)
        
    finally:
        db.close()
    
    return health

if __name__ == "__main__":
    # Allow running this script directly for testing
    logging.basicConfig(level=logging.INFO)
    results = run_startup_recovery()
    print(f"Recovery results: {results}") 