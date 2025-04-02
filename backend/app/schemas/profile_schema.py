"""
Pydantic schemas for Profile data validation.
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List, Dict, Any, Union
from datetime import datetime

class ProfileBase(BaseModel):
    """Base model for profile data with common attributes."""
    name: str = Field(..., description="Name of the profile")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    patient_id: Optional[str] = Field(None, description="Patient ID used in lab reports")

class ProfileCreate(ProfileBase):
    """Schema for creating a new profile."""
    pass

class ProfileUpdate(BaseModel):
    """Schema for updating an existing profile."""
    name: Optional[str] = Field(None, description="Name of the profile")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    patient_id: Optional[str] = Field(None, description="Patient ID used in lab reports")
    # Add favorite biomarkers to update schema
    favorite_biomarkers: Optional[List[str]] = Field(None, description="Ordered list of favorite biomarker names")

class ProfileInDB(ProfileBase):
    """Schema for profile data as stored in the database."""
    id: UUID4
    created_at: datetime
    last_modified: datetime
    favorite_biomarkers: List[str] = Field(default_factory=list, description="Ordered list of favorite biomarker names")
    health_summary: Optional[str] = Field(None, description="LLM-generated health summary")
    summary_last_updated: Optional[datetime] = Field(None, description="Timestamp of the last summary generation")

    class Config:
        from_attributes = True # Pydantic V2 uses from_attributes instead of orm_mode

class ProfileResponse(ProfileInDB):
    """Schema for profile data returned in API responses."""
    biomarker_count: Optional[int] = Field(0, description="Number of biomarkers associated with this profile")
    pdf_count: Optional[int] = Field(0, description="Number of PDF reports associated with this profile")
    # favorite_biomarkers is inherited from ProfileInDB
    # health_summary and summary_last_updated are commented out in parent, so not inherited here

class ProfileList(BaseModel):
    """Schema for a list of profiles."""
    profiles: List[ProfileResponse]
    total: int

# New schemas for the profile matching feature

class ProfileMatchScore(BaseModel):
    """Schema for profile match result with confidence score."""
    profile: ProfileResponse
    confidence: float = Field(..., description="Match confidence score between 0 and 1")

class ProfileExtractedMetadata(BaseModel):
    """Schema for extracted profile metadata from a PDF."""
    patient_name: Optional[str] = Field(None, description="Patient's name extracted from the PDF")
    patient_dob: Optional[Union[str, datetime]] = Field(None, description="Patient's date of birth extracted from the PDF")
    patient_gender: Optional[str] = Field(None, description="Patient's gender extracted from the PDF")
    patient_id: Optional[str] = Field(None, description="Patient ID extracted from the PDF")
    lab_name: Optional[str] = Field(None, description="Laboratory name extracted from the PDF")
    report_date: Optional[Union[str, datetime]] = Field(None, description="Report date extracted from the PDF")

class ProfileMatchingRequest(BaseModel):
    """Schema for requesting profile matching for a PDF."""
    pdf_id: str = Field(..., description="ID of the uploaded PDF to extract metadata from")
    
class ProfileMatchingResponse(BaseModel):
    """Schema for profile matching results."""
    matches: List[ProfileMatchScore] = Field(default_factory=list, description="List of matching profiles with confidence scores")
    metadata: ProfileExtractedMetadata = Field(..., description="Extracted metadata from the PDF")
    
class ProfileAssociationRequest(BaseModel):
    """Schema for associating a PDF with a profile."""
    profile_id: Optional[str] = Field(None, description="ID of the profile to associate with the PDF. If null, create a new profile.")
    pdf_id: str = Field(..., description="ID of the PDF to associate")
    create_new_profile: bool = Field(False, description="Whether to create a new profile instead of using an existing one")
    metadata_updates: Optional[Dict[str, Any]] = Field(None, description="Updates to make to the extracted metadata when creating a profile")
