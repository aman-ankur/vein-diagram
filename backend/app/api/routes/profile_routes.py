"""
API routes for profile management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
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
    # Assuming a simple schema for the order update
    # If not defined elsewhere, add it here or in profile_schema.py
    # class FavoriteOrderUpdate(BaseModel):
    #     ordered_favorites: List[str]
)
from app.services.profile_matcher import find_matching_profiles, create_profile_from_metadata
from app.services.metadata_parser import extract_metadata_with_claude
from pydantic import BaseModel, Field # Import BaseModel and Field if defining schema here
from app.services.health_summary_service import generate_and_update_health_summary

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Schemas specific to favorite operations ---
class AddFavoriteRequest(BaseModel):
    biomarker_name: str = Field(..., description="Name of the biomarker to add to favorites")


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
        # Base query - Select only known/stable columns explicitly
        query = db.query(
            Profile.id,
            Profile.name,
            Profile.date_of_birth,
            Profile.gender,
            Profile.patient_id,
            Profile.created_at,
            Profile.last_modified,
            Profile.favorite_biomarkers
        )

        # Apply search filter if provided (filtering on columns we selected)
        if search:
            search_term = f"%{search}%"
            query = query.filter(Profile.name.ilike(search_term) | Profile.patient_id.ilike(search_term))

        # --- Calculate Total Count Separately ---
        # Construct a separate query specifically for counting, only filtering on necessary columns.
        count_query = db.query(func.count(Profile.id))
        if search:
            # Apply the same filter criteria used in the main query
            count_query = count_query.filter(Profile.name.ilike(search_term) | Profile.patient_id.ilike(search_term))
        total = count_query.scalar()
        # --- End Count Calculation ---

        # Apply pagination and explicitly select only known columns *before* executing .all()
        profile_tuples = query.with_entities(
            Profile.id,
            Profile.name,
            Profile.date_of_birth,
            Profile.gender,
            Profile.patient_id,
            Profile.created_at,
            Profile.last_modified,
            Profile.favorite_biomarkers
        ).offset(skip).limit(limit).all()

        # Prepare response with counts for each profile
        profile_responses = []
        for p_id, p_name, p_dob, p_gender, p_patient_id, p_created_at, p_last_modified, p_favs in profile_tuples:
            biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == p_id).scalar()
            pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == p_id).scalar()

            # Manually construct the response dictionary from the tuple
            # We don't include health_summary here as it wasn't selected
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
                "health_summary": None, # Explicitly set to None as it wasn't queried
                "summary_last_updated": None, # Explicitly set to None
            }
            # Validate data against the schema before appending
            response_item = ProfileResponse(**profile_data)
            profile_responses.append(response_item)
        
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

# New endpoints for profile matching feature

@router.post("/match", response_model=ProfileMatchingResponse)
async def match_profile_from_pdf(
    request: ProfileMatchingRequest,
    db: Session = Depends(get_db)
):
    """
    Extract metadata from a PDF and find matching profiles.
    Returns matching profiles sorted by confidence score along with the extracted metadata.
    """
    logger.info(f"Processing profile matching request for PDF ID: {request.pdf_id}")
    
    # Retrieve the PDF
    pdf = db.query(PDF).filter(PDF.file_id == request.pdf_id).first()
    if not pdf:
        logger.error(f"PDF not found: {request.pdf_id}")
        raise HTTPException(status_code=404, detail="PDF not found")
    
    # Check if PDF has been processed
    if pdf.status != "processed" and pdf.status != "processing":
        logger.error(f"PDF {request.pdf_id} cannot be matched, status: {pdf.status}")
        raise HTTPException(status_code=400, detail=f"PDF is not ready for matching, current status: {pdf.status}")
    
    try:
        # Create metadata dictionary from PDF fields
        metadata: Dict[str, Any] = {
            "patient_name": pdf.patient_name,
            "patient_gender": pdf.patient_gender,
            "patient_id": pdf.patient_id,
            "lab_name": pdf.lab_name,
            "report_date": pdf.report_date
        }
        
        # If metadata is incomplete, try to extract it using Claude
        if not pdf.patient_name or not pdf.patient_gender:
            logger.info(f"Incomplete metadata for PDF {request.pdf_id}, attempting extraction with Claude")
            
            if pdf.extracted_text:
                extracted_metadata = extract_metadata_with_claude(pdf.extracted_text, pdf.filename)
                
                # Update PDF with extracted metadata
                if extracted_metadata:
                    # Update PDF record with extracted metadata
                    if extracted_metadata.get("patient_name") and not pdf.patient_name:
                        pdf.patient_name = extracted_metadata.get("patient_name")
                    if extracted_metadata.get("patient_gender") and not pdf.patient_gender:
                        pdf.patient_gender = extracted_metadata.get("patient_gender")
                    if extracted_metadata.get("patient_id") and not pdf.patient_id:
                        pdf.patient_id = extracted_metadata.get("patient_id")
                    if extracted_metadata.get("lab_name") and not pdf.lab_name:
                        pdf.lab_name = extracted_metadata.get("lab_name")
                    if extracted_metadata.get("report_date") and not pdf.report_date:
                        # Convert string date to datetime object
                        report_date_str = extracted_metadata.get("report_date")
                        try:
                            # Try multiple date formats
                            for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                                try:
                                    pdf.report_date = datetime.strptime(report_date_str, date_format)
                                    logger.info(f"Converted report date '{report_date_str}' to datetime using format {date_format}")
                                    break
                                except ValueError:
                                    continue
                            # If none of the formats worked, log it
                            if isinstance(pdf.report_date, str):
                                logger.warning(f"Could not convert report date '{report_date_str}' to datetime")
                        except Exception as e:
                            logger.warning(f"Error converting report date: {str(e)}")
                    if extracted_metadata.get("patient_dob"):
                        # Convert patient_dob to datetime if it's a string
                        dob_str = extracted_metadata.get("patient_dob")
                        if isinstance(dob_str, str):
                            try:
                                # Try multiple date formats
                                for date_format in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y/%m/%d"]:
                                    try:
                                        metadata["patient_dob"] = datetime.strptime(dob_str, date_format)
                                        logger.info(f"Converted patient DOB '{dob_str}' to datetime using format {date_format}")
                                        break
                                    except ValueError:
                                        continue
                            except Exception as e:
                                logger.warning(f"Error converting patient DOB: {str(e)}")
                        else:
                            metadata["patient_dob"] = dob_str
                    
                    # Save changes
                    db.commit()
                    
                    # Update metadata dictionary with extracted data
                    metadata = {
                        "patient_name": pdf.patient_name,
                        "patient_gender": pdf.patient_gender,
                        "patient_id": pdf.patient_id,
                        "patient_dob": metadata.get("patient_dob"),
                        "lab_name": pdf.lab_name,
                        "report_date": pdf.report_date
                    }
        
        # Find matching profiles
        profile_matches = find_matching_profiles(db, metadata)
        
        # Create response
        profile_match_scores = []
        for profile, score in profile_matches:
            # Get biomarker and PDF counts
            biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == profile.id).scalar()
            pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == profile.id).scalar()
            
            profile_response = ProfileResponse(
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
            
            profile_match_scores.append(ProfileMatchScore(
                profile=profile_response,
                confidence=score
            ))
        
        # Create metadata response
        extracted_metadata = ProfileExtractedMetadata(
            patient_name=metadata.get("patient_name"),
            patient_dob=metadata.get("patient_dob"),
            patient_gender=metadata.get("patient_gender"),
            patient_id=metadata.get("patient_id"),
            lab_name=metadata.get("lab_name"),
            report_date=metadata.get("report_date")
        )
        
        response = ProfileMatchingResponse(
            matches=profile_match_scores,
            metadata=extracted_metadata
        )
        
        logger.info(f"Completed profile matching for PDF {request.pdf_id}, found {len(profile_match_scores)} matches")
        return response
    
    except Exception as e:
        logger.error(f"Error matching profile for PDF {request.pdf_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error matching profile: {str(e)}")

@router.post("/associate", response_model=ProfileResponse)
async def associate_pdf_with_profile(
    request: ProfileAssociationRequest,
    db: Session = Depends(get_db)
):
    """
    Associate a PDF with an existing profile or create a new profile from the PDF metadata.
    """
    logger.info(f"Processing profile association request: {request}")
    
    # Retrieve the PDF
    pdf = db.query(PDF).filter(PDF.file_id == request.pdf_id).first()
    if not pdf:
        logger.error(f"PDF not found: {request.pdf_id}")
        raise HTTPException(status_code=404, detail="PDF not found")
    
    try:
        profile = None
        
        # Case 1: Create a new profile from metadata
        if request.create_new_profile:
            logger.info(f"Creating new profile from PDF {request.pdf_id} metadata")
            
            # Create metadata dictionary from PDF fields with any updates
            metadata = {
                "patient_name": pdf.patient_name,
                "patient_gender": pdf.patient_gender,
                "patient_id": pdf.patient_id,
                "lab_name": pdf.lab_name,
                "report_date": pdf.report_date
            }
            
            # Apply any metadata updates
            if request.metadata_updates:
                logger.info(f"Applying metadata updates: {request.metadata_updates}")
                metadata.update(request.metadata_updates)
            
            # Create the profile
            logger.info(f"Creating profile with metadata: {metadata}")
            profile = create_profile_from_metadata(db, metadata)
            
            if not profile:
                logger.error(f"Failed to create profile from PDF {request.pdf_id} metadata")
                raise HTTPException(status_code=500, detail="Failed to create profile from metadata")
            
            logger.info(f"Successfully created new profile: {profile.id} ({profile.name})")
        
        # Case 2: Use an existing profile
        elif request.profile_id:
            logger.info(f"Associating PDF {request.pdf_id} with existing profile {request.profile_id}")
            
            # Find the profile
            try:
                profile_uuid = UUID(request.profile_id)
                profile = db.query(Profile).filter(Profile.id == profile_uuid).first()
            except ValueError:
                logger.error(f"Invalid profile ID format: {request.profile_id}")
                raise HTTPException(status_code=400, detail="Invalid profile ID format")
            
            if not profile:
                logger.error(f"Profile not found: {request.profile_id}")
                raise HTTPException(status_code=404, detail="Profile not found")
            
            logger.info(f"Found existing profile: {profile.id} ({profile.name})")
        
        # Case 3: No profile specified and not creating a new one
        else:
            logger.error("No profile specified and not creating a new profile")
            raise HTTPException(status_code=400, detail="Must specify either a profile_id or set create_new_profile to true")
        
        # Associate the PDF with the profile
        pdf.profile_id = profile.id
        db.commit()
        logger.info(f"Associated PDF {pdf.id} with profile {profile.id}")
        
        # Associate biomarkers with profile
        biomarkers = db.query(Biomarker).filter(Biomarker.pdf_id == pdf.id).all()
        biomarker_count = len(biomarkers)
        logger.info(f"Found {biomarker_count} biomarkers to associate with profile {profile.id}")
        
        for biomarker in biomarkers:
            biomarker.profile_id = profile.id
        
        db.commit()
        logger.info(f"Associated {biomarker_count} biomarkers with profile {profile.id}")
        
        # Get updated counts
        updated_biomarker_count = db.query(func.count(Biomarker.id)).filter(Biomarker.profile_id == profile.id).scalar()
        pdf_count = db.query(func.count(PDF.id)).filter(PDF.profile_id == profile.id).scalar()
        
        # Create response
        response = ProfileResponse(
            id=profile.id,
            name=profile.name,
            date_of_birth=profile.date_of_birth,
            gender=profile.gender,
            patient_id=profile.patient_id,
            created_at=profile.created_at,
            last_modified=profile.last_modified,
            biomarker_count=updated_biomarker_count,
            pdf_count=pdf_count
        )
        
        logger.info(f"Successfully associated PDF {request.pdf_id} with profile {profile.id}")
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error associating PDF {request.pdf_id} with profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error associating PDF with profile: {str(e)}")


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
