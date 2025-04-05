"""
Profile Matcher Service

This module provides services for matching extracted profile metadata with existing profiles
using fuzzy matching and similarity scoring algorithms.
"""
import logging
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from fuzzywuzzy import fuzz
from app.models.profile_model import Profile
from dateutil import parser
from app.schemas.profile_schema import ProfileMatchScore, ProfileResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set up a file handler
log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, 'profile_matcher.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'))
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)

def preprocess_profile_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Preprocess extracted metadata to standardize format for matching.
    
    Args:
        metadata: Dictionary of extracted metadata
        
    Returns:
        Dictionary with standardized metadata
    """
    processed_metadata = {}
    
    # Process name (convert to lowercase for better matching)
    if metadata.get('patient_name'):
        processed_metadata['patient_name'] = metadata['patient_name'].lower().strip()
    
    # Convert DOB string to datetime if it's a string
    if metadata.get('patient_dob') and isinstance(metadata['patient_dob'], str):
        try:
            # Try different date formats
            for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
                try:
                    dob = datetime.strptime(metadata['patient_dob'], fmt)
                    processed_metadata['patient_dob'] = dob
                    break
                except ValueError:
                    continue
        except Exception as e:
            logger.warning(f"Could not parse DOB: {metadata['patient_dob']} - {str(e)}")
    elif metadata.get('patient_dob'):
        processed_metadata['patient_dob'] = metadata['patient_dob']
    
    # Standardize gender
    if metadata.get('patient_gender'):
        gender = metadata['patient_gender'].lower().strip()
        if gender in ['m', 'male']:
            processed_metadata['patient_gender'] = 'male'
        elif gender in ['f', 'female']:
            processed_metadata['patient_gender'] = 'female'
        else:
            processed_metadata['patient_gender'] = gender
    
    # Copy patient ID if available
    if metadata.get('patient_id'):
        processed_metadata['patient_id'] = metadata['patient_id'].strip()
    
    return processed_metadata

def calculate_profile_match_score(profile: Profile, metadata: Dict[str, Any]) -> float:
    """
    Calculate a match score between a profile and extracted metadata.
    Returns a score between 0 and 1, where 1 is a perfect match.
    
    Args:
        profile: Profile model to compare against
        metadata: Preprocessed metadata extracted from a PDF
        
    Returns:
        Float between 0 and 1 representing match confidence
    """
    total_weight = 0
    weighted_score = 0
    
    # Name matching (highest weight)
    if profile.name and metadata.get('patient_name'):
        weight = 0.5
        total_weight += weight
        name_score = fuzz.token_sort_ratio(profile.name.lower(), metadata['patient_name']) / 100
        weighted_score += weight * name_score
        logger.debug(f"Name match score: {name_score:.2f} for {profile.name} vs {metadata['patient_name']}")
    
    # DOB matching
    if profile.date_of_birth and metadata.get('patient_dob'):
        weight = 0.3
        total_weight += weight
        
        # Direct date comparison
        try:
            if isinstance(metadata['patient_dob'], datetime):
                if profile.date_of_birth.date() == metadata['patient_dob'].date():
                    dob_score = 1.0
                else:
                    dob_score = 0.0
            else:
                dob_score = 0.0
        except Exception as e:
            logger.warning(f"Error comparing DOB: {str(e)}")
            dob_score = 0.0
            
        weighted_score += weight * dob_score
        logger.debug(f"DOB match score: {dob_score:.2f} for {profile.date_of_birth} vs {metadata.get('patient_dob')}")
    
    # Gender matching
    if profile.gender and metadata.get('patient_gender'):
        weight = 0.1
        total_weight += weight
        if profile.gender.lower() == metadata['patient_gender']:
            gender_score = 1.0
        else:
            gender_score = 0.0
        weighted_score += weight * gender_score
        logger.debug(f"Gender match score: {gender_score:.2f} for {profile.gender} vs {metadata['patient_gender']}")
    
    # Patient ID matching (high weight if available)
    if profile.patient_id and metadata.get('patient_id'):
        weight = 0.4
        total_weight += weight
        if profile.patient_id.strip() == metadata['patient_id']:
            patient_id_score = 1.0
        else:
            # Partial matching for patient IDs
            patient_id_score = fuzz.ratio(profile.patient_id.strip(), metadata['patient_id']) / 100
        weighted_score += weight * patient_id_score
        logger.debug(f"Patient ID match score: {patient_id_score:.2f} for {profile.patient_id} vs {metadata['patient_id']}")
    
    # Calculate final score
    if total_weight > 0:
        final_score = weighted_score / total_weight
    else:
        final_score = 0.0
    
    logger.info(f"Profile match score: {final_score:.2f} for profile {profile.id} ({profile.name})")
    return final_score

async def find_matching_profiles(metadata: Dict[str, Any], db: Session, user_id: str = None, threshold: float = 0.6):
    """
    Find profiles that match the extracted metadata with confidence scores.
    
    Args:
        metadata: Extracted metadata from PDF
        db: Database session
        user_id: Optional user ID to filter profiles by
        threshold: Minimum confidence score to include in results (0.0 to 1.0)
        
    Returns:
        List of ProfileMatchScore objects sorted by confidence in descending order
    """
    logger.info(f"Finding matching profiles for metadata: {metadata}")
    
    # Get profiles from database, filtered by user_id if provided
    if user_id:
        profiles = db.query(Profile).filter(Profile.user_id == user_id).all()
        logger.debug(f"Found {len(profiles)} profiles for user {user_id}")
    else:
        profiles = db.query(Profile).all()
        logger.debug(f"Found {len(profiles)} total profiles in database")
    
    # Preprocess metadata
    processed_metadata = preprocess_profile_metadata(metadata)
    logger.debug(f"Preprocessed metadata: {processed_metadata}")
    
    # Calculate match scores for each profile
    profile_scores = []
    for profile in profiles:
        score = calculate_profile_match_score(profile, processed_metadata)
        if score >= threshold:
            # Create a ProfileResponse for this profile
            profile_response = ProfileResponse(
                id=profile.id,
                name=profile.name,
                date_of_birth=profile.date_of_birth,
                gender=profile.gender,
                patient_id=profile.patient_id,
                created_at=profile.created_at,
                last_modified=profile.last_modified,
                favorite_biomarkers=profile.favorite_biomarkers or [],
                user_id=profile.user_id,
                biomarker_count=0,  # These can be populated later if needed
                pdf_count=0
            )
            
            profile_scores.append(ProfileMatchScore(
                profile=profile_response,
                confidence=score
            ))
    
    # Sort by score in descending order
    profile_scores.sort(key=lambda x: x.confidence, reverse=True)
    
    logger.info(f"Found {len(profile_scores)} matching profiles above threshold {threshold}")
    return profile_scores

def create_profile_from_metadata(db: Session, metadata: Dict[str, Any]) -> Optional[Profile]:
    """
    Create a new profile from extracted metadata.
    
    Args:
        db: Database session
        metadata: Extracted metadata dictionary
        
    Returns:
        Profile object or None if creation failed
    """
    logger.info(f"Creating new profile from metadata: {metadata}")
    
    # Extract name or use default
    name = metadata.get('patient_name', 'Unknown Profile')
    if not name or name.strip() == '':
        name = "Default Profile"
        logger.warning("No valid name found in metadata, using default name")
    
    # Extract date of birth if available (might be None)
    date_of_birth = None
    if metadata.get('patient_dob'):
        try:
            # If it's already a datetime, use it directly
            if isinstance(metadata['patient_dob'], datetime):
                date_of_birth = metadata['patient_dob']
            # Otherwise try to parse it
            else:
                date_of_birth = parser.parse(metadata['patient_dob'])
                logger.info(f"Parsed date of birth: {date_of_birth}")
        except Exception as e:
            logger.error(f"Error parsing date of birth: {str(e)}")
    
    # Extract gender
    gender = metadata.get('patient_gender')
    
    # Extract patient ID
    patient_id = metadata.get('patient_id')
    
    try:
        # Create the profile
        profile = Profile(
            name=name,
            date_of_birth=date_of_birth,
            gender=gender,
            patient_id=patient_id
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        logger.info(f"Created new profile: ID={profile.id}, Name={profile.name}")
        return profile
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating profile from metadata: {str(e)}")
        return None 