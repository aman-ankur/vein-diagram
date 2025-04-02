"""
Service for generating and managing LLM-based health summaries for user profiles.
"""
import logging
from typing import Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc
from datetime import datetime
import uuid

from app.models.profile_model import Profile
from app.models.biomarker_model import Biomarker
from app.services import llm_service # Assuming llm_service has the function to call Claude

logger = logging.getLogger(__name__)

def format_biomarker_history(biomarkers: List[Biomarker]) -> str:
    """Formats biomarker history for the LLM prompt."""
    if not biomarkers:
        return "No biomarker history available."

    formatted_lines = ["Biomarker History (most recent first):"]
    for bm in biomarkers:
        date_str = bm.extracted_date.strftime('%Y-%m-%d') if bm.extracted_date else 'Unknown Date'
        value_str = f"{bm.value} {bm.unit}" if bm.unit else str(bm.value)
        range_str = f"(Ref: {bm.reference_range_text})" if bm.reference_range_text else ""
        formatted_lines.append(f"- {date_str}: {bm.name} = {value_str} {range_str}")

    return "\n".join(formatted_lines)

async def generate_health_summary(profile_id: uuid.UUID, db: Session) -> Optional[str]:
    """
    Generates a health summary for a given profile using the LLM.
    """
    try:
        # Fetch profile and all associated biomarkers, ordered by date descending
        stmt = (
            select(Biomarker)
            .where(Biomarker.profile_id == profile_id)
            .order_by(desc(Biomarker.extracted_date))
        )
        result = db.execute(stmt)
        biomarkers = result.scalars().all()

        if not biomarkers:
            logger.info(f"No biomarkers found for profile {profile_id}. Cannot generate summary.")
            return None

        biomarker_history_text = format_biomarker_history(biomarkers)

        # Construct the prompt for the LLM
        # TODO: Refine this prompt significantly based on testing and desired output style.
        prompt = f"""
Analyze the following biomarker history for a user profile. Identify key biomarkers, significant trends, abnormalities, and changes over time. Provide a concise, insightful narrative summary (2-3 paragraphs) of the user's general health state based *only* on this data.

Focus on:
- Notable high or low values compared to reference ranges (if available).
- Significant upward or downward trends for important markers.
- Potential relationships or patterns suggested by the data.
- Overall assessment based *strictly* on the provided numbers and trends.

**IMPORTANT: Do NOT provide any medical advice, diagnoses, or treatment recommendations. Stick strictly to summarizing the provided data and observed trends.**

Biomarker Data:
{biomarker_history_text}

Generate the health summary now:
"""

        # Call the LLM service (assuming a function like this exists)
        # Replace 'get_llm_response' with the actual function name in llm_service.py
        summary = await llm_service.get_llm_response(prompt) # Make sure llm_service.get_llm_response is async or adjust call

        if summary:
            logger.info(f"Successfully generated health summary for profile {profile_id}")
            return summary.strip()
        else:
            logger.warning(f"LLM service returned no summary for profile {profile_id}")
            return None

    except Exception as e:
        logger.error(f"Error generating health summary for profile {profile_id}: {e}", exc_info=True)
        return None

async def generate_and_update_health_summary(profile_id: uuid.UUID, db: Session):
    """
    Generates a health summary and updates the profile record in the database.
    """
    logger.info(f"Attempting to generate and update health summary for profile {profile_id}")
    summary_text = await generate_health_summary(profile_id, db)

    if summary_text:
        try:
            # Fetch the profile to update
            profile = db.get(Profile, profile_id)
            if profile:
                # Uncomment and enable writing the summary to the profile
                profile.health_summary = summary_text
                profile.summary_last_updated = datetime.utcnow()
                db.commit()
                logger.info(f"Successfully updated health summary for profile {profile_id}")
            else:
                logger.error(f"Profile {profile_id} not found for updating health summary.")
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating profile {profile_id} with health summary: {e}", exc_info=True)
    else:
        logger.warning(f"No summary generated for profile {profile_id}, skipping update.")
