from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
from app.models.biomarker_model import Biomarker

class PDF(Base):
    """
    Database model for uploaded PDF files.
    """
    __tablename__ = "pdfs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    processed_date = Column(DateTime, nullable=True)
    report_date = Column(DateTime, nullable=True)
    extracted_text = Column(Text, nullable=True)
    status = Column(String, default="pending")  # pending, processing, processed, error
    error_message = Column(Text, nullable=True)
    
    # Lab report details
    lab_name = Column(String, nullable=True)
    patient_name = Column(String, nullable=True)
    patient_id = Column(String, nullable=True)
    patient_age = Column(Integer, nullable=True)
    patient_gender = Column(String, nullable=True)
    
    # Processing metadata
    processing_details = Column(JSON, nullable=True)  # Store any metadata about processing
    parsing_confidence = Column(Float, nullable=True)  # Confidence score from Claude
    
    # Relationship with biomarkers
    biomarkers = relationship("Biomarker", back_populates="pdf", cascade="all, delete-orphan")
    
    def __repr__(self):
        """String representation of the PDF."""
        return f"<PDF {self.filename} ({self.file_id})>"

# Note: Biomarker class is now imported from biomarker_model.py 