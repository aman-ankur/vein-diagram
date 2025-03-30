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

def find_matching_profiles(db: Session, metadata: Dict[str, Any], threshold: float = 0.6) -> List[Tuple[Profile, float]]:
    """
    Find profiles that match the extracted metadata with confidence scores.
    
    Args:
        db: Database session
        metadata: Extracted metadata from PDF
        threshold: Minimum confidence score to include in results (0.0 to 1.0)
        
    Returns:
        List of tuples containing (Profile, confidence_score) sorted by confidence in descending order
    """
    logger.info(f"Finding matching profiles for metadata: {metadata}")
    
    # Get all profiles from database
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
            profile_scores.append((profile, score))
    
    # Sort by score in descending order
    profile_scores.sort(key=lambda x: x[1], reverse=True)
    
    logger.info(f"Found {len(profile_scores)} matching profiles above threshold {threshold}")
    return profile_scores

def create_profile_from_metadata(db: Session, metadata: Dict[str, Any]) -> Optional[Profile]:
    """
    Create a new profile from extracted metadata.
    
    Args:
        db: Database session
        metadata: Extracted metadata from PDF
        
    Returns:
        Newly created Profile object, or None if creation failed
    """
    try:
        # Preprocess metadata
        processed_metadata = preprocess_profile_metadata(metadata)
        
        # Create profile with available data
        new_profile = Profile(
            name=metadata.get('patient_name', 'Unknown'),
            date_of_birth=processed_metadata.get('patient_dob'),
            gender=processed_metadata.get('patient_gender'),
            patient_id=processed_metadata.get('patient_id')
        )
        
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        
        logger.info(f"Created new profile from metadata: {new_profile.id} ({new_profile.name})")
        return new_profile
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating profile from metadata: {str(e)}")
        return None 