from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.biomarker_model import Biomarker, BiomarkerDictionary
from app.models.pdf_model import PDF
from app.schemas.biomarker_schema import BiomarkerResponse, BiomarkerExplanationRequest, BiomarkerExplanationResponse
from app.services.llm_service import explain_biomarker, ExplanationCache

router = APIRouter()
# Initialize the explanation cache
explanation_cache = ExplanationCache()

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

@router.post("/biomarkers/{biomarker_id}/explain", response_model=BiomarkerExplanationResponse)
async def explain_biomarker_with_ai(
    biomarker_id: int,
    request: BiomarkerExplanationRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate an AI explanation for a specific biomarker.
    
    Args:
        biomarker_id: ID of the biomarker to explain
        request: Request containing biomarker details
        background_tasks: FastAPI background tasks
        db: Database session
        
    Returns:
        Explanation of the biomarker with general information and personalized insights
    """
    try:
        # First check if we have this biomarker in our database
        biomarker = db.query(Biomarker).filter(Biomarker.id == biomarker_id).first()
        if not biomarker:
            raise HTTPException(status_code=404, detail=f"Biomarker with ID {biomarker_id} not found")
        
        # Check if we already have a general explanation for this biomarker in our cache
        biomarker_name = request.name or biomarker.name
        cached_general = explanation_cache.get_general_explanation(biomarker_name)
        
        # Prepare status
        status = "normal" if not request.is_abnormal else "abnormal"
        
        # Check if we already have a specific explanation for this value in our cache
        cache_key = f"{biomarker_name}:{request.value}:{status}"
        cached_specific = explanation_cache.get_specific_explanation(cache_key)
        
        # If we have both in cache, return immediately
        if cached_general and cached_specific:
            return BiomarkerExplanationResponse(
                biomarker_id=biomarker_id,
                name=biomarker_name,
                general_explanation=cached_general,
                specific_explanation=cached_specific,
                created_at=datetime.utcnow().isoformat(),
                from_cache=True
            )
        
        # Otherwise, query the LLM
        general_explanation, specific_explanation = await explain_biomarker(
            biomarker_name=biomarker_name,
            value=request.value,
            unit=request.unit,
            reference_range=request.reference_range,
            status=status
        )
        
        # Update cache in the background
        background_tasks.add_task(
            explanation_cache.add_explanation,
            biomarker_name,
            cache_key,
            general_explanation,
            specific_explanation
        )
        
        # Also check if we have this biomarker in our dictionary
        biomarker_dict = db.query(BiomarkerDictionary).filter(
            BiomarkerDictionary.standard_name == biomarker_name
        ).first()
        
        # If not, consider adding it in the background
        if not biomarker_dict and general_explanation:
            background_tasks.add_task(
                add_to_biomarker_dictionary,
                db,
                biomarker_name,
                general_explanation,
                request.unit
            )
        
        return BiomarkerExplanationResponse(
            biomarker_id=biomarker_id,
            name=biomarker_name,
            general_explanation=general_explanation,
            specific_explanation=specific_explanation,
            created_at=datetime.utcnow().isoformat(),
            from_cache=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

@router.post("/biomarkers/explain", response_model=BiomarkerExplanationResponse)
async def explain_generic_biomarker_with_ai(
    request: BiomarkerExplanationRequest,
    background_tasks: BackgroundTasks
):
    """
    Generate an AI explanation for a biomarker without requiring a database ID.
    Useful for generating explanations for biomarkers not in the database.
    
    Args:
        request: Request containing biomarker details
        background_tasks: FastAPI background tasks
        
    Returns:
        Explanation of the biomarker with general information and personalized insights
    """
    try:
        # Get biomarker name from request
        biomarker_name = request.name
        
        if not biomarker_name:
            raise HTTPException(status_code=400, detail="Biomarker name is required")
        
        # Check if we already have a general explanation for this biomarker in our cache
        cached_general = explanation_cache.get_general_explanation(biomarker_name)
        
        # Prepare status
        status = "normal" if not request.is_abnormal else "abnormal"
        
        # Check if we already have a specific explanation for this value in our cache
        cache_key = f"{biomarker_name}:{request.value}:{status}"
        cached_specific = explanation_cache.get_specific_explanation(cache_key)
        
        # If we have both in cache, return immediately
        if cached_general and cached_specific:
            return BiomarkerExplanationResponse(
                biomarker_id=0,  # Generic ID since this isn't from the database
                name=biomarker_name,
                general_explanation=cached_general,
                specific_explanation=cached_specific,
                created_at=datetime.utcnow().isoformat(),
                from_cache=True
            )
        
        # Otherwise, query the LLM
        general_explanation, specific_explanation = await explain_biomarker(
            biomarker_name=biomarker_name,
            value=request.value,
            unit=request.unit,
            reference_range=request.reference_range,
            status=status
        )
        
        # Update cache in the background
        background_tasks.add_task(
            explanation_cache.add_explanation,
            biomarker_name,
            cache_key,
            general_explanation,
            specific_explanation
        )
        
        return BiomarkerExplanationResponse(
            biomarker_id=0,  # Generic ID since this isn't from the database
            name=biomarker_name,
            general_explanation=general_explanation,
            specific_explanation=specific_explanation,
            created_at=datetime.utcnow().isoformat(),
            from_cache=False
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating explanation: {str(e)}")

async def add_to_biomarker_dictionary(
    db: Session,
    biomarker_name: str,
    explanation: str,
    unit: str
):
    """
    Add a new biomarker to the dictionary if it doesn't exist.
    This runs in a background task.
    """
    try:
        # Check again to avoid race conditions
        existing = db.query(BiomarkerDictionary).filter(
            BiomarkerDictionary.standard_name == biomarker_name
        ).first()
        
        if not existing:
            new_entry = BiomarkerDictionary(
                standard_name=biomarker_name,
                description=explanation,
                standard_unit=unit,
                alternate_names=json.dumps([]),
                unit_conversions=json.dumps({}),
                reference_ranges=json.dumps({})
            )
            db.add(new_entry)
            db.commit()
    except Exception as e:
        print(f"Error adding to biomarker dictionary: {str(e)}")
        db.rollback() 