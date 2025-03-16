"""
Pydantic schemas for Profile data validation.
"""
from pydantic import BaseModel, Field, UUID4
from typing import Optional, List
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

class ProfileInDB(ProfileBase):
    """Schema for profile data as stored in the database."""
    id: UUID4
    created_at: datetime
    last_modified: datetime

    class Config:
        orm_mode = True

class ProfileResponse(ProfileInDB):
    """Schema for profile data returned in API responses."""
    biomarker_count: Optional[int] = Field(0, description="Number of biomarkers associated with this profile")
    pdf_count: Optional[int] = Field(0, description="Number of PDF reports associated with this profile")

class ProfileList(BaseModel):
    """Schema for a list of profiles."""
    profiles: List[ProfileResponse]
    total: int 