"""
API routes for profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from sqlalchemy import String  # Add this import
from typing import List, Optional, Dict, Any
from uuid import UUID
import logging
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from app.db.session import get_db
from app.models.profile_model import Profile
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF
from app.schemas.profile_schema import (
    ProfileCreate, 
    ProfileUpdate, 
    ProfileResponse, 
    ProfileList,
    ProfileMatchingRequest,
    ProfileMatchingResponse,
    ProfileMatchScore,
    ProfileExtractedMetadata,
    ProfileAssociationRequest,
    ProfileMergeRequest, # Import the new schema
    # Assuming a simple schema for the order update
    # If not defined elsewhere, add it here or in profile_schema.py
    # class FavoriteOrderUpdate(BaseModel):
    #     ordered_favorites: List[str]
)
from app.services.profile_matcher import find_matching_profiles, create_profile_from_metadata
from app.services.metadata_parser import extract_metadata_with_claude
from pydantic import BaseModel, Field # Import BaseModel and Field if defining schema here
from app.services.health_summary_service import generate_and_update_health_summary
from app.services.profile_service import merge_profiles # Import the new service function

# Import authentication dependencies
from app.core.auth import get_current_user, get_optional_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Schemas specific to favorite operations ---
class AddFavoriteRequest(BaseModel):
    biomarker_name: str = Field(..., description="Name of the biomarker to add to favorites")


@router.post("/", response_model=ProfileResponse, status_code=201)
async def create_profile(
    profile: ProfileCreate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new profile.
    """
    try:
        # Associate the profile with the authenticated user
        user_id = current_user.get("user_id")
        
        db_profile = Profile(
            name=profile.name,
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            patient_id=profile.patient_id,
            user_id=user_id  # Set the user_id from authentication
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        
        # Count biomarkers and PDFs (will be 0 for new profile)
        biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == db_profile.id).scalar()
        pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == db_profile.id).scalar()
        
        # Create response
        response = ProfileResponse(
            id=db_profile.id,
            name=db_profile.name,
            date_of_birth=db_profile.date_of_birth,
            gender=db_profile.gender,
            patient_id=db_profile.patient_id,
            created_at=db_profile.created_at,
            last_modified=db_profile.last_modified,
            biomarker_count=biomarker_count,
            pdf_count=pdf_count,
            user_id=user_id
        )
        
        return response
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error when creating profile: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not create profile due to database constraint violation")
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("", response_model=ProfileList)
@router.get("/", response_model=ProfileList)
async def get_profiles(
    skip: int = Query(0, description="Number of profiles to skip"),
    limit: int = Query(100, description="Maximum number of profiles to return"),
    search: Optional[str] = Query(None, description="Search term for profile name or patient ID"),
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get all profiles with optional search and pagination.
    Only returns profiles associated with the authenticated user.
    """
    try:
        # Get user_id from authentication
        user_id = current_user.get("user_id")
        logger.info(f"GET /profiles with skip={skip}, limit={limit}, search={search}, user_id={user_id}")
        
        # Base query
        query = db.query(
            Profile.id,
            Profile.name,
            Profile.date_of_birth,
            Profile.gender,
            Profile.patient_id,
            Profile.created_at,
            Profile.last_modified,
            Profile.favorite_biomarkers,
            Profile.user_id
        ).filter(Profile.user_id == user_id)

        if search:
            search_term = f"%{search}%"
            query = query.filter(Profile.name.ilike(search_term) | Profile.patient_id.ilike(search_term))

        total = query.count()
        profile_tuples = query.offset(skip).limit(limit).all()
        logger.info(f"Found {total} total profiles, returning {len(profile_tuples)} after pagination")

        # Prepare response
        profile_responses = []
        for p_id, p_name, p_dob, p_gender, p_patient_id, p_created_at, p_last_modified, p_favs, p_user_id in profile_tuples:
            biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == p_id).scalar()
            pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == p_id).scalar()

            profile_data = {
                "id": p_id,
                "name": p_name,
                "date_of_birth": p_dob,
                "gender": p_gender,
                "patient_id": p_patient_id,
                "created_at": p_created_at,
                "last_modified": p_last_modified,
                "favorite_biomarkers": p_favs if p_favs else [],
                "biomarker_count": biomarker_count,
                "pdf_count": pdf_count,
                "health_summary": None,
                "summary_last_updated": None,
                "user_id": p_user_id
            }
            response_item = ProfileResponse(**profile_data)
            profile_responses.append(response_item)
        
        return ProfileList(profiles=profile_responses, total=total)
    except Exception as e:
        logger.error(f"Error retrieving profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get details of a specific profile by ID.
    Only allows access to profiles owned by the authenticated user.
    """
    logger.info(f"GET endpoint called for profile ID: {profile_id}")
    user_id = current_user.get("user_id")

    try:
        # Convert string to UUID
        try:
            profile_id_uuid = UUID(profile_id)
            profile = db.query(Profile).filter(
                Profile.id == profile_id_uuid,
                Profile.user_id == user_id  # Filter by user_id for security
            ).first()
        except ValueError as e:
            logger.error(f"Invalid UUID format: {profile_id}")
            raise HTTPException(status_code=400, detail="Invalid profile ID format")
        
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get counts
        biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == profile.id).scalar()
        pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == profile.id).scalar()

        # Use from_orm to map fields automatically, including the new summary fields
        response = ProfileResponse.from_orm(profile)
        
        # Add the counts to the response object
        response.biomarker_count = biomarker_count
        response.pdf_count = pdf_count
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profile {profile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: UUID,
    profile_update: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update an existing profile.
    Only allows updating profiles owned by the authenticated user.
    """
    logger.info(f"PUT endpoint called for profile ID: {profile_id}")
    user_id = current_user.get("user_id")
    
    try:
        # Query with user_id filter
        db_profile = db.query(Profile).filter(
            Profile.id == profile_id,
            Profile.user_id == user_id  # Filter by user_id for security
        ).first()
                    
        if not db_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Update fields if provided
        if profile_update.name is not None:
            db_profile.name = profile_update.name
        if profile_update.date_of_birth is not None:
            db_profile.date_of_birth = profile_update.date_of_birth
        if profile_update.gender is not None:
            db_profile.gender = profile_update.gender
        if profile_update.patient_id is not None:
            db_profile.patient_id = profile_update.patient_id
        if profile_update.favorite_biomarkers is not None:
            db_profile.favorite_biomarkers = profile_update.favorite_biomarkers
        
        # Update last_modified timestamp
        db_profile.last_modified = datetime.utcnow()
        
        db.commit()
        db.refresh(db_profile)
        
        # Get counts
        biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == db_profile.id).scalar()
        pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == db_profile.id).scalar()
        
        return ProfileResponse(
            id=db_profile.id,
            name=db_profile.name,
            date_of_birth=db_profile.date_of_birth,
            gender=db_profile.gender,
            patient_id=db_profile.patient_id,
            created_at=db_profile.created_at,
            last_modified=db_profile.last_modified,
            biomarker_count=biomarker_count,
            pdf_count=pdf_count,
            favorite_biomarkers=db_profile.favorite_biomarkers,
            health_summary=db_profile.health_summary,
            summary_last_updated=db_profile.summary_last_updated,
            user_id=db_profile.user_id
        )
    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error when updating profile: {str(e)}")
        raise HTTPException(status_code=400, detail="Could not update profile due to database constraint violation")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating profile {profile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: str,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a profile. 
    Note: This will not delete associated biomarkers or PDFs but will unlink them.
    Only allows deleting profiles owned by the authenticated user.
    """
    profile_id = profile_id.strip()
    user_id = current_user.get("user_id")
    
    try:
        # Convert string to UUID
        try:
            profile_id_uuid = UUID(profile_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid profile ID format: {str(e)}")
        
        # Find the profile with user_id filter
        db_profile = db.query(Profile).filter(
            Profile.id == profile_id_uuid,
            Profile.user_id == user_id  # Filter by user_id for security
        ).first()
        
        if not db_profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Unlink biomarkers and PDFs
        biomarker_count = db.query(Biomarker).filter(Biomarker.profile_id == db_profile.id).count()
        pdf_count = db.query(PDF).filter(PDF.profile_id == db_profile.id).count()
        
        db.query(Biomarker).filter(Biomarker.profile_id == db_profile.id).update({"profile_id": None})
        db.query(PDF).filter(PDF.profile_id == db_profile.id).update({"profile_id": None})
        
        # Delete the profile
        db.delete(db_profile)
        db.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting profile {profile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/extract/{pdf_id}", response_model=List[ProfileResponse])
async def extract_profile_from_pdf(
    pdf_id: int,
    confidence_threshold: float = Query(0.7, ge=0.0, le=1.0),
    db: Session = Depends(get_db)
):
    """
    Extract profile information from a PDF and suggest matching profiles based on name, DOB, and patient ID.
    Returns a list of potential profile matches with confidence scores.
    """
    try:
        # Get the PDF
        pdf = db.query(PDF).filter(PDF.id == pdf_id).first()
        
        if not pdf:
            raise HTTPException(status_code=404, detail="PDF not found")
        
        # Extract potential profile info
        potential_matches = []
        
        # Check for direct patient_id match first
        if pdf.patient_id:
            patient_id_matches = db.query(Profile).filter(Profile.patient_id == pdf.patient_id).all()
            for match in patient_id_matches:
                # This is a high confidence match (patient ID is unique)
                biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == match.id).scalar()
                pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == match.id).scalar()
                
                potential_matches.append(
                    ProfileResponse(
                        id=match.id,
                        name=match.name,
                        date_of_birth=match.date_of_birth,
                        gender=match.gender,
                        patient_id=match.patient_id,
                        created_at=match.created_at,
                        last_modified=match.last_modified,
                        biomarker_count=biomarker_count,
                        pdf_count=pdf_count
                    )
                )
        
        # If no patient_id match, try name match
        if not potential_matches and pdf.patient_name:
            name_matches = db.query(Profile).filter(Profile.name.ilike(f"%{pdf.patient_name}%")).all()
            for match in name_matches:
                # Name matches are medium confidence
                biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == match.id).scalar()
                pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == match.id).scalar()
                
                potential_matches.append(
                    ProfileResponse(
                        id=match.id,
                        name=match.name,
                        date_of_birth=match.date_of_birth,
                        gender=match.gender,
                        patient_id=match.patient_id,
                        created_at=match.created_at,
                        last_modified=match.last_modified,
                        biomarker_count=biomarker_count,
                        pdf_count=pdf_count
                    )
                )
        
        # Return matches
        return potential_matches
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting profile from PDF {pdf_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# New endpoints for profile matching feature

@router.post("/match", response_model=ProfileMatchingResponse)
async def match_profile_from_pdf(
    request: ProfileMatchingRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Extract metadata from a PDF and find matching profiles.
    Only matches against profiles owned by the authenticated user.
    """
    user_id = current_user.get("user_id")
    try:
        # If user_id isn't provided in the request, use the authenticated user's ID
        if not request.user_id:
            request.user_id = user_id
        # Security check: ensure user can only search their own profiles
        elif request.user_id != user_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only match against your own profiles"
            )
        
        # Find the PDF by file_id
        pdf = db.query(PDF).filter(PDF.file_id == request.pdf_id).first()
        if not pdf:
            raise HTTPException(status_code=404, detail=f"PDF with ID {request.pdf_id} not found")
        
        # Extract metadata with Claude
        if not pdf.extracted_text:
            logger.error(f"PDF {request.pdf_id} doesn't have extracted text. Status: {pdf.status}")
            raise HTTPException(
                status_code=400, 
                detail=f"PDF text has not been extracted yet. Current status: {pdf.status}"
            )
            
        # Call extract_metadata_with_claude with text and filename
        metadata = await extract_metadata_with_claude(pdf.extracted_text, pdf.filename)
        
        # Find matching profiles
        matches = await find_matching_profiles(metadata, db, user_id=user_id)
        
        # Return the response
        return ProfileMatchingResponse(
            metadata=metadata,
            matches=matches
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error matching profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/associate", response_model=ProfileResponse)
async def associate_pdf_with_profile(
    request: ProfileAssociationRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Associate a PDF with an existing profile or create a new profile.
    Only allows associating with profiles owned by the authenticated user.
    """
    user_id = current_user.get("user_id")
    
    try:
        # If user_id isn't provided in the request, use the authenticated user's ID
        if not request.user_id:
            request.user_id = user_id
        # Security check: ensure user can only access their own profiles
        elif request.user_id != user_id:
            raise HTTPException(
                status_code=403, 
                detail="You can only associate with your own profiles"
            )
            
        # Find PDF
        pdf = db.query(PDF).filter(PDF.file_id == request.pdf_id).first()
        if not pdf:
            raise HTTPException(status_code=404, detail=f"PDF with ID {request.pdf_id} not found")
            
        profile = None
        
        # Handle the three options: 
        # 1) Use existing profile
        # 2) Create new profile
        # 3) Auto-create profile from metadata
        
        if request.profile_id:
            # Option 1: Use existing profile
            try:
                profile_id_uuid = UUID(request.profile_id)
                profile = db.query(Profile).filter(
                    Profile.id == profile_id_uuid,
                    Profile.user_id == user_id  # Filter by user_id for security
                ).first()
                
                if not profile:
                    raise HTTPException(status_code=404, detail="Profile not found or not accessible")
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid profile ID format")
                
        elif request.create_new_profile:
            # Option 2: Create new profile from request
            # Extract metadata from PDF if available
            if not pdf.extracted_text:
                logger.error(f"PDF {request.pdf_id} doesn't have extracted text. Status: {pdf.status}")
                raise HTTPException(
                    status_code=400, 
                    detail=f"PDF text has not been extracted yet. Current status: {pdf.status}"
                )
                
            # Call extract_metadata_with_claude with text and filename  
            metadata = await extract_metadata_with_claude(pdf.extracted_text, pdf.filename)
            
            # Apply any updates from request
            if request.metadata_updates:
                for key, value in request.metadata_updates.items():
                    if key in metadata:
                        metadata[key] = value
            
            # Create profile from metadata
            profile = create_profile_from_metadata(db, metadata, user_id)
        
        # If neither option was specified or successful, raise an error
        if not profile:
            raise HTTPException(
                status_code=400, 
                detail="Must specify either profile_id or create_new_profile=true"
            )
            
        # Associate PDF with profile
        pdf.profile_id = profile.id
        db.commit()
        
        # Get updated counts
        biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == profile.id).scalar()
        pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == profile.id).scalar()
        
        # Associate all biomarkers from this PDF with the profile
        db.query(Biomarker).filter(
            Biomarker.pdf_id == pdf.id,
            Biomarker.profile_id.is_(None)
        ).update({"profile_id": profile.id})
        
        db.commit()
        
        return ProfileResponse(
            id=profile.id,
            name=profile.name,
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            patient_id=profile.patient_id,
            created_at=profile.created_at,
            last_modified=profile.last_modified,
            biomarker_count=biomarker_count,
            pdf_count=pdf_count,
            favorite_biomarkers=profile.favorite_biomarkers,
            health_summary=profile.health_summary,
            summary_last_updated=profile.summary_last_updated,
            user_id=profile.user_id
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error associating PDF with profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Schema for updating favorite order
class FavoriteOrderUpdate(BaseModel):
    ordered_favorites: List[str]

@router.put("/{profile_id}/favorites/order", response_model=ProfileResponse)
async def update_favorite_biomarker_order(
    profile_id: UUID,
    order_update: FavoriteOrderUpdate,
    db: Session = Depends(get_db)
):
    """
    Update the order of favorite biomarkers for a specific profile.
    """
    logger.info(f"Updating favorite order for profile ID: {profile_id}")
    
    try:
        # Find the profile
        db_profile = db.query(Profile).filter(Profile.id == profile_id).first()
        
        if not db_profile:
            logger.error(f"Profile not found: {profile_id}")
            raise HTTPException(status_code=404, detail="Profile not found")
            
        # Validate the input list (optional, e.g., check if names are valid biomarkers)
        # For now, directly update the stored list
        db_profile.favorite_biomarkers = order_update.ordered_favorites
        db_profile.last_modified = datetime.utcnow()
        
        db.commit()
        db.refresh(db_profile)
        
        logger.info(f"Successfully updated favorite order for profile {profile_id}")
        
        # Return the updated profile response (including the new order)
        biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == db_profile.id).scalar()
        pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == db_profile.id).scalar()
        
        return ProfileResponse(
            id=db_profile.id,
            name=db_profile.name,
            date_of_birth=db_profile.date_of_birth,
            gender=db_profile.gender,
            patient_id=db_profile.patient_id,
            created_at=db_profile.created_at,
            last_modified=db_profile.last_modified,
            favorite_biomarkers=db_profile.favorite_biomarkers, # Include the updated list
            biomarker_count=biomarker_count,
            pdf_count=pdf_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating favorite order for profile {profile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/{profile_id}/favorites", response_model=ProfileResponse)
async def add_favorite_biomarker(
    profile_id: UUID,
    request: AddFavoriteRequest,
    db: Session = Depends(get_db)
):
    """
    Add a biomarker to the profile's favorites list.
    """
    logger.info(f"Adding favorite '{request.biomarker_name}' for profile ID: {profile_id}")
    
    db_profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    # Ensure the list exists and is mutable
    if db_profile.favorite_biomarkers is None:
        db_profile.favorite_biomarkers = []
    
    # Add if not already present (convert to list if it's somehow not)
    current_favorites = list(db_profile.favorite_biomarkers)
    if request.biomarker_name not in current_favorites:
        current_favorites.append(request.biomarker_name)
        db_profile.favorite_biomarkers = current_favorites # Assign back the modified list
        db_profile.last_modified = datetime.utcnow()
        db.commit()
        db.refresh(db_profile)
        logger.info(f"Added '{request.biomarker_name}' to favorites for profile {profile_id}")
    else:
        logger.info(f"'{request.biomarker_name}' already in favorites for profile {profile_id}")

    # Return the updated profile
    biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == db_profile.id).scalar()
    pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == db_profile.id).scalar()
    return ProfileResponse.from_orm(db_profile) # Use from_orm for cleaner mapping


@router.delete("/{profile_id}/favorites/{biomarker_name}", response_model=ProfileResponse)
async def remove_favorite_biomarker(
    profile_id: UUID,
    biomarker_name: str,
    db: Session = Depends(get_db)
):
    """
    Remove a biomarker from the profile's favorites list.
    """
    logger.info(f"Removing favorite '{biomarker_name}' for profile ID: {profile_id}")
    
    db_profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not db_profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    # Ensure the list exists and is mutable
    if db_profile.favorite_biomarkers is None:
        db_profile.favorite_biomarkers = []
        
    current_favorites = list(db_profile.favorite_biomarkers)
    if biomarker_name in current_favorites:
        current_favorites.remove(biomarker_name)
        db_profile.favorite_biomarkers = current_favorites # Assign back the modified list
        db_profile.last_modified = datetime.utcnow()
        db.commit()
        db.refresh(db_profile)
        logger.info(f"Removed '{biomarker_name}' from favorites for profile {profile_id}")
    else:
         logger.info(f"'{biomarker_name}' not found in favorites for profile {profile_id}")

    # Return the updated profile
    biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == db_profile.id).scalar()
    pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == db_profile.id).scalar()
    return ProfileResponse.from_orm(db_profile) # Use from_orm for cleaner mapping

@router.post("/{profile_id}/generate-summary", response_model=ProfileResponse)
async def generate_profile_summary(
    profile_id: UUID, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Generate an AI health summary for a profile in the background.
    """
    try:
        # First check if profile exists
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Add the task to the background tasks
        background_tasks.add_task(generate_and_update_health_summary, profile_id, db)
        
        # Return the profile object (without waiting for summary generation)
        biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == profile.id).scalar()
        pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == profile.id).scalar()
        
        response = ProfileResponse.from_orm(profile)
        response.biomarker_count = biomarker_count
        response.pdf_count = pdf_count
        
        return response
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary for profile {profile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# --- Profile Merging Endpoint ---

@router.post("/merge", status_code=200, response_model=Dict[str, str])
async def merge_profiles_endpoint(
    request: ProfileMergeRequest,
    db: Session = Depends(get_db)
):
    """
    Merge multiple source profiles into a single target profile.
    Re-associates biomarkers and PDFs, handles deduplication, and deletes source profiles.
    """
    logger.info(f"Received request to merge profiles {request.source_profile_ids} into {request.target_profile_id}")
    
    try:
        # Call the service function to perform the merge
        merge_profiles(db=db, merge_request=request)
        
        # Make sure to commit the transaction
        db.commit()
        
        logger.info(f"Successfully merged profiles {request.source_profile_ids} into {request.target_profile_id}")
        return {"message": "Profiles merged successfully"}
    except HTTPException as http_exc:
        # Re-raise HTTP exceptions (like 400, 404) from the service layer
        db.rollback()
        logger.warning(f"HTTP Exception during merge: {http_exc.detail}")
        raise http_exc
    except Exception as e:
        # Catch any other unexpected errors
        db.rollback()
        logger.error(f"Unexpected error during profile merge endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during merge: {str(e)}")

@router.post("/migrate", response_model=Dict[str, Any])
async def migrate_profiles_to_current_user(
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Migrate all unassigned profiles to the currently authenticated user.
    This is particularly useful after implementing auth to ensure users maintain
    access to their previously created profiles.
    """
    try:
        user_id = current_user.get("user_id")
        logger.info(f"Migrating profiles to user: {user_id}")
        
        # Find profiles with no user_id or NULL user_id
        unassigned_profiles = db.query(Profile).filter(
            (Profile.user_id == None) | 
            (Profile.user_id == "") |
            (Profile.user_id == "null")
        ).all()
        
        logger.info(f"Found {len(unassigned_profiles)} unassigned profiles")
        
        # Update these profiles to belong to the current user
        for profile in unassigned_profiles:
            profile.user_id = user_id
            profile.last_modified = datetime.utcnow()
            logger.info(f"Assigning profile {profile.id} ({profile.name}) to user {user_id}")
        
        # Commit all updates
        db.commit()
        
        # Also query for profiles already belonging to the user for the response
        user_profiles = db.query(Profile).filter(Profile.user_id == user_id).all()
        
        return {
            "success": True,
            "message": f"Successfully migrated {len(unassigned_profiles)} profiles to your account",
            "migrated_count": len(unassigned_profiles),
            "total_profiles": len(user_profiles)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error during profile migration: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to migrate profiles: {str(e)}")

# --- Favorite Biomarker Summary Endpoint ---

@router.post("/{profile_id}/favorite-summary", response_model=FavoriteSummaryResponse)
async def get_favorite_biomarker_summary_endpoint(
    profile_id: UUID,
    request: FavoriteSummaryRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Generate or retrieve a cached summary for selected favorite biomarkers.
    Checks the cache first, if not found, generates a new summary via LLM.
    """
    try:
        # Verify profile exists and belongs to user
        user_id = current_user.get("user_id")
        profile = db.query(Profile).filter(
            Profile.id == profile_id,
            Profile.user_id == user_id
        ).first()
        
        if not profile:
            logger.warning(f"Profile {profile_id} not found or access denied for user {user_id}.")
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Check if biomarker names were provided
        if not request.biomarker_names:
            logger.warning(f"No biomarker names provided for profile {profile_id}.")
            raise HTTPException(status_code=400, detail="No biomarker names provided")
        
        # Generate the unique hash for this set of biomarkers
        biomarker_hash = get_biomarker_hash(request.biomarker_names)
        
        # Check cache first
        cached_summary = get_cached_summary(profile_id, biomarker_hash, db)
        
        if cached_summary:
            # Return cached summary immediately
            logger.info(f"Returning cached summary for profile {profile_id}, hash {biomarker_hash}")
            return FavoriteSummaryResponse(
                profile_id=profile_id,
                summary_text=cached_summary,
                biomarker_hash=biomarker_hash,
                created_at=datetime.utcnow(), # Indicate cache retrieval time
                from_cache=True
            )
        
        # If not in cache, generate the summary (this calls the LLM service)
        logger.info(f"No cache found for profile {profile_id}, hash {biomarker_hash}. Generating new summary.")
        summary_text = await generate_favorite_biomarker_summary(
            profile_id=profile_id, 
            biomarker_names=request.biomarker_names, 
            db=db
        )
        
        if not summary_text:
            logger.error(f"Failed to generate favorite summary for profile {profile_id}, hash {biomarker_hash}")
            raise HTTPException(status_code=500, detail="Failed to generate summary from LLM service")
        
        # Return the newly generated summary
        return FavoriteSummaryResponse(
            profile_id=profile_id,
            summary_text=summary_text,
            biomarker_hash=biomarker_hash,
            created_at=datetime.utcnow(), # Indicate generation time
            from_cache=False
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions directly
        raise
    except Exception as e:
        logger.error(f"Error in favorite-summary endpoint for profile {profile_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error while processing favorite summary")
