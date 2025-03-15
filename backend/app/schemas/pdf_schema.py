from pydantic import BaseModel
from typing import Optional, List, Dict

class PDFResponse(BaseModel):
    """
    Response model for PDF upload and processing.
    """
    file_id: str
    filename: str
    extracted_text: str

class BiomarkerData(BaseModel):
    """
    Model for biomarker data extracted from a PDF.
    """
    name: str
    value: float
    unit: str
    reference_range: Optional[str] = None
    category: Optional[str] = None
    
class ParsedPDFResponse(BaseModel):
    """
    Response model for parsed PDF data.
    """
    file_id: str
    filename: str
    date: Optional[str] = None
    biomarkers: List[BiomarkerData] 