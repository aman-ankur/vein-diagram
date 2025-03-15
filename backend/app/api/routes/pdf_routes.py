from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from typing import List
import os
import uuid
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.services.pdf_service import extract_text_from_pdf, parse_biomarkers_from_text, process_pdf_background
from app.schemas.pdf_schema import PDFResponse, PDFStatusResponse, PDFListResponse
from app.models.pdf_model import PDF as PDFModel
from app.db.database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create upload directory
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter()

def validate_pdf(file: UploadFile) -> None:
    """
    Validate PDF file.
    
    Args:
        file: The file to validate
        
    Raises:
        HTTPException: If validation fails
    """
    # Check if file is a PDF
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Check file size (30MB max)
    file_size = 0
    
    # Try to get the file size
    try:
        # This is a bit of a hack, but it works for FastAPI's UploadFile
        # We can't just check the length of the file content because it's a streaming file
        file_content = file.file.read()
        file_size = len(file_content)
        file.file.seek(0)  # Reset file position
    except Exception as e:
        logger.error(f"Error checking file size: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not check file size")
    
    # 30MB in bytes
    max_size = 30 * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(status_code=400, detail=f"File size exceeds the maximum limit of 30MB. Current size: {file_size / (1024 * 1024):.2f}MB")

@router.post("/upload", response_model=PDFResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a PDF file for processing.
    
    Args:
        background_tasks: FastAPI BackgroundTasks for background processing
        file: The PDF file to upload
        db: Database session
        
    Returns:
        PDFResponse: The response containing the file ID and status
    """
    try:
        # Validate file
        validate_pdf(file)
        
        # Generate a unique ID for the file
        file_id = str(uuid.uuid4())
        
        # Save the file
        file_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Create a database record
        pdf_record = PDFModel(
            file_id=file_id,
            filename=file.filename,
            upload_date=datetime.utcnow(),
            status="pending",
            file_path=file_path
        )
        
        db.add(pdf_record)
        db.commit()
        db.refresh(pdf_record)
        
        # Process the PDF in the background
        background_tasks.add_task(process_pdf_background, file_path, file_id, db)
        
        logger.info(f"Successfully uploaded PDF: {file.filename} (ID: {file_id})")
        
        return PDFResponse(
            file_id=file_id,
            filename=file.filename,
            status="pending",
            message="File uploaded successfully and is being processed"
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        
        # Clean up any saved file
        if 'file_path' in locals() and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Cleaned up file after error: {file_path}")
            except Exception as cleanup_error:
                logger.error(f"Error cleaning up file: {str(cleanup_error)}")
                
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@router.get("/status/{file_id}", response_model=PDFStatusResponse)
async def get_pdf_status(file_id: str, db: Session = Depends(get_db)):
    """
    Get the processing status of a PDF file.
    
    Args:
        file_id: The ID of the file to check
        db: Database session
        
    Returns:
        PDFStatusResponse: The status of the file processing
    """
    pdf = db.query(PDFModel).filter(PDFModel.file_id == file_id).first()
    
    if not pdf:
        raise HTTPException(status_code=404, detail="File not found")
    
    return PDFStatusResponse(
        file_id=pdf.file_id,
        filename=pdf.filename,
        status=pdf.status,
        upload_date=pdf.upload_date,
        processed_date=pdf.processed_date,
        error_message=pdf.error_message if pdf.status == "error" else None
    ) 