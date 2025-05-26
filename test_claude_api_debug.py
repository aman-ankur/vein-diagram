#!/usr/bin/env python3
"""
Claude API Debug Script

This script tests the specific Claude API issues we're seeing:
1. Token increase instead of reduction (4447 -> 9172 tokens, -106.25%)
2. "No biomarkers found" responses
3. "Could not extract JSON" errors
4. Content optimization backfiring
"""

import os
import sys
import json
import logging
import time
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_api_key():
    """Test if API key is available and valid."""
    logger.info("=== Testing API Key ===")
    
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        logger.error("❌ No API key found in environment variables")
        return False
    
    logger.info(f"✅ API key found: {api_key[:10]}...{api_key[-4:]}")
    return True

def test_simple_api_call():
    """Test a simple Claude API call to verify connectivity."""
    logger.info("=== Testing Simple API Call ===")
    
    try:
        import anthropic
        
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
        client = anthropic.Anthropic(api_key=api_key)
        
        start_time = time.time()
        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            temperature=0,
            system="You are a helpful assistant.",
            messages=[{"role": "user", "content": "Say 'Hello, API is working!'"}]
        )
        
        elapsed = time.time() - start_time
        content = response.content[0].text
        
        logger.info(f"✅ API call successful in {elapsed:.2f}s")
        logger.info(f"Response: {content}")
        return True
        
    except Exception as e:
        logger.error(f"❌ API call failed: {str(e)}")
        return False

def test_biomarker_extraction_prompt():
    """Test the biomarker extraction prompt with sample data."""
    logger.info("=== Testing Biomarker Extraction Prompt ===")
    
    # Sample lab report text (similar to what would be in the PDF)
    sample_text = """
LABORATORY REPORT
Patient: SANDHYA SINHA
Date: 2025-05-12
Lab: Agilus Diagnostics Ltd

TEST                    RESULT      REFERENCE RANGE    FLAG
Glucose, Fasting        95 mg/dL    70-99 mg/dL        Normal
Hemoglobin A1c          5.7 %       < 5.7 %            High
Total Cholesterol       180 mg/dL   < 200 mg/dL        Normal
HDL Cholesterol         45 mg/dL    > 40 mg/dL         Normal
LDL Cholesterol         120 mg/dL   < 100 mg/dL        High
Triglycerides          150 mg/dL    < 150 mg/dL        Normal
TSH                     2.5 mIU/L   0.4-4.0 mIU/L      Normal
Vitamin D               25 ng/mL    30-100 ng/mL       Low
"""
    
    # The exact prompt from biomarker_parser.py
    prompt = """
Extract ONLY legitimate clinical biomarkers from this medical lab report text. Focus exclusively on measurements that have numeric values and units.

For each biomarker, provide:
- name: Standardized name
- original_name: Exact name as it appears
- value: Numerical result (convert ranges to midpoint)
- original_value: Result as shown in report
- unit: Standardized unit
- original_unit: Unit as shown
- reference_range: Normal range text
- reference_range_low: Lower bound as number
- reference_range_high: Upper bound as number
- category: One of: Lipid, Metabolic, Liver, Kidney, Electrolyte, Blood, Thyroid, Vitamin, Hormone, Immunology, Cardiovascular, Other
- is_abnormal: true if outside reference range
- confidence: 0.0-1.0 score of certainty

CRITICAL: DO NOT extract page numbers, headers, footers, patient info, dates, IDs, URLs, or explanatory text.

Return valid JSON matching exactly this structure (NO METADATA):
{
  "biomarkers": [
    {
      "name": "Glucose",
      "original_name": "Glucose, Fasting",
      "value": 95,
      "original_value": "95",
      "unit": "mg/dL",
      "original_unit": "mg/dL",
      "reference_range": "70-99 mg/dL",
      "reference_range_low": 70,
      "reference_range_high": 99,
      "category": "Metabolic",
      "is_abnormal": false,
      "confidence": 0.98
    }
  ]
}

Lab report text:
""" + sample_text
    
    try:
        import anthropic
        
        api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
        client = anthropic.Anthropic(api_key=api_key)
        
        logger.info("Sending biomarker extraction request...")
        start_time = time.time()
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=4000,
            temperature=0.0,
            system="You are a biomarker extraction expert specializing in parsing medical lab reports. Extract ONLY valid clinical biomarkers with measurements and reference ranges. Your output MUST be COMPLETE, VALID JSON.",
            messages=[{"role": "user", "content": prompt}]
        )
        
        elapsed = time.time() - start_time
        content = response.content[0].text
        
        logger.info(f"✅ Biomarker extraction call successful in {elapsed:.2f}s")
        logger.info(f"Response length: {len(content)} characters")
        logger.info(f"Response preview: {content[:200]}...")
        
        # Try to parse the JSON
        try:
            import re
            json_match = re.search(r'({[\s\S]*})', content)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)
                biomarkers = parsed.get("biomarkers", [])
                logger.info(f"✅ Successfully parsed JSON with {len(biomarkers)} biomarkers")
                
                for i, bm in enumerate(biomarkers[:3]):  # Show first 3
                    logger.info(f"  Biomarker {i+1}: {bm.get('name')} = {bm.get('value')} {bm.get('unit')}")
                
                return True
            else:
                logger.error("❌ No JSON found in response")
                logger.error(f"Full response: {content}")
                return False
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {str(e)}")
            logger.error(f"JSON content: {json_str[:500]}...")
            return False
            
    except Exception as e:
        logger.error(f"❌ Biomarker extraction failed: {str(e)}")
        return False

def test_token_counting():
    """Test token counting to understand the token increase issue."""
    logger.info("=== Testing Token Counting ===")
    
    try:
        from app.services.utils.content_optimization import estimate_tokens
        
        # Sample text that might cause token increase
        original_text = """
LABORATORY REPORT
Patient: SANDHYA SINHA
Date: 2025-05-12

TEST                    RESULT      REFERENCE RANGE
Glucose                 95 mg/dL    70-99 mg/dL
Cholesterol            180 mg/dL    < 200 mg/dL
"""
        
        # Simulate content optimization
        from app.services.utils.content_optimization import compress_text_content
        compressed_text = compress_text_content(original_text)
        
        original_tokens = estimate_tokens(original_text)
        compressed_tokens = estimate_tokens(compressed_text)
        
        logger.info(f"Original text: {len(original_text)} chars, {original_tokens} tokens")
        logger.info(f"Compressed text: {len(compressed_text)} chars, {compressed_tokens} tokens")
        
        if compressed_tokens > original_tokens:
            logger.error(f"❌ Token INCREASE: {compressed_tokens - original_tokens} tokens ({((compressed_tokens/original_tokens - 1) * 100):.1f}%)")
        else:
            logger.info(f"✅ Token reduction: {original_tokens - compressed_tokens} tokens ({((1 - compressed_tokens/original_tokens) * 100):.1f}%)")
        
        logger.info(f"Original text:\n{original_text}")
        logger.info(f"Compressed text:\n{compressed_text}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Token counting test failed: {str(e)}")
        return False

def test_content_optimization():
    """Test the content optimization that's causing token increases."""
    logger.info("=== Testing Content Optimization ===")
    
    try:
        # Simulate the pages_text_dict that would come from PDF extraction
        pages_text_dict = {
            0: """LABORATORY REPORT
Patient: SANDHYA SINHA
Date: 2025-05-12
Lab: Agilus Diagnostics Ltd

TEST                    RESULT      REFERENCE RANGE    FLAG
Glucose, Fasting        95 mg/dL    70-99 mg/dL        Normal
Hemoglobin A1c          5.7 %       < 5.7 %            High""",
            
            1: """TEST                    RESULT      REFERENCE RANGE    FLAG
Total Cholesterol       180 mg/dL   < 200 mg/dL        Normal
HDL Cholesterol         45 mg/dL    > 40 mg/dL         Normal
LDL Cholesterol         120 mg/dL   < 100 mg/dL        High""",
            
            2: """TEST                    RESULT      REFERENCE RANGE    FLAG
Triglycerides          150 mg/dL    < 150 mg/dL        Normal
TSH                     2.5 mIU/L   0.4-4.0 mIU/L      Normal
Vitamin D               25 ng/mL    30-100 ng/mL       Low"""
        }
        
        # Simulate document structure
        document_structure = {
            "confidence": 0.89,
            "tables": {0: [{}], 1: [{}], 2: [{}]},
            "page_zones": {
                0: {"content": {"confidence": 0.8}},
                1: {"content": {"confidence": 0.8}},
                2: {"content": {"confidence": 0.8}}
            }
        }
        
        from app.services.utils.content_optimization import optimize_content_chunks, estimate_tokens
        
        # Calculate original tokens
        original_tokens = sum(estimate_tokens(text) for text in pages_text_dict.values())
        logger.info(f"Original total tokens: {original_tokens}")
        
        # Run content optimization
        chunks = optimize_content_chunks(pages_text_dict, document_structure)
        
        # Calculate optimized tokens
        optimized_tokens = sum(chunk["estimated_tokens"] for chunk in chunks)
        logger.info(f"Optimized total tokens: {optimized_tokens}")
        
        reduction_percentage = (1 - (optimized_tokens / original_tokens)) * 100 if original_tokens > 0 else 0
        logger.info(f"Token change: {reduction_percentage:.2f}%")
        
        if reduction_percentage < 0:
            logger.error(f"❌ Token INCREASE detected: {-reduction_percentage:.2f}%")
            logger.info("Chunk details:")
            for i, chunk in enumerate(chunks):
                logger.info(f"  Chunk {i}: {chunk['estimated_tokens']} tokens, confidence: {chunk['biomarker_confidence']:.2f}")
                logger.info(f"    Text preview: {chunk['text'][:100]}...")
        else:
            logger.info(f"✅ Token reduction achieved: {reduction_percentage:.2f}%")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Content optimization test failed: {str(e)}")
        return False

def main():
    """Run all diagnostic tests."""
    logger.info("🔍 Starting Claude API Diagnostic Tests")
    logger.info("=" * 50)
    
    tests = [
        ("API Key Check", test_api_key),
        ("Simple API Call", test_simple_api_call),
        ("Token Counting", test_token_counting),
        ("Content Optimization", test_content_optimization),
        ("Biomarker Extraction", test_biomarker_extraction_prompt),
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"\n🧪 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} crashed: {str(e)}")
            results[test_name] = False
        
        logger.info("-" * 30)
    
    # Summary
    logger.info("\n📊 TEST RESULTS SUMMARY")
    logger.info("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Claude API should be working correctly.")
    else:
        logger.error("⚠️  Some tests failed. Check the logs above for specific issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 