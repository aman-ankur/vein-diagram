from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class PDF(Base):
    """
    Database model for uploaded PDF files.
    """
    __tablename__ = "pdfs"
    
    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String, unique=True, index=True)
    filename = Column(String)
    upload_date = Column(DateTime, default=datetime.utcnow)
    report_date = Column(DateTime, nullable=True)
    extracted_text = Column(Text)
    
    # Relationship with biomarkers
    biomarkers = relationship("Biomarker", back_populates="pdf")
    
class Biomarker(Base):
    """
    Database model for biomarker data extracted from PDFs.
    """
    __tablename__ = "biomarkers"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdfs.id"))
    name = Column(String, index=True)
    value = Column(Float)
    unit = Column(String)
    reference_range = Column(String, nullable=True)
    category = Column(String, nullable=True)
    
    # Relationship with PDF
    pdf = relationship("PDF", back_populates="biomarkers") 