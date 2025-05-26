from app.services.biomarker_parser import parse_biomarkers_from_text

# Test text with real biomarker data
test_text = """
LABORATORY REPORT
Patient: John Doe

TEST                    RESULT      REFERENCE RANGE    FLAG
Glucose                 95 mg/dL    70-99              Normal
Hemoglobin A1c          5.7 %       < 5.7              Normal
Total Cholesterol       180 mg/dL   < 200              Normal
HDL Cholesterol         45 mg/dL    > 40               Normal
LDL Cholesterol         120 mg/dL   < 100              High

Normal 100.00 Impaired
CR00000037 ACCESSION NO 706.00 YE
59 DHANBAD 826001.00 ABHA
"""

print("Testing improved fallback parser...")
biomarkers = parse_biomarkers_from_text(test_text)

print(f"Found {len(biomarkers)} biomarkers:")
for bm in biomarkers:
    print(f"  - {bm['name']}: {bm['value']} {bm['unit']}") 