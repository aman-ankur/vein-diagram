from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF
from app.schemas.biomarker_schema import BiomarkerResponse

router = APIRouter()

@router.get("/pdf/{file_id}/biomarkers", response_model=List[BiomarkerResponse])
def get_biomarkers_by_file_id(file_id: str, db: Session = Depends(get_db)):
    """
    Get all biomarkers for a specific PDF file.
    
    Args:
        file_id: The ID of the PDF file
        db: Database session
        
    Returns:
        List of biomarkers
    """
    # Check if the PDF exists
    pdf = db.query(PDF).filter(PDF.file_id == file_id).first()
    if not pdf:
        raise HTTPException(status_code=404, detail=f"PDF with ID {file_id} not found")
    
    # Get all biomarkers for the PDF
    biomarkers = db.query(Biomarker).filter(Biomarker.pdf_id == pdf.id).all()
    
    return biomarkers

@router.get("/biomarkers", response_model=List[BiomarkerResponse])
def get_all_biomarkers(
    category: Optional[str] = Query(None, description="Filter biomarkers by category"),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get all biomarkers with optional filtering by category.
    
    Args:
        category: Optional category to filter by
        limit: Maximum number of biomarkers to return
        offset: Offset for pagination
        db: Database session
        
    Returns:
        List of biomarkers
    """
    # Build the query
    query = db.query(Biomarker)
    
    # Apply category filter if provided
    if category:
        query = query.filter(Biomarker.category == category)
    
    # Apply pagination
    query = query.order_by(Biomarker.name).offset(offset).limit(limit)
    
    # Execute the query
    biomarkers = query.all()
    
    return biomarkers

@router.get("/biomarkers/categories", response_model=List[str])
def get_biomarker_categories(db: Session = Depends(get_db)):
    """
    Get all unique biomarker categories.
    
    Args:
        db: Database session
        
    Returns:
        List of unique categories
    """
    # Query for distinct categories
    categories = db.query(Biomarker.category).distinct().all()
    
    # Extract the category values from the result
    category_list = [category[0] for category in categories if category[0]]
    
    return sorted(category_list)

@router.get("/biomarkers/search", response_model=List[BiomarkerResponse])
def search_biomarkers(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of results"),
    db: Session = Depends(get_db)
):
    """
    Search for biomarkers by name.
    
    Args:
        query: Search query
        limit: Maximum number of biomarkers to return
        db: Database session
        
    Returns:
        List of matching biomarkers
    """
    # Create a SQL LIKE pattern
    search_pattern = f"%{query}%"
    
    # Query biomarkers where name contains the search term
    biomarkers = db.query(Biomarker).filter(
        Biomarker.name.ilike(search_pattern) | 
        Biomarker.original_name.ilike(search_pattern)
    ).limit(limit).all()
    
    return biomarkers

@router.get("/biomarkers/{biomarker_id}", response_model=BiomarkerResponse)
def get_biomarker_by_id(biomarker_id: int, db: Session = Depends(get_db)):
    """
    Get a specific biomarker by ID.
    
    Args:
        biomarker_id: ID of the biomarker
        db: Database session
        
    Returns:
        Biomarker details
    """
    biomarker = db.query(Biomarker).filter(Biomarker.id == biomarker_id).first()
    if not biomarker:
        raise HTTPException(status_code=404, detail=f"Biomarker with ID {biomarker_id} not found")
    
    return biomarker 