from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status # Added status
from sqlalchemy.orm import Session, joinedload # Import joinedload
from sqlalchemy import func
import json
from datetime import datetime, timedelta
import uuid
from uuid import UUID
import logging

from app.db.session import get_db
from app.models.biomarker_model import Biomarker, BiomarkerDictionary
from app.models.pdf_model import PDF
from app.models.profile_model import Profile
from app.schemas.biomarker_schema import BiomarkerResponse, BiomarkerExplanationRequest, BiomarkerExplanationResponse
from app.services.llm_service import explain_biomarker, ExplanationCache

# Import authentication dependencies
from app.core.auth import get_current_user, get_optional_current_user

router = APIRouter()
logger = logging.getLogger(__name__)
# Initialize the explanation cache
explanation_cache = ExplanationCache()

@router.get("/pdf/{file_id}/biomarkers", response_model=List[BiomarkerResponse])
def get_biomarkers_by_file_id(
    file_id: str, 
    profile_id: Optional[str] = Query(None, description="Filter biomarkers by profile ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all biomarkers for a specific PDF file.
    
    Args:
        file_id: The ID of the PDF file
        profile_id: Optional profile ID to filter by
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of biomarkers
    """
    try:
        # Log the request
        logger.info(f"Getting biomarkers for PDF with file_id: {file_id}, profile_id: {profile_id}")
        
        # Get the user_id from the authenticated user
        user_id = current_user.get("user_id")
        
        # Check if the PDF exists
        pdf = db.query(PDF).filter(PDF.file_id == file_id).first()
        if not pdf:
            logger.warning(f"PDF with ID {file_id} not found, returning empty biomarkers list")
            return []  # Return empty list instead of 404
        
        # Start with a base query
        query = db.query(Biomarker).filter(Biomarker.pdf_id == pdf.id).options(joinedload(Biomarker.pdf))
        
        # Apply profile filter if provided
        if profile_id:
            try:
                # Convert string to UUID
                profile_uuid = UUID(profile_id)
                
                # Check if profile belongs to the current user
                profile = db.query(Profile).filter(
                    Profile.id == profile_uuid,
                    Profile.user_id == user_id
                ).first()
                
                if not profile:
                    logger.warning(f"Profile {profile_id} not found or not accessible for user {user_id}, returning empty list")
                    return []  # Return empty list instead of 404
                
                query = query.filter(Biomarker.profile_id == profile_uuid)
            except ValueError:
                logger.error(f"Invalid profile ID format: {profile_id}")
                raise HTTPException(status_code=400, detail=f"Invalid profile ID format: {profile_id}")
        
        # Execute the query
        biomarkers = query.all()
        logger.info(f"Found {len(biomarkers)} biomarkers for PDF {file_id}")
        
        # Process the biomarker objects to properly handle PDF relationship
        result = []
        for biomarker in biomarkers:
            # Create a dictionary for the biomarker
            biomarker_dict = {
                "id": biomarker.id,
                "pdf_id": biomarker.pdf_id,
                "name": biomarker.name,
                "original_name": biomarker.original_name,
                "original_value": biomarker.original_value,
                "original_unit": biomarker.original_unit,
                "value": biomarker.value,
                "unit": biomarker.unit,
                "reference_range_low": biomarker.reference_range_low,
                "reference_range_high": biomarker.reference_range_high,
                "reference_range_text": biomarker.reference_range_text,
                "category": biomarker.category,
                "is_abnormal": biomarker.is_abnormal,
                "notes": biomarker.notes,
                "extracted_date": biomarker.extracted_date,
                "validated": biomarker.validated,
                "validated_by": biomarker.validated_by,
                "validated_date": biomarker.validated_date,
                "pdf": None
            }
            
            # If pdf relationship is loaded, add it to the result
            if biomarker.pdf:
                biomarker_dict["pdf"] = {
                    "file_id": biomarker.pdf.file_id,
                    "filename": biomarker.pdf.filename,
                    "report_date": biomarker.pdf.report_date
                }
            
            result.append(biomarker_dict)
        
        # Return the processed results
        return result
    except Exception as e:
        logger.error(f"Error fetching biomarkers for PDF {file_id}: {str(e)}")
        # Re-raise for now, but with a more specific message
        raise HTTPException(status_code=500, detail=f"Error fetching biomarkers: {str(e)}")

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
    """
    # Log the request parameters
    logger.info(f"GET /biomarkers with category={category}, profile_id={profile_id}, limit={limit}, offset={offset}")
    
    # Start with a base query and eager load PDF relationship
    query = db.query(Biomarker).options(joinedload(Biomarker.pdf))
    
    # Apply category filter if provided
    if category:
        query = query.filter(Biomarker.category == category)
    
    # Apply profile filter if provided
    if profile_id:
        try:
            profile_uuid = UUID(profile_id)
            query = query.filter(Biomarker.profile_id == profile_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid profile ID format: {profile_id}")
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute the query
    biomarkers = query.all()
    logger.info(f"Found {len(biomarkers)} biomarkers")
    
    # Process and return the results
    return [BiomarkerResponse.from_orm(b) for b in biomarkers]

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
    db_query = db.query(Biomarker).filter(Biomarker.name.ilike(search_query)).options(joinedload(Biomarker.pdf))
    
    # Apply profile filter if provided
    if profile_id:
        try:
            # Convert string to UUID
            profile_uuid = UUID(profile_id)
            db_query = db_query.filter(Biomarker.profile_id == profile_uuid)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid profile ID format: {profile_id}")
    
    # Apply limit
    db_query = db_query.limit(limit)
    
    # Execute the query
    biomarkers = db_query.all()
    
    # Process the biomarker objects to properly handle PDF relationship
    result = []
    for biomarker in biomarkers:
        # Create a dictionary for the biomarker
        biomarker_dict = {
            "id": biomarker.id,
            "pdf_id": biomarker.pdf_id,
            "name": biomarker.name,
            "original_name": biomarker.original_name,
            "original_value": biomarker.original_value,
            "original_unit": biomarker.original_unit,
            "value": biomarker.value,
            "unit": biomarker.unit,
            "reference_range_low": biomarker.reference_range_low,
            "reference_range_high": biomarker.reference_range_high,
            "reference_range_text": biomarker.reference_range_text,
            "category": biomarker.category,
            "is_abnormal": biomarker.is_abnormal,
            "notes": biomarker.notes,
            "extracted_date": biomarker.extracted_date,
            "validated": biomarker.validated,
            "validated_by": biomarker.validated_by,
            "validated_date": biomarker.validated_date,
            "pdf": None
        }
        
        # If pdf relationship is loaded, add it to the result
        if biomarker.pdf:
            biomarker_dict["pdf"] = {
                "file_id": biomarker.pdf.file_id,
                "filename": biomarker.pdf.filename,
                "report_date": biomarker.pdf.report_date
            }
        
        result.append(biomarker_dict)
    
    # Return the processed results
    return result

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
    biomarker = db.query(Biomarker).filter(Biomarker.id == biomarker_id).options(joinedload(Biomarker.pdf)).first()
    if not biomarker:
        raise HTTPException(status_code=404, detail=f"Biomarker with ID {biomarker_id} not found")
    
    # Create a dictionary for the biomarker
    biomarker_dict = {
        "id": biomarker.id,
        "pdf_id": biomarker.pdf_id,
        "name": biomarker.name,
        "original_name": biomarker.original_name,
        "original_value": biomarker.original_value,
        "original_unit": biomarker.original_unit,
        "value": biomarker.value,
        "unit": biomarker.unit,
        "reference_range_low": biomarker.reference_range_low,
        "reference_range_high": biomarker.reference_range_high,
        "reference_range_text": biomarker.reference_range_text,
        "category": biomarker.category,
        "is_abnormal": biomarker.is_abnormal,
        "notes": biomarker.notes,
        "extracted_date": biomarker.extracted_date,
        "validated": biomarker.validated,
        "validated_by": biomarker.validated_by,
        "validated_date": biomarker.validated_date,
        "pdf": None
    }
    
    # If pdf relationship is loaded, add it to the result
    if biomarker.pdf:
        biomarker_dict["pdf"] = {
            "file_id": biomarker.pdf.file_id,
            "filename": biomarker.pdf.filename,
            "report_date": biomarker.pdf.report_date
        }
    
    # Return the processed result
    return biomarker_dict

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


@router.delete("/biomarkers/{biomarker_entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_biomarker_entry(biomarker_entry_id: int, db: Session = Depends(get_db)):
    """
    Delete a specific biomarker entry by its ID.

    Args:
        biomarker_entry_id: The primary key ID of the biomarker entry to delete.
        db: Database session.

    Returns:
        None (HTTP 204 No Content on success).
    """
    # Find the biomarker entry
    biomarker_entry = db.query(Biomarker).filter(Biomarker.id == biomarker_entry_id).first()

    # If not found, raise 404
    if not biomarker_entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Biomarker entry with ID {biomarker_entry_id} not found",
        )

    # Delete the entry
    try:
        db.delete(biomarker_entry)
        db.commit()
        print(f"Successfully deleted biomarker entry with ID {biomarker_entry_id}")
    except Exception as e:
        db.rollback()
        print(f"Error deleting biomarker entry {biomarker_entry_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete biomarker entry: {str(e)}",
        )

    return None # FastAPI handles the 204 response
