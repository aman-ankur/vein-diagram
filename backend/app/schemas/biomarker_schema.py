from typing import Optional, Union, List
from pydantic import BaseModel, Field

class BiomarkerResponse(BaseModel):
    """
    Schema for biomarker response.
    """
    id: int
    pdf_id: int
    name: str = Field(..., description="Standardized name of the biomarker")
    value: float = Field(..., description="Standardized numeric value of the biomarker")
    unit: Optional[str] = Field("", description="Standardized unit of measurement")
    original_name: Optional[str] = Field(None, description="Original name as found in the lab report")
    original_value: Optional[str] = Field(None, description="Original value as found in the lab report (as a string)")
    original_unit: Optional[str] = Field(None, description="Original unit as found in the lab report")
    reference_range_low: Optional[float] = Field(None, description="Lower bound of reference range if available")
    reference_range_high: Optional[float] = Field(None, description="Upper bound of reference range if available")
    reference_range_text: Optional[str] = Field(None, description="Original reference range text")
    category: Optional[str] = Field(None, description="Category of the biomarker (e.g., Lipid, Metabolic)")
    is_abnormal: Optional[bool] = Field(False, description="Whether the value is outside the reference range")
    notes: Optional[str] = Field(None, description="Additional notes or observations")
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic v2 compatibility

class BiomarkerExplanationRequest(BaseModel):
    """
    Schema for requesting AI-generated explanations for a biomarker.
    """
    name: str = Field(..., description="Name of the biomarker")
    value: float = Field(..., description="Value of the biomarker")
    unit: str = Field(..., description="Unit of measurement")
    reference_range: str = Field(..., description="Reference range for the biomarker")
    is_abnormal: bool = Field(False, description="Whether the value is outside the reference range")

class BiomarkerExplanationResponse(BaseModel):
    """
    Schema for AI-generated explanations for a biomarker.
    """
    biomarker_id: int = Field(..., description="ID of the biomarker")
    name: str = Field(..., description="Name of the biomarker")
    general_explanation: str = Field(..., description="General explanation of what the biomarker measures")
    specific_explanation: str = Field(..., description="Personalized interpretation of the specific value")
    created_at: str = Field(..., description="Timestamp when the explanation was generated")
    from_cache: bool = Field(False, description="Whether the explanation was retrieved from cache") 