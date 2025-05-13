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
    }
} 