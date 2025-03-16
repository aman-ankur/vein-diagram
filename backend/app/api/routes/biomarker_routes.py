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
    profile_id: Optional[str] = Query(None, description="Filter biomarkers by profile ID"),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db)
):
    """
    Get all biomarkers with optional filtering.
    
    Args:
        category: Optional category to filter by
        profile_id: Optional profile ID to filter by
        limit: Maximum number of results to return
        offset: Offset for pagination
        db: Database session
        
    Returns:
        List of biomarkers
    """
    # Start with a base query
    query = db.query(Biomarker)
    
    # Apply category filter if provided
    if category:
        query = query.filter(Biomarker.category == category)
    
    # Apply profile filter if provided
    if profile_id:
        query = query.filter(Biomarker.profile_id == profile_id)
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute the query
    biomarkers = query.all()
    
    # Return the results
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
    profile_id: Optional[str] = Query(None, description="Filter biomarkers by profile ID"),
    limit: int = Query(100, ge=1, le=1000, description="Limit the number of results"),
    db: Session = Depends(get_db)
):
    """
    Search for biomarkers by name.
    
    Args:
        query: Search query (biomarker name)
        profile_id: Optional profile ID to filter by
        limit: Maximum number of results to return
        db: Database session
        
    Returns:
        List of matching biomarkers
    """
    # Convert query to lowercase and add wildcards
    search_query = f"%{query.lower()}%"
    
    # Create the base query
    db_query = db.query(Biomarker).filter(Biomarker.name.ilike(search_query))
    
    # Apply profile filter if provided
    if profile_id:
        db_query = db_query.filter(Biomarker.profile_id == profile_id)
    
    # Apply limit
    db_query = db_query.limit(limit)
    
    # Execute the query
    biomarkers = db_query.all()
    
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