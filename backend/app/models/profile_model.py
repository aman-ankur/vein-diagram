"""
Profile data model for managing user profiles in the lab report analyzer application.
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, JSON, Text, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY # Added ARRAY for potential alternative
from datetime import datetime
import uuid
from app.db.database import Base

class Profile(Base):
    """
    Database model for user profiles to associate biomarkers with specific individuals.
    """
    __tablename__ = "profiles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String, nullable=True)
    patient_id = Column(String, nullable=True, index=True)  # For lab report reference numbers
    created_at = Column(DateTime, default=datetime.utcnow)
    last_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User ID from Supabase authentication
    user_id = Column(String(36), nullable=True, index=True)
    
    # Relationship with biomarkers
    biomarkers = relationship("Biomarker", back_populates="profile", cascade="all, delete-orphan")
    
    # Relationship with PDFs
    pdfs = relationship("PDF", back_populates="profile")
    
    # Store favorite biomarkers as an ordered list (JSON array of strings)
    favorite_biomarkers = Column(JSON, nullable=True, default=[]) 
    # Alternative using PostgreSQL ARRAY type (if using PostgreSQL):
    # favorite_biomarkers = Column(ARRAY(String), nullable=True, default=[])

    # Store the LLM-generated health summary (Temporarily commented out due to schema mismatch)
    health_summary = Column(Text, nullable=True)
    summary_last_updated = Column(DateTime, nullable=True)
    
    def __repr__(self):
        """String representation of the profile."""
        return f"<Profile {self.name} ({self.id})>"
