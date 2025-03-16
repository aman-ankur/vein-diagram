"""
Biomarker data models for storing information extracted from PDFs.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from app.db.database import Base

class Biomarker(Base):
    """
    Database model for biomarker data extracted from PDFs.
    """
    __tablename__ = "biomarkers"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"))
    profile_id = Column(UUID(as_uuid=True), ForeignKey("profiles.id"), nullable=True)
    
    # Basic biomarker info
    name = Column(String, index=True)  # Standardized name
    original_name = Column(String)     # Original name as found in report
    
    # Values in both original and standardized units
    original_value = Column(String)    # Original value as string to accommodate values like 'Nil', 'Negative', etc.
    original_unit = Column(String)
    value = Column(Float)          # Value in standardized unit
    unit = Column(String)          # Standardized unit
    
    # Reference ranges and context
    reference_range_low = Column(Float, nullable=True)
    reference_range_high = Column(Float, nullable=True)
    reference_range_text = Column(String, nullable=True)  # Original text representation
    
    # Additional information
    category = Column(String, nullable=True)
    is_abnormal = Column(Boolean, default=False)
    importance = Column(Integer, default=1)  # 1-5 scale of importance
    
    # Audit and validation
    extracted_date = Column(DateTime, default=datetime.utcnow)
    validated = Column(Boolean, default=False)
    validated_by = Column(String, nullable=True)
    validated_date = Column(DateTime, nullable=True)
    
    # Notes and contextual information
    notes = Column(Text, nullable=True)
    
    # Relationships
    pdf = relationship("PDF", back_populates="biomarkers")
    profile = relationship("Profile", back_populates="biomarkers")
    
    def __repr__(self):
        """String representation of the biomarker."""
        return f"<Biomarker {self.name}: {self.value} {self.unit}>"
    
class BiomarkerDictionary(Base):
    """
    Database model for storing standardized biomarker information.
    This allows for dynamic additions to the biomarker dictionary.
    """
    __tablename__ = "biomarker_dictionary"
    
    id = Column(Integer, primary_key=True, index=True)
    standard_name = Column(String, unique=True, index=True)
    alternate_names = Column(Text)  # Stored as JSON string of alternate names
    standard_unit = Column(String)
    unit_conversions = Column(Text)  # Stored as JSON string of conversion factors
    category = Column(String, nullable=True)
    reference_ranges = Column(Text)  # Stored as JSON string of reference ranges
    description = Column(Text, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    updated_date = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        """String representation of the biomarker dictionary entry."""
        return f"<BiomarkerDictionary {self.standard_name}>" 