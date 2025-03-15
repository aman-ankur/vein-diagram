from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class PDFResponse(BaseModel):
    """
    Response model for PDF upload and processing.
    """
    file_id: str
    filename: str
    status: str
    message: Optional[str] = None
    
class PDFStatusResponse(BaseModel):
    """
    Response model for PDF status.
    """
    file_id: str
    filename: str
    status: str
    upload_date: datetime
    processed_date: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        orm_mode = True

class PDFListResponse(BaseModel):
    """
    Response model for list of PDFs.
    """
    total: int
    pdfs: List[PDFStatusResponse]
    
    class Config:
        orm_mode = True

class PDFContentResponse(BaseModel):
    """
    Response model for PDF content.
    """
    file_id: str
    filename: str
    status: str
    extracted_text: Optional[str] = None
    
    class Config:
        orm_mode = True

class BiomarkerData(BaseModel):
    """
    Model for biomarker data extracted from a PDF.
    """
    name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    category: Optional[str] = None
    
    class Config:
        orm_mode = True
    
class ParsedPDFResponse(BaseModel):
    """
    Response model for parsed PDF data.
    """
    file_id: str
    filename: str
    date: Optional[str] = None
    biomarkers: List[BiomarkerData]
    
    class Config:
        orm_mode = True 