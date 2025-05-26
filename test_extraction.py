import asyncio
from app.services.biomarker_parser import extract_biomarkers_with_claude

async def test_extraction():
    text = 'Glucose: 95 mg/dL (70-99)'
    try:
        biomarkers, context = await extract_biomarkers_with_claude(text)
        print(f'✅ Extraction works: Found {len(biomarkers)} biomarkers')
        if biomarkers:
            print(f'First biomarker: {biomarkers[0]["name"]}')
        return True
    except Exception as e:
        print(f'❌ Extraction failed: {e}')
        return False

if __name__ == "__main__":
    result = asyncio.run(test_extraction())
    print(f'Test result: {result}') 