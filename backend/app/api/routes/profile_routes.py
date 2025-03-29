"""
API routes for profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import String  # Add this import
from typing import List, Optional
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
    ProfileList
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=ProfileResponse, status_code=201)
async def create_profile(
    profile: ProfileCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new profile.
    """
    try:
        db_profile = Profile(
            name=profile.name,
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            patient_id=profile.patient_id
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
            pdf_count=pdf_count
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

@router.get("/", response_model=ProfileList)
async def get_profiles(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get all profiles with optional search and pagination.
    """
    try:
        # Base query
        query = db.query(Profile)
        
        # Apply search filter if provided
        if search:
            search_term = f"%{search}%"
            query = query.filter(Profile.name.ilike(search_term) | Profile.patient_id.ilike(search_term))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        profiles = query.offset(skip).limit(limit).all()
        
        # Prepare response with counts for each profile
        profile_responses = []
        for profile in profiles:
            biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == profile.id).scalar()
            pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == profile.id).scalar()
            
            profile_responses.append(
                ProfileResponse(
                    id=profile.id,
                    name=profile.name,
                    date_of_birth=profile.date_of_birth,
                    gender=profile.gender,
                    patient_id=profile.patient_id,
                    created_at=profile.created_at,
                    last_modified=profile.last_modified,
                    biomarker_count=biomarker_count,
                    pdf_count=pdf_count
                )
            )
        
        return ProfileList(profiles=profile_responses, total=total)
    except Exception as e:
        logger.error(f"Error retrieving profiles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{profile_id}", response_model=ProfileResponse)
async def get_profile(
    profile_id: str,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific profile by ID.
    """
    logger.info(f"GET endpoint called for profile ID: {profile_id}")

    try:
        # Simplest approach: convert string to UUID and query directly
        try:
            profile_id_uuid = UUID(profile_id)
            profile = db.query(Profile).filter(Profile.id == profile_id_uuid).first()
        except ValueError as e:
            logger.error(f"Invalid UUID format: {profile_id}")
            raise HTTPException(status_code=400, detail="Invalid profile ID format")
        
        if not profile:
            # Manually check all profiles as a fallback
            all_profiles = db.query(Profile).all()
            for p in all_profiles:
                if str(p.id).lower() == profile_id.lower():
                    profile = p
                    logger.info(f"Found profile through manual comparison")
                    break
                    
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        # Get counts
        biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == profile.id).scalar()
        pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == profile.id).scalar()
        
        return ProfileResponse(
            id=profile.id,
            name=profile.name,
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            patient_id=profile.patient_id,
            created_at=profile.created_at,
            last_modified=profile.last_modified,
            biomarker_count=biomarker_count,
            pdf_count=pdf_count
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving profile {profile_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.put("/{profile_id}", response_model=ProfileResponse)
async def update_profile(
    profile_id: UUID,
    profile_update: ProfileUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing profile.
    """
    logger.info(f"PUT endpoint called for profile ID: {profile_id}")
    
    try:
        # Simplest approach: convert string to UUID and query directly
        try:
            profile_id_uuid = UUID(profile_id)
            db_profile = db.query(Profile).filter(Profile.id == profile_id_uuid).first()
        except ValueError as e:
            logger.error(f"Invalid UUID format: {profile_id}")
            raise HTTPException(status_code=400, detail="Invalid profile ID format")
        
        if not db_profile:
            # Manually check all profiles as a fallback
            all_profiles = db.query(Profile).all()
            for p in all_profiles:
                if str(p.id).lower() == profile_id.lower():
                    db_profile = p
                    logger.info(f"Found profile through manual comparison")
                    break
                    
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
            pdf_count=pdf_count
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
    db: Session = Depends(get_db)
):
    """
    Delete a profile. 
    Note: This will not delete associated biomarkers or PDFs but will unlink them.
    """
    # Strip any whitespace that might be in the ID
    profile_id = profile_id.strip()
    logger.info(f"DELETE endpoint called for profile ID: '{profile_id}'")
    
    try:
        # Get all profiles before deletion for debugging
        all_profiles_before = db.query(Profile).all()
        logger.info(f"Total profiles before deletion: {len(all_profiles_before)}")
        logger.info(f"Profile IDs before deletion: {[str(p.id) for p in all_profiles_before]}")
        
        # Convert string to UUID
        try:
            profile_id_uuid = UUID(profile_id)
            logger.info(f"Converted input to UUID: {profile_id_uuid}")
        except ValueError as e:
            logger.error(f"Invalid UUID format: '{profile_id}'")
            raise HTTPException(status_code=400, detail=f"Invalid profile ID format: {str(e)}")
        
        # Find the profile
        db_profile = db.query(Profile).filter(Profile.id == profile_id_uuid).first()
        
        if not db_profile:
            logger.warning(f"Profile with ID '{profile_id}' not found")
            raise HTTPException(status_code=404, detail="Profile not found")
        
        logger.info(f"Found profile to delete: {db_profile.name} (ID: {db_profile.id})")
        
        # Unlink biomarkers and PDFs
        biomarker_count = db.query(Biomarker).filter(Biomarker.profile_id == db_profile.id).count()
        pdf_count = db.query(PDF).filter(PDF.profile_id == db_profile.id).count()
        
        logger.info(f"Unlinking {biomarker_count} biomarkers and {pdf_count} PDFs")
        
        db.query(Biomarker).filter(Biomarker.profile_id == db_profile.id).update({"profile_id": None})
        db.query(PDF).filter(PDF.profile_id == db_profile.id).update({"profile_id": None})
        
        # Store profile ID for verification
        profile_id_to_check = db_profile.id
        
        # Delete the profile
        logger.info(f"Executing db.delete on profile {db_profile.id}")
        db.delete(db_profile)
        
        # Flush changes to DB before commit to catch any issues
        logger.info("Flushing database session...")
        db.flush()
        
        # Commit the transaction
        logger.info("Committing transaction...")
        db.commit()
        
        # Verify deletion by checking if profile still exists
        logger.info(f"Verifying deletion of profile {profile_id_to_check}...")
        verification_check = db.query(Profile).filter(Profile.id == profile_id_to_check).first()
        
        if verification_check:
            logger.error(f"DELETION FAILED! Profile {profile_id_to_check} still exists after deletion and commit!")
            # Force another deletion attempt
            logger.info("Attempting forced deletion...")
            db.delete(verification_check)
            db.commit()
            
            # Check again
            second_verification = db.query(Profile).filter(Profile.id == profile_id_to_check).first()
            if second_verification:
                logger.error("CRITICAL: Second deletion attempt failed!")
            else:
                logger.info("Second deletion attempt successful")
        else:
            logger.info(f"Verification successful - Profile {profile_id_to_check} no longer exists in database")
        
        # Get all profiles after deletion for debugging
        all_profiles_after = db.query(Profile).all()
        logger.info(f"Total profiles after deletion: {len(all_profiles_after)}")
        logger.info(f"Profile IDs after deletion: {[str(p.id) for p in all_profiles_after]}")
        
        logger.info(f"Successfully completed delete operation for profile {profile_id}")
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting profile {profile_id}: {str(e)}")
        logger.exception("Full exception details:")
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