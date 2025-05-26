"""
Startup Recovery Service

Handles recovery of stuck processes when the server restarts.
"""

import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.pdf_model import PDF
from app.services.pdf_service import process_pdf_background
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

def recover_stuck_pdfs():
    """
    Recover PDFs that were stuck in processing when the server was restarted.
    This should be called during server startup.
    """
    db = SessionLocal()
    try:
        # Find PDFs that have been in "processing" status for more than 10 minutes
        # This indicates they were likely interrupted by a server restart
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        
        stuck_pdfs = db.query(PDF).filter(
            PDF.status == "processing",
            # Use processing_started_at if available, otherwise fall back to upload_date
            (PDF.processing_started_at < cutoff_time) | 
            ((PDF.processing_started_at.is_(None)) & (PDF.upload_date < cutoff_time))
        ).all()
        
        if not stuck_pdfs:
            logger.info("✅ No stuck PDFs found during startup recovery")
            return
        
        logger.info(f"🔄 Found {len(stuck_pdfs)} stuck PDFs during startup recovery")
        
        for pdf in stuck_pdfs:
            logger.info(f"🔄 Resetting PDF {pdf.id} ({pdf.filename}) from processing to pending")
            
            # Reset status to pending so it can be reprocessed
            pdf.status = "pending"
            pdf.error_message = None
            pdf.processed_date = None
            pdf.processing_started_at = None  # Clear the processing start time
            
        db.commit()
        logger.info(f"✅ Reset {len(stuck_pdfs)} PDFs to pending status")
        
    except Exception as e:
        logger.error(f"❌ Error during startup recovery: {str(e)}")
        db.rollback()
    finally:
        db.close()

def requeue_pending_pdfs(background_tasks: BackgroundTasks):
    """
    Requeue any pending PDFs for processing.
    This should be called after startup recovery.
    """
    db = SessionLocal()
    try:
        # Find all pending PDFs
        pending_pdfs = db.query(PDF).filter(PDF.status == "pending").all()
        
        if not pending_pdfs:
            logger.info("✅ No pending PDFs found to requeue")
            return
        
        logger.info(f"🔄 Requeuing {len(pending_pdfs)} pending PDFs for processing")
        
        for pdf in pending_pdfs:
            logger.info(f"🔄 Requeuing PDF {pdf.id} ({pdf.filename}) for background processing")
            
            # Add to background tasks for processing
            background_tasks.add_task(process_pdf_background, pdf_id=pdf.id)
            
        logger.info(f"✅ Requeued {len(pending_pdfs)} PDFs for processing")
        
    except Exception as e:
        logger.error(f"❌ Error during PDF requeuing: {str(e)}")
    finally:
        db.close()

def startup_recovery(background_tasks: BackgroundTasks = None):
    """
    Complete startup recovery process.
    
    Args:
        background_tasks: Optional BackgroundTasks instance for requeuing
    """
    logger.info("🚀 Starting PDF processing recovery...")
    
    # Step 1: Recover stuck PDFs
    recover_stuck_pdfs()
    
    # Step 2: Requeue pending PDFs if background_tasks is provided
    if background_tasks:
        requeue_pending_pdfs(background_tasks)
    
    logger.info("✅ PDF processing recovery completed") 