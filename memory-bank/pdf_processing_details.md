# Vein Diagram: PDF Processing Details

This document details the pipeline used to extract metadata and biomarker data from uploaded PDF lab reports.

## Overview

The primary goal of the PDF processing pipeline is to automatically extract structured information (patient details, report details, biomarker results) from unstructured PDF files provided by users. This involves text extraction, document structure analysis, potential OCR, AI-powered data extraction using Claude, data standardization, and database storage.

## Triggering the Pipeline

-   The process starts when a user uploads a PDF via the `POST /api/pdfs/upload` endpoint.
-   This endpoint saves the file, creates an initial `PDF` record in the database with status "pending", and triggers the `process_pdf_background` function (defined in `app/services/pdf_service.py`) using FastAPI's `BackgroundTasks`.

## Processing Steps (`process_pdf_background`)

1.  **Update Status**: The `PDF` record status is set to "processing".
2.  **Text Extraction (`pdf_service.extract_text_from_pdf`)**:
    *   **Primary Method**: Attempts to extract text directly using `PyMuPDF` (fitz).
    *   **OCR Fallback**: If `PyMuPDF` extracts no significant text (indicating an image-based PDF), it falls back to Optical Character Recognition (OCR).
        *   Uses `pdf2image` to convert PDF pages (limited to the first `MAX_PAGES=5`) into images (PNG format, 300 DPI).
        *   Uses `pytesseract` (interface to Tesseract OCR engine) to extract text from each page image. Tries different Page Segmentation Modes (PSM 6, then PSM 3) for better results.
    *   **Output**: A dictionary mapping page numbers (0-indexed) to the extracted text for *all* pages (`Dict[int, str]`). A combined version of this text is saved to the `extracted_text` field of the `PDF` record. Debug logs and JSON files (containing text per page) are saved in the `backend/logs/` directory.
3.  **Document Structure Analysis (`document_analyzer.analyze_document_structure`)**:
    *   **Input**: PDF path and the dictionary of page texts (`pages_text_dict`) from Step 2.
    *   **Process**:
        *   Uses `pdfplumber` to detect tables and analyze document layout
        *   Identifies page zones (header, footer, content)
        *   Classifies document type using pattern matching (e.g., "quest_diagnostics", "labcorp")
        *   Generates confidence scores for the analysis
    *   **Output**: A `DocumentStructure` object containing tables, page zones, document type, and other structural information.
    *   **Feature Toggle**: This functionality can be enabled/disabled via the `DOCUMENT_ANALYZER_CONFIG` settings in `config.py`.
4.  **Metadata Extraction (`metadata_parser.extract_metadata_with_claude`)**:
    *   **Input**: Concatenated text from the first few pages (e.g., pages 0-2) of the dictionary extracted in Step 2.
    *   **Process**:
        *   Sends the preprocessed text from the initial pages to the Claude API (`claude-3-sonnet-20240229` model).
        *   Uses a specific prompt instructing Claude to extract only metadata fields (lab_name, report_date, patient_name, dob, gender, id, age) and return them in a predefined JSON format (`{"metadata": {...}}`).
        *   Includes logic (`_repair_json`) to attempt fixing common JSON formatting errors in Claude's response.
        *   Uses a timeout decorator (`with_timeout`, 45 seconds) for the API call.
    *   **Output**: A dictionary containing the extracted metadata.
    *   **DB Update**: Updates the corresponding fields (`patient_name`, `patient_gender`, `patient_id`, `lab_name`, `report_date`, `patient_age`) in the `PDF` database record. Date parsing is handled carefully.
5.  **Page Filtering (`pdf_service.filter_relevant_pages`)**:
    *   **Input**: The full dictionary of page texts (`pages_text_dict`) from Step 2 and the document structure from Step 3.
    *   **Process**:
        *   Loads biomarker names and aliases from `app/utils/biomarker_aliases.json`.
        *   Scores each page's relevance using `pdf_service.score_page_relevance` based on:
            * Presence of biomarker aliases
            * Common units near numbers
            * Potential table structures
            * **NEW**: Structural information (tables, content zones) from document analysis
        *   Filters pages that meet a minimum relevance score (currently score >= 1).
    *   **Output**: A sorted list of tuples `(page_number, page_text)` containing only the pages deemed relevant for biomarker extraction.
6.  **Sequential Biomarker Extraction (`pdf_service.process_pages_sequentially`)**:
    *   **Input**: The list of relevant page tuples from Step 5 and the document structure from Step 3.
    *   **Process**:
        *   Iterates through each relevant page tuple.
        *   For each page, calls `biomarker_parser.extract_biomarkers_with_claude`, passing only that single page's text.
        *   `extract_biomarkers_with_claude` uses a prompt optimized for single-page extraction (no metadata request) and includes JSON repair and timeout logic (10 minutes per page). It falls back to `parse_biomarkers_from_text` (regex parser) for that specific page if Claude fails (timeout, error, invalid JSON).
        *   Aggregates the biomarker dictionaries returned from each successful page processing call.
        *   De-duplicates the aggregated biomarkers based on the standardized name (keeping the first occurrence).
    *   **Output**: A list of de-duplicated biomarker dictionaries.
7.  **Biomarker Standardization (`biomarker_parser._process_biomarker`)**:
    *   **Input**: The list of de-duplicated biomarker dictionaries extracted in the previous step.
    *   **Process**: Iterates through each biomarker dictionary and performs:
        *   Value Conversion: Attempts to convert the `value` field to a float.
        *   Unit Standardization: Uses `standardize_unit` to convert units like `mg/dl` to `mg/dL`.
        *   Reference Range Parsing: Uses `parse_reference_range` to extract numeric `reference_range_low` and `reference_range_high` values from the text range.
        *   Categorization: Uses `categorize_biomarker` to assign a category (Lipid, Metabolic, etc.) based on keywords in the name, defaulting to "Other".
        *   Abnormality Check: Determines `is_abnormal` based on comparing the numeric value to the parsed numeric reference range, or uses an explicit flag if provided by Claude.
    *   **Output**: A list of processed and standardized biomarker dictionaries.
8.  **Database Storage**:
    *   Iterates through the final list of processed biomarkers.
    *   Creates and saves `Biomarker` records to the database, linking each to the parent `PDF` record's ID and the `Profile` ID associated with the PDF.
9.  **Final Status Update**:
    *   Sets the `PDF` record status to "processed" and records the `processed_date`.
    *   Calculates and saves an average `parsing_confidence` score based on the confidence values returned by Claude for the successfully extracted biomarkers across all processed pages.
    *   If any step fails critically, sets the status to "error" and saves the error message.

## System Reliability & Recovery

### Smart Status Endpoint
The `/api/pdf/status/{file_id}` endpoint includes intelligent auto-recovery capabilities:

- **Inconsistency Detection**: Automatically detects PDFs stuck in "pending" or "processing" status that actually have biomarkers
- **Auto-Correction**: Updates status to "processed" when biomarkers exist but status is incorrect
- **Confidence Calculation**: Calculates parsing confidence (base 50% + 5% per biomarker, capped at 95%) if missing
- **Data Preservation**: Preserves existing processed_date and parsing_confidence values
- **Logging**: Comprehensive logging of all corrections for monitoring

### Startup Recovery Service
The system includes an automatic recovery service (`startup_recovery_service.py`) that:

- **Runs on Startup**: Automatically executes when the server starts
- **Detects Inconsistencies**: Identifies PDFs with wrong status but existing biomarkers
- **Batch Recovery**: Fixes multiple stuck PDFs in a single operation
- **Health Monitoring**: Provides comprehensive health checks without making changes
- **Error Handling**: Graceful handling of database errors with rollback and logging

### Recovery Functions
- `detect_inconsistent_pdfs()`: Finds PDFs with inconsistent status
- `fix_inconsistent_pdf()`: Updates a single PDF's status and metadata
- `run_startup_recovery()`: Complete recovery process with detailed results
- `check_processing_health()`: Health monitoring without changes

### Benefits
- **Zero Downtime**: System self-heals without manual intervention
- **Eliminates Infinite Loops**: Frontend never gets stuck polling for status
- **Data Integrity**: Ensures consistent state between processing completion and status
- **Monitoring**: Clear visibility into system health and recovery actions

## Key Libraries Used

-   **Text Extraction**: `PyMuPDF` (fitz), `pdf2image`, `pytesseract`
-   **Document Structure Analysis**: `pdfplumber`
-   **AI Extraction**: `anthropic` (Claude Python SDK), `httpx` (for async calls in `llm_service`)
-   **Parsing/Validation**: `re` (Regular Expressions), `json`, `dateutil`
-   **Database**: `SQLAlchemy`

## Handling Different Formats

-   The **document structure analysis** helps identify different document formats and layouts, improving extraction accuracy for various lab report types.
-   The system primarily relies on the **Claude API's ability** to understand and extract data from various PDF layouts and text structures during the sequential page processing. The quality of the prompts is crucial here.
-   **OCR** handles PDFs that are purely images or have non-selectable text.
-   The **fallback regex parser** (`parse_biomarkers_from_text`) provides a basic level of extraction for common formats *per page* if Claude fails for that specific page, but it is significantly less robust and accurate.

## Feature Toggles

The document analysis features can be controlled through the configuration settings in `config.py`:

```python
DOCUMENT_ANALYZER_CONFIG = {
    "enabled": True,               # Master toggle for all features
    "structure_analysis": {
        "enabled": True,           # Enable structure analysis
        "fallback_to_legacy": True # Fall back to old method if analysis fails
    }
}
```

This allows for progressive rollout and A/B testing of the new functionality.

## Known Limitations & Edge Cases

-   **Accuracy Dependency**: The overall accuracy heavily depends on the Claude model's performance for both metadata and biomarker extraction, which can vary based on PDF quality and format complexity. Prompt engineering is key.
-   **Fallback Parser Limitations**: The regex fallback parser only recognizes limited formats and may miss or misinterpret data.
-   **OCR Errors**: OCR accuracy depends on image resolution, text clarity, and layout complexity. Errors can lead to incorrect data extraction.
-   **Filtering Accuracy**: The relevance scoring (`score_page_relevance`) is heuristic. It might incorrectly exclude pages with valid biomarkers or include irrelevant pages, although it aims to be inclusive (low threshold). Accuracy depends on the quality of aliases and patterns.
-   **Complex Tables/Layouts**: While the document structure analysis improves handling of tables and layouts, extremely complex or unconventional structures might still cause challenges.
-   **JSON Repair**: While attempts are made to repair malformed JSON from Claude, complex errors might still lead to parsing failures and reliance on the fallback parser for individual pages.
-   **Timeouts**: While sequential processing reduces the likelihood of timeouts caused by large text volume, individual page calls to Claude still have a timeout (currently 10 minutes). Very complex pages or slow API responses could still time out for that specific page, triggering the regex fallback for that page.
-   **Ambiguous Data**: Sometimes data in PDFs is inherently ambiguous (e.g., unclear units, overlapping ranges), which can lead to interpretation errors.
