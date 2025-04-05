from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from typing import List, Optional
import os
import uuid
import logging
from sqlalchemy.orm import Session
from datetime import datetime
import hashlib

from app.services.pdf_service import extract_text_from_pdf, parse_biomarkers_from_text, process_pdf_background
from app.services.metadata_parser import extract_metadata_with_claude
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

def compute_file_hash(file_content):
    """
    Compute a hash of the file content to identify duplicate uploads.
    
    Args:
        file_content: The binary content of the file
        
    Returns:
        str: Hash of the file content
    """
    return hashlib.sha256(file_content).hexdigest()

@router.post("/upload", response_model=PDFResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    profile_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db)
):
    """
    Upload a PDF file for processing.
    
    Note: Only the first 3 pages of the PDF will be processed, regardless of the total number of pages.
    This is to maintain performance and focus on the most relevant content, which is typically in the
    first few pages of a lab report.
    
    Args:
        background_tasks: FastAPI BackgroundTasks for async processing
        file: The PDF file to upload
        profile_id: Optional UUID of profile to associate with this PDF
        db: Database session
        
    Returns:
        PDFResponse with file ID and status
    """
    try:
        # Validate the file
        validate_pdf(file)
        
        # Read file content
        file_content = await file.read()
        
        # Compute file hash to prevent duplicates
        file_hash = compute_file_hash(file_content)
        
        # Check if this file has already been uploaded
        existing_pdf = db.query(PDFModel).filter(PDFModel.file_id == file_hash).first()
        if existing_pdf:
            if profile_id and existing_pdf.profile_id != profile_id:
                # Update the profile_id if a new one is provided
                existing_pdf.profile_id = profile_id
                db.commit()
                db.refresh(existing_pdf)
                
            return PDFResponse(
                file_id=existing_pdf.file_id,
                filename=existing_pdf.filename,
                upload_date=existing_pdf.upload_date,
                status=existing_pdf.status,
                profile_id=existing_pdf.profile_id,
                # Add extracted metadata details
                patient_name=existing_pdf.patient_name,
                patient_gender=existing_pdf.patient_gender,
                patient_id=existing_pdf.patient_id,
                lab_name=existing_pdf.lab_name,
                report_date=existing_pdf.report_date
            )
        
        # Save file with unique name
        unique_filename = f"{uuid.uuid4()}-{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create PDF record in database
        pdf = PDFModel(
            file_id=file_hash,
            filename=file.filename,
            file_path=file_path,
            status="pending",
            profile_id=profile_id
        )
        db.add(pdf)
        db.commit()
        db.refresh(pdf)
        
        # Start background processing
        background_tasks.add_task(
            process_pdf_background,
            pdf_id=pdf.id
            # db_session=db # Removed: Background task should create its own session
        )

        return PDFResponse(
            file_id=pdf.file_id,
            filename=pdf.filename,
            upload_date=pdf.upload_date,
            status=pdf.status,
            profile_id=pdf.profile_id,
            # Metadata fields will be null at this point
            patient_name=None,
            patient_gender=None,
            patient_id=None,
            lab_name=None,
            report_date=None
        )
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error uploading PDF: {str(e)}")

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
    try:
        # Log the request
        logger.info(f"Checking status for PDF with file_id: {file_id}")
        
        # Try to find the PDF in the database
        pdf = db.query(PDFModel).filter(PDFModel.file_id == file_id).first()
        
        if not pdf:
            logger.warning(f"PDF with file_id {file_id} not found in database")
            
            # Check if this was a recent upload that might not be in the database yet
            if file_id and len(file_id) > 10:  # Basic validation that it's a reasonable ID
                return PDFStatusResponse(
                    file_id=file_id,
                    filename="Unknown",
                    status="not_found",
                    upload_date=None,
                    processed_date=None,
                    error_message="PDF not found in database. It may have been deleted or not yet uploaded.",
                    profile_id=None,
                    lab_name=None,
                    patient_name=None,
                    patient_id=None,
                    patient_age=None,
                    patient_gender=None,
                    report_date=None,
                    parsing_confidence=None
                )
            else:
                # Invalid file_id format
                raise HTTPException(status_code=400, detail="Invalid file ID format")
        
        # Return the PDF status
        logger.info(f"Returning status for PDF {file_id}: {pdf.status}")
        return PDFStatusResponse(
            file_id=pdf.file_id,
            filename=pdf.filename,
            status=pdf.status,
            upload_date=pdf.upload_date,
            processed_date=pdf.processed_date,
            error_message=pdf.error_message if pdf.status == "error" else None,
            profile_id=pdf.profile_id,
            lab_name=pdf.lab_name,
            patient_name=pdf.patient_name,
            patient_id=pdf.patient_id,
            patient_age=pdf.patient_age,
            patient_gender=pdf.patient_gender,
            report_date=pdf.report_date,
            parsing_confidence=pdf.parsing_confidence
        )
    except Exception as e:
        logger.error(f"Error retrieving PDF status for {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving PDF status: {str(e)}")

@router.get("/list", response_model=PDFListResponse)
async def list_pdfs(db: Session = Depends(get_db)):
    """
    List all PDF files.
    
    Args:
        db: Database session
        
    Returns:
        PDFListResponse: A list of all PDF files
    """
    pdfs = db.query(PDFModel).all()
    
    pdf_responses = [
        PDFStatusResponse(
            file_id=pdf.file_id,
            filename=pdf.filename,
            status=pdf.status,
            upload_date=pdf.upload_date,
            processed_date=pdf.processed_date,
            error_message=pdf.error_message if pdf.status == "error" else None,
            profile_id=pdf.profile_id,
            lab_name=pdf.lab_name,
            patient_name=pdf.patient_name,
            patient_id=pdf.patient_id,
            patient_age=pdf.patient_age,
            patient_gender=pdf.patient_gender,
            report_date=pdf.report_date,
            parsing_confidence=pdf.parsing_confidence
        )
        for pdf in pdfs
    ]
    
    return PDFListResponse(
        total=len(pdf_responses),
        pdfs=pdf_responses
    )

@router.delete("/{file_id}")
async def delete_pdf(file_id: str, db: Session = Depends(get_db)):
    """
    Delete a PDF file.
    
    Args:
        file_id: The ID of the file to delete
        db: Database session
        
    Returns:
        dict: A message indicating success
    """
    try:
        # Log the request
        logger.info(f"Attempting to delete PDF with file_id: {file_id}")
        
        pdf = db.query(PDFModel).filter(PDFModel.file_id == file_id).first()
        
        if not pdf:
            logger.warning(f"PDF with file_id {file_id} not found in database for deletion")
            # Return a success message even if not found, as the end result is the same (file is not in system)
            return {"message": f"File with ID {file_id} is not in the system"}
        
        # Delete the file from disk if it exists
        if os.path.exists(pdf.file_path):
            try:
                os.remove(pdf.file_path)
                logger.info(f"Deleted file from disk: {pdf.file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {pdf.file_path}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")
        else:
            logger.warning(f"File {pdf.file_path} not found on disk")
        
        # Delete the record from the database
        db.delete(pdf)
        db.commit()
        logger.info(f"Successfully deleted PDF record for {file_id}")
        
        return {"message": f"File {pdf.filename} deleted successfully"}
    except Exception as e:
        logger.error(f"Error during PDF deletion for {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting PDF: {str(e)}")
