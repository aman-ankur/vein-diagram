# Document Analyzer Configuration
DOCUMENT_ANALYZER_CONFIG = {
    "enabled": True,               # Master toggle for all features
    "structure_analysis": {
        "enabled": True,           # Enable structure analysis
        "fallback_to_legacy": True # Fall back to old method if analysis fails
    },
    "content_optimization": {
        "enabled": True,           # Enable content optimization
        "token_reduction_target": 0.4 # Target 40% token reduction
    },
    "adaptive_context": {
        "enabled": True,           # Enable adaptive context
        "confidence_threshold": 0.7 # Minimum confidence to use adaptive prompts
    },
    "smart_chunk_skipping": {
        "enabled": True,           # Enable smart chunk skipping
        "safety_mode": True,       # Enable safety fallback when no biomarkers found
        "confidence_threshold": 0.3, # Skip chunks below this confidence
        "admin_pattern_threshold": 3, # Skip if this many admin patterns found
        "lab_indicator_boost": 0.2   # Boost confidence for lab report indicators
    },
    "biomarker_caching": {
        "enabled": True,           # Enable biomarker caching system
        "max_cache_size": 500,     # Maximum number of cached biomarker patterns
        "cache_file": None,        # Cache file path (None = auto-generated)
        "confidence_threshold": 0.8, # Use cache for biomarkers above this confidence
        "learn_from_extractions": True, # Learn new patterns from LLM extractions
        "auto_save_frequency": 10, # Save cache every N extractions
        "enable_statistics": True  # Track cache performance statistics
    }
} 