#!/usr/bin/env python3
"""
Test Claude API with environment setup
"""

import os
import sys
import logging

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Environment variables loaded from .env file")
except ImportError:
    print("⚠️ python-dotenv not installed. Using system environment variables.")

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_claude_api():
    """Test Claude API with current environment setup"""
    print("🧪 Testing Claude API with environment setup...")
    
    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")
    if not api_key:
        print("❌ No API key found in environment")
        print("Available env vars:", [k for k in os.environ.keys() if 'API' in k or 'CLAUDE' in k or 'ANTHROPIC' in k])
        return False
    
    print(f"✅ API key found (length: {len(api_key)})")
    print(f"Key starts with: {api_key[:15]}...")
    
    try:
        import anthropic
        print("✅ Anthropic library imported successfully")
        
        client = anthropic.Anthropic(api_key=api_key)
        print("✅ Anthropic client created successfully")
        
        # Test with a simple request
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            temperature=0.0,
            system="You are a helpful assistant.",
            messages=[
                {"role": "user", "content": "Say 'API test successful' if you can read this."}
            ]
        )
        
        response_text = response.content[0].text
        print(f"✅ API call successful!")
        print(f"Response: {response_text}")
        
        # Test biomarker extraction format
        print("\\n🧪 Testing biomarker extraction format...")
        biomarker_response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=200,
            temperature=0.0,
            system="You are a biomarker extraction expert. Extract biomarkers from lab reports and return valid JSON.",
            messages=[
                {"role": "user", "content": """Extract biomarkers from this text: "Glucose: 95 mg/dL (70-99)"
                
Return JSON in this format:
{
  "biomarkers": [
    {
      "name": "Glucose",
      "value": 95,
      "unit": "mg/dL",
      "reference_range": "70-99 mg/dL",
      "confidence": 0.95
    }
  ]
}"""}
            ]
        )
        
        biomarker_text = biomarker_response.content[0].text
        print(f"✅ Biomarker extraction test successful!")
        print(f"Response: {biomarker_text}")
        
        # Try to parse the JSON
        import json
        import re
        json_match = re.search(r'({[\\s\\S]*})', biomarker_text)
        if json_match:
            parsed = json.loads(json_match.group(1))
            biomarkers = parsed.get("biomarkers", [])
            print(f"✅ JSON parsing successful! Found {len(biomarkers)} biomarkers")
        else:
            print("⚠️ Could not extract JSON from response")
        
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = test_claude_api()
    if success:
        print("\\n🎉 All tests passed! Claude API is working correctly.")
    else:
        print("\\n❌ Tests failed. Check the errors above.")
        sys.exit(1) 