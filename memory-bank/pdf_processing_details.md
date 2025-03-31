# Vein Diagram: PDF Processing Details

This document details the pipeline used to extract metadata and biomarker data from uploaded PDF lab reports.

## Overview

The primary goal of the PDF processing pipeline is to automatically extract structured information (patient details, report details, biomarker results) from unstructured PDF files provided by users. This involves text extraction, potential OCR, AI-powered data extraction using Claude, data standardization, and database storage.

## Triggering the Pipeline

-   The process starts when a user uploads a PDF via the `POST /api/pdfs/upload` endpoint.
-   This endpoint saves the file, creates an initial `PDF` record in the database with status "pending", and triggers the `process_pdf_background` function (defined in `app/services/pdf_service.py`) using FastAPI's `BackgroundTasks`.

## Processing Steps (`process_pdf_background`)

1.  **Update Status**: The `PDF` record status is set to "processing".
2.  **Text Extraction (`pdf_service.extract_text_from_pdf`)**:
    *   **Primary Method**: Attempts to extract text directly using `PyPDF2`.
    *   **OCR Fallback**: If `PyPDF2` extracts no significant text (indicating an image-based PDF), it falls back to Optical Character Recognition (OCR).
        *   Uses `pdf2image` to convert PDF pages (limited to the first `MAX_PAGES=5`) into images (PNG format, 300 DPI).
        *   Uses `pytesseract` (interface to Tesseract OCR engine) to extract text from each page image. Tries different Page Segmentation Modes (PSM 6, then PSM 3) for better results.
    *   **Output**: A single string containing the extracted text from the first 5 pages. This text is saved to the `extracted_text` field of the `PDF` record. Debug logs and text files are saved in the `backend/logs/` directory.
3.  **Metadata Extraction (`metadata_parser.extract_metadata_with_claude`)**:
    *   **Input**: The extracted text from the previous step.
    *   **Process**:
        *   Sends the preprocessed text (`_preprocess_text_for_claude`) to the Claude API (`claude-3-sonnet-20240229` model).
        *   Uses a specific prompt instructing Claude to extract only metadata fields (lab_name, report_date, patient_name, dob, gender, id, age) and return them in a predefined JSON format (`{"metadata": {...}}`).
        *   Includes logic (`_repair_json`) to attempt fixing common JSON formatting errors in Claude's response.
        *   Uses a timeout decorator (`with_timeout`, 45 seconds) for the API call.
    *   **Output**: A dictionary containing the extracted metadata.
    *   **DB Update**: Updates the corresponding fields (`patient_name`, `patient_gender`, `patient_id`, `lab_name`, `report_date`, `patient_age`) in the `PDF` database record. Date parsing is handled carefully.
4.  **Biomarker Extraction (`biomarker_parser.extract_biomarkers_with_claude`)**:
    *   **Input**: The extracted text from step 2.
    *   **Primary Process**:
        *   Sends preprocessed text (`_preprocess_text_for_claude`) to the Claude API (`claude-3-sonnet-20240229` model).
        *   Uses a detailed prompt asking for specific biomarker fields (name, original_name, value, original_value, unit, original_unit, reference_range, category, is_abnormal, confidence) in a specific JSON format (`{"biomarkers": [...], "metadata": {...}}`).
        *   Includes extensive JSON repair logic (`_repair_json`, `_fix_truncated_json`) and timeout handling (`with_timeout`, 600 seconds / 10 minutes).
        *   Filters extracted biomarkers based on a minimum confidence score (currently 0.6).
    *   **Fallback 1 (Simpler Claude Prompt)**: If the primary Claude call fails (timeout, invalid JSON), it retries using `_retry_claude_with_simpler_prompt` which uses a simpler prompt and potentially a different model (`claude-3-sonnet-20240229` still mentioned, but could be Haiku) asking only for name, value, unit, range.
    *   **Fallback 2 (Pattern Matching)**: If all Claude methods fail, it uses `biomarker_parser.parse_biomarkers_from_text` which employs regular expressions (`pattern1`, `pattern2`) to find potential biomarkers based on common formats. This method has lower confidence.
    *   **Output**: A list of biomarker dictionaries.
5.  **Biomarker Standardization (`biomarker_parser._process_biomarker`)**:
    *   **Input**: The list of biomarker dictionaries extracted in the previous step.
    *   **Process**: Iterates through each biomarker dictionary and performs:
        *   Value Conversion: Attempts to convert the `value` field to a float.
        *   Unit Standardization: Uses `standardize_unit` to convert units like `mg/dl` to `mg/dL`.
        *   Reference Range Parsing: Uses `parse_reference_range` to extract numeric `reference_range_low` and `reference_range_high` values from the text range.
        *   Categorization: Uses `categorize_biomarker` to assign a category (Lipid, Metabolic, etc.) based on keywords in the name, defaulting to "Other".
        *   Abnormality Check: Determines `is_abnormal` based on comparing the numeric value to the parsed numeric reference range, or uses an explicit flag if provided by Claude.
    *   **Output**: A list of processed and standardized biomarker dictionaries.
6.  **Database Storage**:
    *   Iterates through the processed biomarkers.
    *   Creates and saves `Biomarker` records to the database, linking each to the parent `PDF` record's ID and the `Profile` ID (if available on the PDF record).
7.  **Final Status Update**:
    *   Sets the `PDF` record status to "processed" and records the `processed_date`.
    *   Calculates and saves an average `parsing_confidence` score based on the confidence values returned by Claude for the extracted biomarkers.
    *   If any step fails critically, sets the status to "error" and saves the error message.

## Key Libraries Used

-   **Text Extraction**: `PyPDF2`, `pdf2image`, `pytesseract`
-   **AI Extraction**: `anthropic` (Claude Python SDK), `httpx` (for async calls in `llm_service`)
-   **Parsing/Validation**: `re` (Regular Expressions), `json`, `dateutil`
-   **Database**: `SQLAlchemy`

## Handling Different Formats

-   The system primarily relies on the **Claude API's ability** to understand and extract data from various PDF layouts and text structures. The quality of the prompts is crucial here.
-   **OCR** handles PDFs that are purely images or have non-selectable text.
-   The **fallback regex parser** (`parse_biomarkers_from_text`) provides a basic level of extraction for common formats if Claude fails, but it is significantly less robust and accurate.

## Known Limitations & Edge Cases

-   **Accuracy Dependency**: The overall accuracy heavily depends on the Claude model's performance for both metadata and biomarker extraction, which can vary based on PDF quality and format complexity. Prompt engineering is key.
-   **Fallback Parser Limitations**: The regex fallback parser only recognizes limited formats and may miss or misinterpret data.
-   **OCR Errors**: OCR accuracy depends on image resolution, text clarity, and layout complexity. Errors can lead to incorrect data extraction.
-   **Page Limit**: Processing is limited to the first `MAX_PAGES` (currently 5) pages of the PDF. Information beyond this limit is ignored.
-   **Complex Tables/Layouts**: Extremely complex or unconventional table structures might still confuse Claude or the fallback parser.
-   **JSON Repair**: While attempts are made to repair malformed JSON from Claude, complex errors might still lead to parsing failures and reliance on the fallback parser.
-   **Timeouts**: Long processing times or slow Claude API responses might hit timeouts, potentially leading to incomplete processing or reliance on fallbacks.
-   **Ambiguous Data**: Sometimes data in PDFs is inherently ambiguous (e.g., unclear units, overlapping ranges), which can lead to interpretation errors.
