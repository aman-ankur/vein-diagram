# PDF Biomarker Extraction: End-to-End Overview

This document summarizes the full process for extracting biomarkers from uploaded PDF lab reports in the Vein Diagram system. It references key files, functions, controls, and limitations, and is intended as a high-level technical overview for developers and maintainers.

---

## 1. PDF Upload & Initial Trigger
- **Frontend**: User uploads a PDF via the UI (handled by React, `pdfService.ts`).
- **Backend Endpoint**: `POST /api/pdfs/upload` (see `api_documentation.md`)
  - Saves the file, creates a `PDF` record (status: `pending`).
  - Triggers background processing via `process_pdf_background` (`app/services/pdf_service.py`).

## 2. Text Extraction from PDF
- **Function**: `pdf_service.extract_text_from_pdf`
- **Libraries**: `PyMuPDF` (fitz) for direct text extraction.
  - If text extraction fails, falls back to OCR:
    - `pdf2image` (convert up to 5 pages to images)
    - `pytesseract` (OCR, multiple PSM modes)
- **Output**: Dict mapping page numbers to extracted text.
- **Controls**: Logs and debug info saved for traceability.

## 3. Metadata Extraction (LLM/Claude)
- **Function**: `metadata_parser.extract_metadata_with_claude`
- **Input**: Concatenated text from first few pages.
- **LLM**: Claude (`claude-3-sonnet-20240229`)
- **Prompt**: Requests only specific metadata fields in strict JSON.
- **Controls**:
  - Timeout (45s)
  - JSON repair logic
  - Only updates specific fields in the `PDF` record
- **Limitations**: If Claude fails/times out, metadata may be incomplete.

## 4. Page Filtering (Heuristic Guardrail)
- **Function**: `pdf_service.filter_relevant_pages`
- **Logic**:
  - Loads biomarker names/aliases from `biomarker_aliases.json`
  - Scores each page for relevance (biomarker mentions, units, table-like structures)
  - Only pages with score ≥ 1 are processed for biomarkers
- **Purpose**: Reduces noise, controls cost/latency, avoids irrelevant LLM calls.

## 5. Sequential Biomarker Extraction (LLM/Claude)
- **Function**: `pdf_service.process_pages_sequentially`
- **For Each Relevant Page**:
  - Calls `biomarker_parser.extract_biomarkers_with_claude`
    - **Prompt**: Requests only biomarker fields in strict JSON
    - **Timeout**: 10 min per page
    - **JSON Repair**: Extensive logic for malformed/truncated JSON
    - **Fallback**: If Claude fails, uses `parse_biomarkers_from_text` (regex-based)
- **Aggregation**: Combines results, de-duplicates by standardized biomarker name.

## 6. Biomarker Standardization & Validation
- **Function**: `biomarker_parser._process_biomarker`
- **Steps**:
  - Converts values to floats
  - Standardizes units
  - Parses reference ranges
  - Categorizes biomarkers
  - Checks for abnormal values
- **Purpose**: Ensures consistency and reliability in downstream analysis.

## 7. Database Storage
- **Entities**: `PDF`, `Biomarker`, `Profile` (see `database_schema.md`)
- **Action**: Stores each processed biomarker, linking to PDF and user profile.

## 8. Status Update & Confidence Scoring
- **Final Step**: Updates PDF record to `processed` or `error`.
- **Confidence**: Stores average confidence score from Claude for extracted biomarkers.

---

## Controls, Guardrails, and Limitations

### Controls & Guardrails
- **Page Filtering**: Only relevant pages sent to LLM
- **Timeouts**: Strict timeouts for LLM calls (45s metadata, 10min/page biomarkers)
- **Fallbacks**: Regex-based extraction if LLM fails
- **JSON Repair**: Attempts to fix malformed LLM output
- **Logging**: Debug logs and JSON dumps for traceability
- **Standardization**: All biomarker data normalized for name, unit, and range
- **Error Handling**: Status set to `error` and error logged if any step fails

### Limitations
- **LLM Dependency**: Extraction accuracy depends on Claude's performance and prompt quality
- **OCR Quality**: Poor scans or complex layouts can reduce extraction accuracy
- **Heuristic Filtering**: May miss relevant pages or include irrelevant ones
- **Fallback Parser**: Regex-based extraction is less robust
- **Ambiguity**: Some data in PDFs may be inherently ambiguous
- **Rate Limits/Cost**: Sequential LLM calls can be slow/costly for large PDFs

---

## Summary Table: Key Files & Functions

| Step                        | File/Module                        | Key Function(s) / Endpoint                |
|-----------------------------|------------------------------------|-------------------------------------------|
| PDF Upload                  | `pdfService.ts` (frontend), `pdf_routes.py` (backend) | `/api/pdfs/upload`                        |
| Text Extraction             | `pdf_service.py`                   | `extract_text_from_pdf`                   |
| Metadata Extraction (LLM)   | `metadata_parser.py`               | `extract_metadata_with_claude`            |
| Page Filtering              | `pdf_service.py`                   | `filter_relevant_pages`                   |
| Biomarker Extraction (LLM)  | `biomarker_parser.py`              | `extract_biomarkers_with_claude`, `parse_biomarkers_from_text` |
| Standardization             | `biomarker_parser.py`              | `_process_biomarker`                      |
| Database Storage            | `pdf_service.py`, `biomarker_model.py` | ORM logic                                 |
| Status/Confidence Update    | `pdf_service.py`                   | Status update logic                       |

---

## References in @memory-bank
- `pdf_processing_details.md`: Full pipeline, controls, and limitations
- `claude_integration.md`: LLM prompt strategies, error handling, and fallback logic
- `database_schema.md`: Data model and relationships
- `.clinerules`: Step-by-step and known challenges
- `progress.md`, `activeContext.md`: Recent improvements, known issues, and ongoing work

---

**This document is intended as a living reference. Please update as the pipeline or controls evolve.** 