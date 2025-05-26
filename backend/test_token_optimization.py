#!/usr/bin/env python3
"""
Test token optimization to verify it's working correctly
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

def test_token_optimization():
    """Test token optimization to ensure it reduces tokens"""
    print("🧪 Testing Token Optimization...")
    
    try:
        from app.services.utils.content_optimization import estimate_tokens, compress_text_content
        
        # Sample text that mimics the problematic PDF content
        original_text = """
DIAGNOSTIC REPORT

PATIENT NAME : SANDHYA SINHA                    REF. DOCTOR : DR. DR SK SINHA
CODE/NAME & ADDRESS : CR00000037                ACCESSION NO : 0706YE002446    AGE/SEX : 66 Years    Female
SRL REACH LTD  OPD PATIENT-DHANBAD             PATIENT ID    : SANDF260260706   DRAWN   : 11/05/2025 08:27:23
SADAR HOSPITAL,                                 CLIENT PATIENT ID:              RECEIVED : 11/05/2025 08:29:59
DHANBAD 826001                                  ABHA NO      :                  REPORTED : 12/05/2025 13:54:07

Test Report Status    Final                     Results                         Biological Reference Interval    Units

ALLERGY
TOTAL IGE
TOTAL  IGE                                      2022.0  High                    < 100                           kU/L
METHOD : ELECTROCHEMILUMINESCENCE,SANDWICH IMMUNOASSAY

Interpretation:
TOTAL IGE-Introduction:
Total Immunoglobulin E (IgE), serum measures the total quantity of circulating IgE in human serum samples. Immunoglobulin E (IgE) is one of the 5 classes of
immunoglobulins and is defined by the presence of the epsilon heavy chain.

Test Utility:
Elevated levels may be found in,
1.Allergy - IgE antibodies appear as a result of sensitization to allergens, and the measurement of circulating total IgE assists the clinical diagnosis of IgE-mediated allergic
disorders. Elevated levels of circulating total IgE are usually seen in atopic eczema, 60% of patients with extrinsic asthma, and about 30% cases of hay fever. However a
markedly elevated total IgE may not specifically with allergen solid phase and result in weakly positive specific IgE that may not be clinically relevant.
2. Parasitic infections, Visceral larva migrans, Hookworm disease, Schistosomiasis,  Echinococcosis.
3. Monoclonal IgE myeloma
4. Allergic Bronchopulmonary Aspergillosis (ABPA)

Decreased levels may be found in,
1. Hypogammaglobulinemia
2. Acquired immunodeficiency
3. Ataxia telangiectasia
4. Non-secretory myeloma
Limitation:
A normal level of IgE does not eliminate the possibility of allergy, hence test is not recommended as a stand-alone screen. Value is influenced by type of allergen, duration
of stimulation, presence of symptoms, hyposensitization treatment.

**End Of Report**
Please visit www.agilusdiagnostics.com for related Test Information for this accession

Dr. Chaitali Ray, PHD                          Dr. Santanu Hazra
Senior Biochemist cum                          Consultant Microbiologist
Management Representative

PERFORMED AT :
Agilus Diagnostics Ltd
Frontier Warehouse Building, 153F,SM Bose Road. 1st Floor,Block C (F1,F2,F3 &
F4), Premises Sarpara, North 24 Pgs
Kolkata, 700114
West Bengal, India
Tel : 9111591115, Fax : 30203412
CIN - U74899PB1995PLC045956
Email : customercare.saltlake@agilus.in

Fax: 30203412.00
CIN: -U74899PB1995PLC045956 Email :customercare.saltlake@agilus.inPERFORMED AT :
"""
        
        # Calculate original tokens
        original_tokens = estimate_tokens(original_text)
        print(f"📊 Original text: {len(original_text)} chars, {original_tokens} tokens")
        
        # Apply compression
        compressed_text = compress_text_content(original_text)
        compressed_tokens = estimate_tokens(compressed_text)
        
        print(f"📊 Compressed text: {len(compressed_text)} chars, {compressed_tokens} tokens")
        
        # Calculate reduction
        token_reduction = original_tokens - compressed_tokens
        reduction_percentage = (token_reduction / original_tokens) * 100 if original_tokens > 0 else 0
        
        if token_reduction > 0:
            print(f"✅ Token reduction achieved: {token_reduction} tokens ({reduction_percentage:.1f}%)")
        else:
            print(f"❌ Token INCREASE: {-token_reduction} tokens ({-reduction_percentage:.1f}%)")
            
        print(f"\n📝 Original text preview:\n{original_text[:200]}...")
        print(f"\n📝 Compressed text preview:\n{compressed_text[:200]}...")
        
        # Test with the specific problematic patterns
        print("\n🔍 Testing specific pattern removal...")
        
        test_patterns = [
            "Fax: 30203412.00",
            "CIN: -U74899PB1995PLC045956",
            "Email :customercare.saltlake@agilus.in",
            "PERFORMED AT :",
            "Normal"
        ]
        
        for pattern in test_patterns:
            if pattern in original_text and pattern not in compressed_text:
                print(f"✅ Successfully removed: '{pattern}'")
            elif pattern in original_text and pattern in compressed_text:
                print(f"⚠️ Pattern still present: '{pattern}'")
            else:
                print(f"ℹ️ Pattern not found in original: '{pattern}'")
        
        return token_reduction > 0
        
    except Exception as e:
        print(f"❌ Token optimization test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def test_biomarker_filtering():
    """Test biomarker filtering to ensure invalid entries are excluded"""
    print("\n🧪 Testing Biomarker Filtering...")
    
    try:
        from app.services.biomarker_parser import parse_biomarkers_from_text
        
        # Sample text with both valid and invalid biomarkers
        test_text = """
Fax: 30203412.00
CIN: -U74899PB1995PLC045956 Email :customercare.saltlake@agilus.in
PERFORMED AT : Agilus Diagnostics Ltd

TOTAL IGE                    2022.0  High      < 100           kU/L
Glucose, Fasting             116.0             <100            mg/dL  
Hemoglobin                   9.9               12 - 15 gm/dL   g/dL
TSH                          3.21              0.27 - 4.20     µIU/mL

Normal
Other
"""
        
        biomarkers = parse_biomarkers_from_text(test_text)
        
        print(f"📊 Found {len(biomarkers)} biomarkers:")
        
        valid_biomarkers = []
        invalid_biomarkers = []
        
        expected_valid = ["total ige", "glucose", "hemoglobin", "tsh"]
        expected_invalid = ["fax", "cin", "normal", "other", "performed at"]
        
        for biomarker in biomarkers:
            name = biomarker.get("name", "").lower()
            print(f"  - {biomarker.get('name')}: {biomarker.get('value')} {biomarker.get('unit')}")
            
            if any(valid in name for valid in expected_valid):
                valid_biomarkers.append(name)
            elif any(invalid in name for invalid in expected_invalid):
                invalid_biomarkers.append(name)
        
        print(f"\n✅ Valid biomarkers found: {len(valid_biomarkers)}")
        print(f"❌ Invalid biomarkers found: {len(invalid_biomarkers)}")
        
        if len(invalid_biomarkers) == 0:
            print("✅ Filtering working correctly - no invalid biomarkers extracted")
            return True
        else:
            print(f"⚠️ Filtering needs improvement - found invalid biomarkers: {invalid_biomarkers}")
            return False
            
    except Exception as e:
        print(f"❌ Biomarker filtering test failed: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Token Optimization and Biomarker Filtering Tests\n")
    
    token_test_passed = test_token_optimization()
    filter_test_passed = test_biomarker_filtering()
    
    print("\n" + "="*50)
    print("📋 TEST SUMMARY")
    print("="*50)
    print(f"Token Optimization: {'✅ PASSED' if token_test_passed else '❌ FAILED'}")
    print(f"Biomarker Filtering: {'✅ PASSED' if filter_test_passed else '❌ FAILED'}")
    
    if token_test_passed and filter_test_passed:
        print("\n🎉 All tests passed! The optimizations are working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️ Some tests failed. Check the output above for details.")
        sys.exit(1) 