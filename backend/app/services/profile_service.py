"""
Service layer for profile-related business logic.
"""
import logging
from typing import List, Dict, Tuple
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, select, delete, update
from fastapi import HTTPException

from app.models.profile_model import Profile
from app.models.biomarker_model import Biomarker
from app.models.pdf_model import PDF
from app.schemas.profile_schema import ProfileMergeRequest

logger = logging.getLogger(__name__)

def merge_profiles(db: Session, merge_request: ProfileMergeRequest):
    """
    Merges source profiles into a target profile.

    Steps:
    1. Validate source and target profiles exist and are distinct.
    2. Re-associate Biomarkers and PDFs from source profiles to the target profile.
    3. Identify and delete duplicate Biomarkers within the target profile based on
       name, value, unit, and report_date.
    4. Delete the source profiles.
    All operations are performed within a single transaction.
    """
    source_ids = merge_request.source_profile_ids
    target_id = merge_request.target_profile_id

    if target_id in source_ids:
        raise HTTPException(status_code=400, detail="Target profile cannot be one of the source profiles.")

    try:
        # Start transaction
        with db.begin_nested(): # Use nested transaction to manage within the function

            # 1. Validation
            logger.info(f"Validating profiles: Target={target_id}, Sources={source_ids}")
            target_profile = db.query(Profile).filter(Profile.id == target_id).first()
            if not target_profile:
                raise HTTPException(status_code=404, detail=f"Target profile {target_id} not found.")

            source_profiles = db.query(Profile).filter(Profile.id.in_(source_ids)).all()
            if len(source_profiles) != len(source_ids):
                found_ids = {p.id for p in source_profiles}
                missing_ids = set(source_ids) - found_ids
                raise HTTPException(status_code=404, detail=f"Source profiles not found: {missing_ids}")

            logger.info("Validation successful.")

            # --- Metadata Handling (Optional Enhancement) ---
            # Decide which profile's metadata (name, dob, gender, favorites) to keep.
            # Default: Keep target profile's metadata.
            # If needed, add logic here to merge favorites or update target metadata based on request.
            # Example: Merge favorite lists and deduplicate
            # combined_favorites = list(target_profile.favorite_biomarkers or [])
            # for sp in source_profiles:
            #     combined_favorites.extend(sp.favorite_biomarkers or [])
            # target_profile.favorite_biomarkers = list(dict.fromkeys(combined_favorites)) # Deduplicate while preserving order

            # 2. Re-association
            logger.info(f"Re-associating data from sources {source_ids} to target {target_id}")
            
            # Update Biomarkers
            biomarker_update_stmt = (
                update(Biomarker)
                .where(Biomarker.profile_id.in_(source_ids))
                .values(profile_id=target_id)
            )
            biomarker_update_result = db.execute(biomarker_update_stmt)
            logger.info(f"Updated {biomarker_update_result.rowcount} biomarker records.")

            # Update PDFs
            pdf_update_stmt = (
                update(PDF)
                .where(PDF.profile_id.in_(source_ids))
                .values(profile_id=target_id)
            )
            pdf_update_result = db.execute(pdf_update_stmt)
            logger.info(f"Updated {pdf_update_result.rowcount} PDF records.")

            # 3. Deduplication
            logger.info(f"Starting deduplication for target profile {target_id}")
            
            # Query all biomarkers for the target profile, joining with PDF to get report_date
            biomarkers_to_check = (
                db.query(Biomarker.id, Biomarker.name, Biomarker.value, Biomarker.unit, PDF.report_date)
                .join(PDF, Biomarker.pdf_id == PDF.id)
                .filter(Biomarker.profile_id == target_id)
                .order_by(Biomarker.name, PDF.report_date, Biomarker.id) # Order for consistent duplicate selection
                .all()
            )

            duplicates_to_delete = set()
            seen_biomarkers: Dict[Tuple[str, float, str, datetime], int] = {} # Key: (name, value, unit, report_date), Value: biomarker_id to keep

            for b_id, b_name, b_value, b_unit, pdf_report_date in biomarkers_to_check:
                # Ensure value is float for consistent keying, handle None values
                key_value = float(b_value) if b_value is not None else None
                key_date = pdf_report_date if pdf_report_date else None # Use None if date is missing

                # Skip if essential parts of the key are missing
                if b_name is None or key_value is None or b_unit is None or key_date is None:
                    logger.debug(f"Skipping biomarker {b_id} due to missing key components: name={b_name}, value={key_value}, unit={b_unit}, date={key_date}")
                    continue

                biomarker_key = (b_name, key_value, b_unit, key_date)

                if biomarker_key in seen_biomarkers:
                    # This is a duplicate, mark for deletion
                    duplicates_to_delete.add(b_id)
                    logger.debug(f"Marking biomarker {b_id} as duplicate of {seen_biomarkers[biomarker_key]} for key {biomarker_key}")
                else:
                    # First time seeing this combination, keep this one
                    seen_biomarkers[biomarker_key] = b_id
                    logger.debug(f"Keeping biomarker {b_id} for key {biomarker_key}")

            if duplicates_to_delete:
                logger.info(f"Identified {len(duplicates_to_delete)} duplicate biomarker entries to delete.")
                delete_stmt = delete(Biomarker).where(Biomarker.id.in_(list(duplicates_to_delete)))
                delete_result = db.execute(delete_stmt)
                logger.info(f"Deleted {delete_result.rowcount} duplicate biomarker records.")
            else:
                logger.info("No duplicate biomarkers found.")

            # 4. Delete Source Profiles
            logger.info(f"Deleting source profiles: {source_ids}")
            delete_profile_stmt = delete(Profile).where(Profile.id.in_(source_ids))
            delete_profile_result = db.execute(delete_profile_stmt)
            logger.info(f"Deleted {delete_profile_result.rowcount} source profile records.")

            # Commit is handled by the caller's context manager (or db.commit() if not nested)
            logger.info("Profile merge transaction steps completed successfully within nested block.")

    except HTTPException as http_exc:
        logger.error(f"HTTP Exception during profile merge: {http_exc.detail}")
        # No need to rollback here, caller's transaction context will handle it
        raise http_exc # Re-raise the HTTP exception
    except Exception as e:
        logger.error(f"Unexpected error during profile merge: {str(e)}", exc_info=True)
        # No need to rollback here, caller's transaction context will handle it
        # Raise a generic 500 error
        raise HTTPException(status_code=500, detail=f"Internal server error during profile merge: {str(e)}")

# --- Other potential profile service functions can be added here ---
# e.g., get_profile_details, update_profile_metadata, etc.
