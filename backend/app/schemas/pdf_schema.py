from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class BiomarkerBase(BaseModel):
    """
    Base model for biomarker data.
    """
    name: str
    original_name: Optional[str] = None
    original_value: str
    original_unit: str
    value: float
    unit: str
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    reference_range_text: Optional[str] = None
    category: Optional[str] = None
    is_abnormal: Optional[bool] = None
    importance: Optional[int] = 1
    notes: Optional[str] = None

class BiomarkerCreate(BiomarkerBase):
    """
    Model for creating a new biomarker.
    """
    pdf_id: int

class BiomarkerUpdate(BaseModel):
    """
    Model for updating biomarker data.
    """
    name: Optional[str] = None
    original_name: Optional[str] = None
    original_value: Optional[str] = None
    original_unit: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    reference_range_text: Optional[str] = None
    category: Optional[str] = None
    is_abnormal: Optional[bool] = None
    importance: Optional[int] = None
    notes: Optional[str] = None
    validated: Optional[bool] = None
    validated_by: Optional[str] = None
    validated_date: Optional[datetime] = None

class BiomarkerResponse(BiomarkerBase):
    """
    Response model for biomarker data.
    """
    id: int
    pdf_id: int
    extracted_date: datetime
    validated: bool = False
    validated_by: Optional[str] = None
    validated_date: Optional[datetime] = None
    
    class Config:
        orm_mode = True

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
    lab_name: Optional[str] = None
    patient_name: Optional[str] = None
    patient_id: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    report_date: Optional[datetime] = None
    parsing_confidence: Optional[float] = None
    
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
    
class ParsedPDFResponse(BaseModel):
    """
    Response model for parsed PDF data.
    """
    file_id: str
    filename: str
    lab_name: Optional[str] = None
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    patient_gender: Optional[str] = None
    report_date: Optional[datetime] = None
    biomarkers: List[BiomarkerResponse]
    parsing_confidence: Optional[float] = None
    
    class Config:
        orm_mode = True

class BiomarkerUpdateRequest(BaseModel):
    """
    Request model for updating biomarker data.
    """
    biomarker_id: int
    updates: BiomarkerUpdate
    
class BulkBiomarkerUpdate(BaseModel):
    """
    Request model for bulk updating biomarker data.
    """
    biomarkers: List[BiomarkerUpdateRequest] 