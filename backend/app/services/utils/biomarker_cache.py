"""
Biomarker Caching System

This module provides intelligent caching for common biomarkers to reduce LLM API calls
by using pattern matching for frequently encountered biomarkers.
"""

import re
import json
import logging
import os
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from threading import Lock
import statistics

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class BiomarkerPattern:
    """Represents a cached biomarker pattern."""
    name: str
    standardized_name: str
    common_units: List[str]
    typical_ranges: Dict[str, Dict[str, float]]  # {unit: {low: float, high: float}}
    pattern_variations: List[str]  # Different ways the name appears
    confidence_threshold: float
    last_seen: str
    frequency_count: int = 0
    success_rate: float = 0.95  # How often this pattern works


@dataclass
class CacheStatistics:
    """Cache performance statistics."""
    total_extractions: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    llm_calls_saved: int = 0
    false_positives: int = 0
    cache_hit_rate: float = 0.0
    average_confidence: float = 0.0
    last_updated: str = ""


class BiomarkerCache:
    """
    Intelligent biomarker caching system for reducing LLM API calls.
    """
    
    def __init__(self, cache_file: str = None, max_cache_size: int = 500):
        """
        Initialize biomarker cache.
        
        Args:
            cache_file: Path to cache file (default: auto-generated)
            max_cache_size: Maximum number of cached biomarkers
        """
        self.max_cache_size = max_cache_size
        self.cache_lock = Lock()
        
        # Set up cache file path
        if cache_file is None:
            cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'cache')
            os.makedirs(cache_dir, exist_ok=True)
            self.cache_file = os.path.join(cache_dir, 'biomarker_cache.json')
        else:
            self.cache_file = cache_file
        
        # Initialize cache and statistics
        self.biomarker_patterns: Dict[str, BiomarkerPattern] = {}
        self.statistics = CacheStatistics()
        
        # Load existing cache
        self.load_cache()
        
        # Initialize common biomarkers if cache is empty
        if not self.biomarker_patterns:
            self._initialize_common_biomarkers()
            self.save_cache()
    
    def _initialize_common_biomarkers(self) -> None:
        """Initialize cache with most common biomarkers."""
        logger.info("🔄 Initializing biomarker cache with common patterns")
        
        common_biomarkers = [
            {
                "name": "glucose",
                "standardized_name": "Glucose",
                "common_units": ["mg/dL", "mg/dl", "mmol/L", "mmol/l"],
                "typical_ranges": {
                    "mg/dL": {"low": 70, "high": 99},
                    "mg/dl": {"low": 70, "high": 99},
                    "mmol/L": {"low": 3.9, "high": 5.5},
                    "mmol/l": {"low": 3.9, "high": 5.5}
                },
                "pattern_variations": [
                    "glucose", "blood glucose", "fasting glucose", "random glucose",
                    "glucose fasting", "glucose random", "glu"
                ],
                "confidence_threshold": 0.9
            },
            {
                "name": "cholesterol",
                "standardized_name": "Total Cholesterol", 
                "common_units": ["mg/dL", "mg/dl", "mmol/L", "mmol/l"],
                "typical_ranges": {
                    "mg/dL": {"low": 0, "high": 200},
                    "mg/dl": {"low": 0, "high": 200},
                    "mmol/L": {"low": 0, "high": 5.2},
                    "mmol/l": {"low": 0, "high": 5.2}
                },
                "pattern_variations": [
                    "cholesterol", "total cholesterol", "chol", "cholest", "tc"
                ],
                "confidence_threshold": 0.9
            },
            {
                "name": "hemoglobin",
                "standardized_name": "Hemoglobin",
                "common_units": ["g/dL", "g/dl", "g/L", "g/l"],
                "typical_ranges": {
                    "g/dL": {"low": 12.0, "high": 17.0},
                    "g/dl": {"low": 12.0, "high": 17.0},
                    "g/L": {"low": 120, "high": 170},
                    "g/l": {"low": 120, "high": 170}
                },
                "pattern_variations": [
                    "hemoglobin", "haemoglobin", "hb", "hgb", "hemoglobin hb"
                ],
                "confidence_threshold": 0.95
            },
            {
                "name": "hematocrit",
                "standardized_name": "Hematocrit",
                "common_units": ["%", "percent", "ratio"],
                "typical_ranges": {
                    "%": {"low": 36, "high": 50},
                    "percent": {"low": 36, "high": 50},
                    "ratio": {"low": 0.36, "high": 0.50}
                },
                "pattern_variations": [
                    "hematocrit", "haematocrit", "hct", "hct%", "packed cell volume", "pcv"
                ],
                "confidence_threshold": 0.9
            },
            {
                "name": "hdl_cholesterol",
                "standardized_name": "HDL Cholesterol",
                "common_units": ["mg/dL", "mg/dl", "mmol/L", "mmol/l"],
                "typical_ranges": {
                    "mg/dL": {"low": 40, "high": 200},
                    "mg/dl": {"low": 40, "high": 200},
                    "mmol/L": {"low": 1.0, "high": 5.2},
                    "mmol/l": {"low": 1.0, "high": 5.2}
                },
                "pattern_variations": [
                    "hdl", "hdl cholesterol", "hdl-c", "hdl chol", "high density lipoprotein"
                ],
                "confidence_threshold": 0.9
            },
            {
                "name": "ldl_cholesterol",
                "standardized_name": "LDL Cholesterol",
                "common_units": ["mg/dL", "mg/dl", "mmol/L", "mmol/l"],
                "typical_ranges": {
                    "mg/dL": {"low": 0, "high": 100},
                    "mg/dl": {"low": 0, "high": 100},
                    "mmol/L": {"low": 0, "high": 2.6},
                    "mmol/l": {"low": 0, "high": 2.6}
                },
                "pattern_variations": [
                    "ldl", "ldl cholesterol", "ldl-c", "ldl chol", "low density lipoprotein"
                ],
                "confidence_threshold": 0.9
            },
            {
                "name": "triglycerides",
                "standardized_name": "Triglycerides",
                "common_units": ["mg/dL", "mg/dl", "mmol/L", "mmol/l"],
                "typical_ranges": {
                    "mg/dL": {"low": 0, "high": 150},
                    "mg/dl": {"low": 0, "high": 150},
                    "mmol/L": {"low": 0, "high": 1.7},
                    "mmol/l": {"low": 0, "high": 1.7}
                },
                "pattern_variations": [
                    "triglycerides", "tg", "trigs", "triglyceride"
                ],
                "confidence_threshold": 0.9
            },
            {
                "name": "creatinine", 
                "standardized_name": "Creatinine",
                "common_units": ["mg/dL", "mg/dl", "μmol/L", "umol/L", "umol/l"],
                "typical_ranges": {
                    "mg/dL": {"low": 0.6, "high": 1.2},
                    "mg/dl": {"low": 0.6, "high": 1.2},
                    "μmol/L": {"low": 53, "high": 106},
                    "umol/L": {"low": 53, "high": 106},
                    "umol/l": {"low": 53, "high": 106}
                },
                "pattern_variations": [
                    "creatinine", "creat", "cr", "serum creatinine"
                ],
                "confidence_threshold": 0.9
            }
        ]
        
        for biomarker_data in common_biomarkers:
            pattern = BiomarkerPattern(
                name=biomarker_data["name"],
                standardized_name=biomarker_data["standardized_name"],
                common_units=biomarker_data["common_units"],
                typical_ranges=biomarker_data["typical_ranges"],
                pattern_variations=biomarker_data["pattern_variations"],
                confidence_threshold=biomarker_data["confidence_threshold"],
                last_seen=datetime.now().isoformat(),
                frequency_count=1
            )
            self.biomarker_patterns[biomarker_data["name"]] = pattern
        
        logger.info(f"✅ Initialized cache with {len(self.biomarker_patterns)} common biomarkers")
    
    def extract_cached_biomarkers(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract biomarkers using cached patterns (fast, no LLM calls).
        
        Args:
            text: Text content to extract biomarkers from
            
        Returns:
            List of extracted biomarkers found using cache
        """
        with self.cache_lock:
            self.statistics.total_extractions += 1
            
        extracted_biomarkers = []
        
        for cache_key, pattern in self.biomarker_patterns.items():
            biomarkers = self._extract_biomarker_with_pattern(text, pattern)
            extracted_biomarkers.extend(biomarkers)
            
            if biomarkers:
                with self.cache_lock:
                    self.statistics.cache_hits += 1
                    pattern.frequency_count += 1
                    pattern.last_seen = datetime.now().isoformat()
        
        # Update statistics
        if extracted_biomarkers:
            with self.cache_lock:
                self.statistics.llm_calls_saved += 1
                avg_confidence = sum(b.get("confidence", 0) for b in extracted_biomarkers) / len(extracted_biomarkers)
                self.statistics.average_confidence = (
                    (self.statistics.average_confidence * (self.statistics.cache_hits - len(extracted_biomarkers)) + 
                     avg_confidence * len(extracted_biomarkers)) / self.statistics.cache_hits
                ) if self.statistics.cache_hits > 0 else avg_confidence
        else:
            with self.cache_lock:
                self.statistics.cache_misses += 1
        
        # Update cache hit rate
        with self.cache_lock:
            if self.statistics.total_extractions > 0:
                self.statistics.cache_hit_rate = self.statistics.cache_hits / self.statistics.total_extractions
        
        return extracted_biomarkers
    
    def _extract_biomarker_with_pattern(self, text: str, pattern: BiomarkerPattern) -> List[Dict[str, Any]]:
        """Extract a specific biomarker using its cached pattern."""
        biomarkers = []
        
        # Create comprehensive regex patterns for this biomarker
        for variation in pattern.pattern_variations:
            # Pattern: biomarker_name followed by value and unit
            for unit in pattern.common_units:
                # Escape special regex characters in unit
                escaped_unit = re.escape(unit)
                escaped_variation = re.escape(variation)
                
                # Multiple pattern formats with improved flexibility
                patterns = [
                    # "Glucose: 105 mg/dL" or "Glucose 105 mg/dL" 
                    rf"\b{escaped_variation}\s*:?\s*(\d+(?:\.\d+)?)\s*{escaped_unit}\b",
                    
                    # "Glucose (Fasting): 105 mg/dL" - handles parenthetical text
                    rf"\b{escaped_variation}\s*\([^)]*\)\s*:?\s*(\d+(?:\.\d+)?)\s*{escaped_unit}\b",
                    
                    # "105 mg/dL Glucose" (value first)
                    rf"\b(\d+(?:\.\d+)?)\s*{escaped_unit}\s*{escaped_variation}\b",
                    
                    # Table format: "Glucose    105    mg/dL" - more flexible spacing
                    rf"\b{escaped_variation}\s+(\d+(?:\.\d+)?)\s+{escaped_unit}\b",
                    
                    # Lab report format: "Glucose (Hb)   15.2   g/dL   13.0-17.0"
                    rf"\b{escaped_variation}\s*(?:\([^)]*\))?\s+(\d+(?:\.\d+)?)\s+{escaped_unit}\s+[^\n]*",
                    
                    # With reference range: "Glucose: 105 mg/dL (70-99)"
                    rf"\b{escaped_variation}\s*:?\s*(\d+(?:\.\d+)?)\s*{escaped_unit}\s*\([^)]*\)",
                    
                    # Hemoglobin special case: "Hemoglobin (Hb)" format
                    rf"\b{escaped_variation}\s*\((?:Hb|HB|hb)\)\s*(\d+(?:\.\d+)?)\s*{escaped_unit}\b",
                    
                    # Flexible format: allows for various spacing and optional colons
                    rf"\b{escaped_variation}(?:\s*\([^)]*\))?\s*:?\s*(\d+(?:\.\d+)?)\s*{escaped_unit}(?:\s|$|[^\w])",
                ]
                
                for regex_pattern in patterns:
                    try:
                        matches = re.finditer(regex_pattern, text, re.IGNORECASE)
                        
                        for match in matches:
                            try:
                                value = float(match.group(1))
                                
                                # Avoid duplicates by checking if we already found this biomarker+value+unit combo
                                duplicate_found = any(
                                    b["name"] == pattern.standardized_name and 
                                    b["value"] == value and 
                                    b["unit"] == unit 
                                    for b in biomarkers
                                )
                                
                                if duplicate_found:
                                    continue
                                
                                # Extract reference range if present
                                ref_range_low, ref_range_high = self._extract_reference_range(
                                    text, match.start(), match.end(), unit, pattern
                                )
                                
                                # Determine if abnormal
                                is_abnormal = self._is_value_abnormal(value, unit, pattern, ref_range_low, ref_range_high)
                                
                                biomarker = {
                                    "name": pattern.standardized_name,
                                    "original_name": self._extract_original_name(match.group(0)),
                                    "value": value,
                                    "original_value": match.group(1),
                                    "unit": unit,
                                    "original_unit": unit,
                                    "reference_range_low": ref_range_low,
                                    "reference_range_high": ref_range_high,
                                    "reference_range_text": "",
                                    "is_abnormal": is_abnormal,
                                    "confidence": pattern.confidence_threshold,
                                    "category": self._categorize_biomarker(pattern.name),
                                    "extraction_method": "cache",
                                    "cache_pattern": variation
                                }
                                
                                biomarkers.append(biomarker)
                                
                            except (ValueError, IndexError) as e:
                                logger.debug(f"Error parsing biomarker value: {e}")
                                continue
                    except re.error as e:
                        logger.debug(f"Regex error with pattern {regex_pattern}: {e}")
                        continue
        
        return biomarkers
    
    def _extract_reference_range(self, text: str, start: int, end: int, unit: str, pattern: BiomarkerPattern) -> Tuple[Optional[float], Optional[float]]:
        """Extract reference range from context around the biomarker."""
        # Look for reference range in nearby text (±100 characters)
        context_start = max(0, start - 100)
        context_end = min(len(text), end + 100)
        context = text[context_start:context_end]
        
        # Pattern for reference ranges: (70-99), [70-99], 70-99, etc.
        range_patterns = [
            r'\((\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\)',
            r'\[(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\]',
            r'(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)',
            r'ref[^:]*:\s*(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)',
            r'normal[^:]*:\s*(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)'
        ]
        
        for range_pattern in range_patterns:
            match = re.search(range_pattern, context, re.IGNORECASE)
            if match:
                try:
                    low = float(match.group(1))
                    high = float(match.group(2))
                    return low, high
                except (ValueError, IndexError):
                    continue
        
        # Fall back to typical ranges for this biomarker and unit
        if unit in pattern.typical_ranges:
            typical = pattern.typical_ranges[unit]
            return typical.get("low"), typical.get("high")
        
        return None, None
    
    def _is_value_abnormal(self, value: float, unit: str, pattern: BiomarkerPattern, 
                          ref_low: Optional[float], ref_high: Optional[float]) -> bool:
        """Determine if a biomarker value is abnormal."""
        # Use extracted reference range if available
        if ref_low is not None and ref_high is not None:
            return value < ref_low or value > ref_high
        
        # Fall back to typical ranges
        if unit in pattern.typical_ranges:
            typical = pattern.typical_ranges[unit]
            typical_low = typical.get("low", 0)
            typical_high = typical.get("high", float('inf'))
            return value < typical_low or value > typical_high
        
        return False
    
    def _categorize_biomarker(self, biomarker_name: str) -> str:
        """Categorize biomarker into appropriate category."""
        categories = {
            "glucose": "Metabolic",
            "cholesterol": "Lipid Profile", 
            "hdl_cholesterol": "Lipid Profile",
            "ldl_cholesterol": "Lipid Profile", 
            "triglycerides": "Lipid Profile",
            "hemoglobin": "Hematology",
            "hematocrit": "Hematology",
            "creatinine": "Kidney Function"
        }
        return categories.get(biomarker_name, "Other")
    
    def learn_from_extraction(self, extracted_biomarkers: List[Dict[str, Any]], 
                            text: str, method: str = "llm") -> None:
        """
        Learn from successful biomarker extractions to improve cache.
        
        Args:
            extracted_biomarkers: Successfully extracted biomarkers
            text: Original text they were extracted from
            method: Method used for extraction (llm, cache, manual)
        """
        if method != "llm":
            return  # Only learn from LLM extractions
        
        patterns_added = 0
        patterns_updated = 0
        
        with self.cache_lock:
            for biomarker in extracted_biomarkers:
                name = biomarker.get("name", "").lower().replace(" ", "_")
                
                if name in self.biomarker_patterns:
                    # Update existing pattern
                    pattern = self.biomarker_patterns[name]
                    pattern.frequency_count += 1
                    pattern.last_seen = datetime.now().isoformat()
                    
                    # Update success rate based on confidence
                    confidence = biomarker.get("confidence", 0.5)
                    pattern.success_rate = (pattern.success_rate * 0.9 + confidence * 0.1)
                    patterns_updated += 1
                else:
                    # Create new pattern if we have room
                    if len(self.biomarker_patterns) < self.max_cache_size:
                        self._create_new_pattern(biomarker, text)
                        patterns_added += 1
        
        # Always save cache after learning new patterns
        if patterns_added > 0 or patterns_updated > 0:
            logger.debug(f"💾 Cache learning complete: {patterns_added} new patterns, {patterns_updated} updated patterns")
            self.save_cache()
    
    def _create_new_pattern(self, biomarker: Dict[str, Any], text: str) -> None:
        """Create a new biomarker pattern from successful extraction."""
        name = biomarker.get("name", "").lower().replace(" ", "_")
        standardized_name = biomarker.get("name", "Unknown")
        unit = biomarker.get("unit", "")
        value = biomarker.get("value", 0)
        confidence = biomarker.get("confidence", 0.5)
        
        # Only create patterns for high-confidence extractions
        if confidence < 0.7:
            return
        
        # Extract potential name variations from text
        variations = self._extract_name_variations(standardized_name, text)
        
        pattern = BiomarkerPattern(
            name=name,
            standardized_name=standardized_name,
            common_units=[unit] if unit else [],
            typical_ranges={unit: {"low": value * 0.5, "high": value * 2.0}} if unit and value > 0 else {},
            pattern_variations=variations,
            confidence_threshold=confidence * 0.9,  # Slightly lower for new patterns
            last_seen=datetime.now().isoformat(),
            frequency_count=1,
            success_rate=confidence
        )
        
        self.biomarker_patterns[name] = pattern
        logger.info(f"📚 Created new biomarker pattern: {standardized_name}")
    
    def _extract_name_variations(self, name: str, text: str) -> List[str]:
        """Extract potential name variations from text."""
        variations = [name.lower()]
        
        # Add common abbreviations and variations
        name_lower = name.lower()
        if "cholesterol" in name_lower:
            variations.extend(["chol", "cholest"])
        if "hemoglobin" in name_lower:
            variations.extend(["hb", "hgb", "haemoglobin"])
        if "glucose" in name_lower:
            variations.extend(["glu", "blood glucose"])
        
        return list(set(variations))
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        with self.cache_lock:
            stats = asdict(self.statistics)
            stats["cache_size"] = len(self.biomarker_patterns)
            stats["max_cache_size"] = self.max_cache_size
            stats["most_frequent_biomarkers"] = [
                {
                    "name": pattern.standardized_name,
                    "frequency": pattern.frequency_count,
                    "success_rate": pattern.success_rate
                }
                for pattern in sorted(
                    self.biomarker_patterns.values(), 
                    key=lambda x: x.frequency_count, 
                    reverse=True
                )[:10]
            ]
            stats["last_updated"] = datetime.now().isoformat()
            
            return stats
    
    def load_cache(self) -> bool:
        """Load cache from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                
                # Load biomarker patterns
                if "biomarker_patterns" in data:
                    for key, pattern_data in data["biomarker_patterns"].items():
                        self.biomarker_patterns[key] = BiomarkerPattern(**pattern_data)
                
                # Load statistics
                if "statistics" in data:
                    self.statistics = CacheStatistics(**data["statistics"])
                
                logger.info(f"📥 Loaded cache with {len(self.biomarker_patterns)} patterns")
                return True
        except Exception as e:
            logger.error(f"❌ Error loading cache: {e}")
        
        return False
    
    def save_cache(self) -> bool:
        """Save cache to file."""
        try:
            # Prepare data for serialization
            data = {
                "biomarker_patterns": {
                    key: asdict(pattern) for key, pattern in self.biomarker_patterns.items()
                },
                "statistics": asdict(self.statistics),
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0"
                }
            }
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            
            # Save to file
            with open(self.cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug(f"💾 Saved cache with {len(self.biomarker_patterns)} patterns")
            return True
        except Exception as e:
            logger.error(f"❌ Error saving cache: {e}")
            return False
    
    def clear_cache(self) -> None:
        """Clear all cached patterns and statistics."""
        with self.cache_lock:
            self.biomarker_patterns.clear()
            self.statistics = CacheStatistics()
        
        logger.info("🗑️  Cache cleared")
    
    def optimize_cache(self) -> None:
        """Optimize cache by removing low-performing patterns."""
        with self.cache_lock:
            if len(self.biomarker_patterns) <= self.max_cache_size * 0.8:
                return  # No need to optimize yet
            
            # Sort patterns by performance score
            patterns_by_score = sorted(
                self.biomarker_patterns.items(),
                key=lambda x: x[1].frequency_count * x[1].success_rate,
                reverse=True
            )
            
            # Keep top performers
            keep_count = int(self.max_cache_size * 0.7)
            patterns_to_keep = dict(patterns_by_score[:keep_count])
            
            removed_count = len(self.biomarker_patterns) - len(patterns_to_keep)
            self.biomarker_patterns = patterns_to_keep
            
            logger.info(f"🔧 Cache optimized: removed {removed_count} low-performing patterns")

    def _extract_original_name(self, match_text: str) -> str:
        """Extract the original biomarker name from the matched text."""
        # Remove extra whitespace and get first meaningful word(s)
        cleaned = match_text.strip()
        
        # If it contains parentheses, include them
        if '(' in cleaned:
            # Find everything up to the first number
            name_part = re.split(r'\d', cleaned)[0].strip()
            return name_part.rstrip(':').strip()
        else:
            # Simple case: first word before colon or number
            return cleaned.split()[0].rstrip(':')


# Global cache instance
_biomarker_cache = None
_cache_lock = Lock()


def get_biomarker_cache() -> BiomarkerCache:
    """Get the global biomarker cache instance (singleton)."""
    global _biomarker_cache
    
    if _biomarker_cache is None:
        with _cache_lock:
            if _biomarker_cache is None:
                _biomarker_cache = BiomarkerCache()
    
    return _biomarker_cache


def extract_cached_biomarkers(text: str) -> List[Dict[str, Any]]:
    """
    Convenience function to extract biomarkers using cache.
    
    Args:
        text: Text to extract biomarkers from
        
    Returns:
        List of cached biomarker extractions
    """
    cache = get_biomarker_cache()
    return cache.extract_cached_biomarkers(text) 