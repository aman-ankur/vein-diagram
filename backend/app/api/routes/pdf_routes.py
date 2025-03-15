from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
import os
import uuid
from app.services.pdf_service import extract_text_from_pdf
from app.schemas.pdf_schema import PDFResponse

router = APIRouter()

@router.post("/upload", response_model=PDFResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF file for processing.
    
    Args:
        file: The PDF file to upload
        
    Returns:
        PDFResponse: The response containing the extracted text and file ID
    """
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Generate a unique ID for the file
    file_id = str(uuid.uuid4())
    
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Save the file
    file_path = f"uploads/{file_id}.pdf"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Extract text from the PDF
    try:
        extracted_text = extract_text_from_pdf(file_path)
        return PDFResponse(
            file_id=file_id,
            filename=file.filename,
            extracted_text=extracted_text
        )
    except Exception as e:
        # Clean up the file if processing fails
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@router.get("/status/{file_id}")
async def get_pdf_status(file_id: str):
    """
    Get the processing status of a PDF file.
    
    Args:
        file_id: The ID of the file to check
        
    Returns:
        dict: The status of the file processing
    """
    # Check if the file exists
    file_path = f"uploads/{file_id}.pdf"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"status": "processed", "file_id": file_id} 