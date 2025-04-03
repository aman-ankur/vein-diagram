"""
Service for generating and managing LLM-based health summaries for user profiles.
"""
import logging
from typing import Optional, List, Dict, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc, func
from datetime import datetime, timedelta
import uuid
import itertools
from collections import defaultdict

from app.models.profile_model import Profile
from app.models.biomarker_model import Biomarker
from app.services import llm_service

logger = logging.getLogger(__name__)

def calculate_trends(biomarkers_by_name: Dict[str, List[Biomarker]]) -> Dict[str, Dict[str, any]]:
    """
    Analyze trends for each biomarker type.
    Returns a dictionary with trend information for each biomarker.
    """
    trends = {}
    
    for name, markers in biomarkers_by_name.items():
        if len(markers) < 2:
            continue
            
        # Sort by date (oldest to newest)
        sorted_markers = sorted(markers, key=lambda x: x.extracted_date if x.extracted_date else datetime.min)
        
        # Get first and last values
        first = sorted_markers[0]
        last = sorted_markers[-1]
        
        # Calculate percent change
        if first.value and first.value != 0:
            percent_change = ((last.value - first.value) / abs(first.value)) * 100
        else:
            percent_change = 0
            
        # Determine direction
        direction = "stable"
        if percent_change > 5:
            direction = "increasing"
        elif percent_change < -5:
            direction = "decreasing"
            
        # Determine if the change is positive (e.g., HDL increasing is good)
        is_positive_change = False
        
        # Simple logic for common markers (this could be expanded with a comprehensive database)
        if name.lower() == "hdl cholesterol" and direction == "increasing":
            is_positive_change = True
        elif name.lower() == "ldl cholesterol" and direction == "decreasing":
            is_positive_change = True
        elif name.lower() == "triglycerides" and direction == "decreasing":
            is_positive_change = True
        elif name.lower() == "total cholesterol" and direction == "decreasing":
            is_positive_change = True
        elif name.lower() == "glucose" and direction == "stable":
            is_positive_change = True
        
        # Store trend information
        trends[name] = {
            "first_value": first.value,
            "first_date": first.extracted_date,
            "last_value": last.value,
            "last_date": last.extracted_date,
            "percent_change": percent_change,
            "direction": direction,
            "is_positive_change": is_positive_change,
            "measurement_count": len(sorted_markers),
            "unit": last.unit
        }
    
    return trends

def format_biomarker_history(biomarkers: List[Biomarker], profile: Profile) -> Tuple[str, Dict]:
    """
    Formats biomarker history for the LLM prompt and extracts trend information.
    Returns formatted text and trend analysis dictionary.
    """
    if not biomarkers:
        return "No biomarker history available.", {}

    # Group biomarkers by name
    biomarkers_by_name = defaultdict(list)
    for bm in biomarkers:
        biomarkers_by_name[bm.name].append(bm)
    
    # Calculate trends
    trends = calculate_trends(biomarkers_by_name)
    
    # Format the biomarker history
    sections = []
    
    # User Profile Section
    profile_section = ["User Profile:"]
    profile_section.append(f"Name: {profile.name}")
    if profile.date_of_birth:
        age = (datetime.utcnow() - profile.date_of_birth).days // 365
        profile_section.append(f"Age: Approximately {age} years")
    if profile.gender:
        profile_section.append(f"Gender: {profile.gender}")
    
    sections.append("\n".join(profile_section))
    
    # Recent Biomarkers Section
    recent_section = ["Recent Biomarker Values:"]
    
    # Get the most recent date
    most_recent_date = max((bm.extracted_date for bm in biomarkers if bm.extracted_date), default=None)
    
    if most_recent_date:
        # Consider biomarkers from the most recent test date
        recent_biomarkers = [bm for bm in biomarkers if bm.extracted_date and 
                            (most_recent_date - bm.extracted_date).days <= 7]
        
        for bm in recent_biomarkers:
            date_str = bm.extracted_date.strftime('%Y-%m-%d') if bm.extracted_date else 'Unknown Date'
            value_str = f"{bm.value} {bm.unit}" if bm.unit else str(bm.value)
            
            # Add reference range and abnormal status
            range_str = ""
            if bm.reference_range_text:
                range_str = f"(Ref: {bm.reference_range_text})"
            
            status_str = ""
            if bm.is_abnormal:
                if bm.reference_range_high is not None and bm.value > bm.reference_range_high:
                    status_str = " [HIGH]"
                elif bm.reference_range_low is not None and bm.value < bm.reference_range_low:
                    status_str = " [LOW]"
                else:
                    status_str = " [ABNORMAL]"
            
            recent_section.append(f"- {bm.name} = {value_str} {range_str}{status_str}")
    
    sections.append("\n".join(recent_section))
    
    # Historical Trends Section
    if trends:
        trends_section = ["Historical Trends:"]
        
        for name, trend_data in trends.items():
            if trend_data["measurement_count"] >= 2:
                first_date = trend_data["first_date"].strftime('%Y-%m-%d') if trend_data["first_date"] else "Unknown"
                last_date = trend_data["last_date"].strftime('%Y-%m-%d') if trend_data["last_date"] else "Unknown"
                
                change_str = f"{abs(trend_data['percent_change']):.1f}% {trend_data['direction']}"
                value_change = f"{trend_data['first_value']} → {trend_data['last_value']} {trend_data['unit']}"
                
                trends_section.append(f"- {name}: {value_change} ({change_str} from {first_date} to {last_date}, {trend_data['measurement_count']} measurements)")
        
        sections.append("\n".join(trends_section))
    
    # Complete Biomarker History
    history_section = ["Complete Biomarker History (chronological order):"]
    
    # Group by date
    biomarkers_by_date = defaultdict(list)
    for bm in biomarkers:
        date_key = bm.extracted_date.strftime('%Y-%m-%d') if bm.extracted_date else 'Unknown Date'
        biomarkers_by_date[date_key].append(bm)
    
    # Sort dates (newest to oldest)
    for date_str in sorted(biomarkers_by_date.keys(), reverse=True):
        history_section.append(f"\n{date_str}:")
        
        # Sort biomarkers alphabetically within each date
        for bm in sorted(biomarkers_by_date[date_str], key=lambda x: x.name):
            value_str = f"{bm.value} {bm.unit}" if bm.unit else str(bm.value)
            range_str = f"(Ref: {bm.reference_range_text})" if bm.reference_range_text else ""
            
            status_str = ""
            if bm.is_abnormal:
                if bm.reference_range_high is not None and bm.value > bm.reference_range_high:
                    status_str = " [HIGH]"
                elif bm.reference_range_low is not None and bm.value < bm.reference_range_low:
                    status_str = " [LOW]"
                else:
                    status_str = " [ABNORMAL]"
            
            history_section.append(f"  - {bm.name} = {value_str} {range_str}{status_str}")
    
    sections.append("\n".join(history_section))
    
    # Return the formatted biomarker history and trend information
    return "\n\n".join(sections), trends

async def generate_health_summary(profile_id: uuid.UUID, db: Session) -> Optional[str]:
    """
    Generates a health summary for a given profile using the LLM.
    """
    try:
        # Fetch profile
        profile = db.get(Profile, profile_id)
        if not profile:
            logger.error(f"Profile {profile_id} not found.")
            return None
            
        # Fetch biomarkers, ordered by date descending
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

        biomarker_history_text, trends = format_biomarker_history(biomarkers, profile)
        
        # Calculate positive trends to highlight
        positive_trends = {name: data for name, data in trends.items() 
                          if data.get("is_positive_change") and data.get("measurement_count", 0) >= 2}
        
        # Get favorite biomarkers if available
        favorite_biomarkers = profile.favorite_biomarkers if profile.favorite_biomarkers else []
        
        # Count abnormal biomarkers
        abnormal_count = sum(1 for bm in biomarkers if bm.is_abnormal and 
                            bm.extracted_date >= datetime.utcnow() - timedelta(days=30))
        
        # Construct the prompt for the LLM
        prompt = f"""You are a knowledgeable and empathetic health monitoring assistant. Create a personalized smart health summary based on the user's biomarker data.

YOUR TASK:
Create a personalized, insightful, and action-oriented health summary that highlights important patterns in the user's biomarker data.

USER INFORMATION:
{profile.name} has {len(biomarkers)} biomarker measurements, with {abnormal_count} abnormal values in the last 30 days.
{'They have marked these biomarkers as favorites: ' + ', '.join(favorite_biomarkers) if favorite_biomarkers else 'They have not marked any biomarkers as favorites yet.'}

STRUCTURE YOUR RESPONSE IN THIS EXACT ORDER:

1. KEY INSIGHTS (with 💡 emoji):
- Start with the most critical findings about abnormal values and concerning patterns
- Include specific numbers and reference ranges
- Explain potential implications in simple terms
- Focus on cholesterol, triglycerides, and other key metabolic markers
- Each point should be a complete thought with context

2. POSITIVE DEVELOPMENTS (with 📈 emoji):
- Highlight improvements in biomarker values
- Include specific percentage changes and timeframes
- Focus on meaningful improvements, not minor fluctuations
- Connect improvements to overall health context

3. AREAS TO MONITOR (with 👀 emoji):
- Identify trends or values that need attention
- Frame concerns constructively without causing alarm
- Focus on actionable observations
- Include context about why these areas matter

WRITING STYLE:
- Write in complete, well-formed sentences
- Use professional but accessible language
- Include specific numbers and percentages
- Make logical connections between related markers
- Keep medical terms to a minimum, explain when used
- Use "you" and "your" to make it personal
- Each bullet point should be a complete thought
- Maintain a calm, professional tone

FORMAT REQUIREMENTS:
- Start each section *directly* with its emoji (💡, 📈, 👀) on a new line. NO text like 'KEY INSIGHTS:' should follow the emoji on the same line.
- Start each point *within* a section on a new line, beginning with the '•' character followed by a space.
- Adhere strictly to this format: EMOJI\n• Point\n• Point\nEMOJI\n• Point...
- No greetings or conclusions.
- No duplicate information.
- No medical advice or treatment suggestions.
- Keep sections distinct and organized.

BIOMARKER DATA:
{biomarker_history_text}

Now, create the personalized health summary:
"""

        # Call the LLM service
        summary = await llm_service.get_llm_response(prompt, model="claude-3-sonnet-20240229", max_tokens=1500)

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
