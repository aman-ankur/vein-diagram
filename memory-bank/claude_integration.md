# Vein Diagram: Claude API Integration

This document outlines how the Vein Diagram application integrates with the Anthropic Claude API to enhance functionality.

## Purpose

The Claude API is leveraged for three primary tasks:

1.  **Biomarker Explanations**: Generating user-friendly explanations for specific biomarker results, including general information about the biomarker and context based on the user's specific value and reference range. (Handled by `app/services/llm_service.py`)
2.  **Metadata Extraction**: Extracting structured patient and report metadata (like name, DOB, gender, patient ID, lab name, report date) from the unstructured text content of the ***initial pages*** of uploaded PDF lab reports. This aids in profile matching and data organization. (Handled by `app/services/metadata_parser.py`)
3.  **Biomarker Extraction**: Extracting structured biomarker data (name, value, unit, range, etc.) from the text of ***relevant, filtered pages*** of uploaded PDF lab reports, processed sequentially. (Handled by `app/services/biomarker_parser.py`)

## Configuration

-   **API Key**: The integration requires an Anthropic API key, which must be set in the environment variable `ANTHROPIC_API_KEY` (or `CLAUDE_API_KEY` as a fallback). If the key is not found, the services will use mock/fallback responses.
-   **API Endpoint**: `https://api.anthropic.com/v1/messages`
-   **Anthropic Version Header**: `2023-06-01`

## Models Used

-   **Biomarker Explanations**: `claude-3-haiku-20240307` (Chosen for speed and cost-effectiveness for explanation tasks).
-   **Metadata Extraction**: `claude-3-sonnet-20240229` (Chosen for accuracy in structured data extraction from the initial pages).
-   **Biomarker Extraction (Sequential per page)**: `claude-3-sonnet-20240229` (Chosen for balance of accuracy and capability in extracting structured biomarker data from individual relevant pages).

## Prompting Strategy

### 1. Biomarker Explanations (`llm_service.py`)

-   **Goal**: Generate both a general overview and a personalized interpretation.
-   **Input**: Biomarker name, value, unit, reference range, status (normal/abnormal).
-   **Structure**:
    -   System Prompt: Instructs Claude to act as a helpful medical assistant explaining results in plain language.
    -   User Prompt: Provides the specific biomarker details and requests explanations formatted into `ABOUT_THIS_BIOMARKER:` and `YOUR_RESULTS:` sections, including a medical disclaimer.
-   **Parsing**: The service attempts to parse the response based on the section headers. If parsing fails, it uses fallback logic to split the text.

### 2. Metadata Extraction (`metadata_parser.py`)

-   **Goal**: Extract specific, predefined metadata fields only.
-   **Input**: Preprocessed text content from the *initial pages* of a PDF.
-   **Structure**:
    -   System Prompt: Instructs Claude to act as a metadata extraction expert, focusing *only* on specific fields (lab_name, report_date, patient_name, patient_dob, patient_gender, patient_id, patient_age) and outputting *only* valid JSON in a predefined format (`{"metadata": {...}}`). Explicitly tells Claude to ignore biomarker results.
    -   User Prompt: Provides the preprocessed text fragment from the *initial pages*.
-   **Parsing**: The service uses regex to find the JSON block in the response and `json.loads` to parse it. Includes logic (`_repair_json`) to attempt fixing minor JSON formatting issues before parsing.

### 3. Biomarker Extraction (`biomarker_parser.py`)

-   **Goal**: Extract specific biomarker fields from individual relevant pages.
-   **Input**: Preprocessed text content from a *single, filtered* PDF page.
-   **Structure**:
    -   System Prompt: Instructs Claude to act as a biomarker extraction expert, focusing *only* on biomarker fields (name, original_name, value, original_value, unit, original_unit, reference_range, reference_range_low, reference_range_high, category, is_abnormal, confidence) and outputting *only* valid JSON in a predefined format (`{"biomarkers": [...]}`). Explicitly tells Claude to ignore metadata and non-biomarker text.
    -   User Prompt: Provides the preprocessed text from the single page.
-   **Parsing**: The service uses regex to find the JSON block in the response and `json.loads` to parse it. Includes extensive logic (`_repair_json`, `_fix_truncated_json`) to attempt fixing JSON formatting issues.
-   **Sequential Processing**: This extraction is called sequentially for each relevant page identified by the filtering process in `pdf_service.py`.

## Caching (Biomarker Explanations Only)

-   An in-memory cache (`ExplanationCache` in `llm_service.py`) is used to store generated explanations and reduce redundant API calls.
    -   **General Explanations**: Cached per biomarker name. TTL: 30 days.
    -   **Specific Explanations**: Cached per unique combination of biomarker name, value, and status. TTL: 7 days.
-   *Note: This is a simple in-memory cache suitable for development. A persistent cache like Redis would be needed for production.*

## Error Handling & Fallbacks

-   **API Key Missing**: Logs a warning and returns mock/placeholder responses.
-   **API Errors (HTTP Status != 200)**: Logs the error and returns generic "unavailable" messages.
-   **Timeout**:
    -   Metadata extraction uses a `with_timeout` decorator (45 seconds) and returns an empty dictionary on timeout.
    -   Biomarker explanation uses `httpx` client timeout (30 seconds) and returns "unavailable" messages on timeout.
    -   Biomarker extraction (per page) uses a `with_timeout` decorator (600 seconds / 10 minutes *per page*) and falls back to the regex parser (`parse_biomarkers_from_text`) for that specific page on timeout.
-   **Request Errors (`httpx.RequestError`)**: Logs the error and returns "unavailable" messages or an empty dictionary/list.
-   **Response Parsing Errors**:
    -   Explanation: Logs the error and attempts fallback splitting or returns generic messages.
    -   Metadata: Logs the error, attempts JSON repair, and returns an empty dictionary if parsing/repair fails.
    -   Biomarker Extraction (per page): Logs the error, attempts extensive JSON repair, and falls back to the regex parser for that specific page if parsing/repair fails.
-   **Unexpected Errors**: Catches general exceptions, logs them, and returns generic error messages/empty dictionaries/lists.
-   **Fallback Parser (Biomarker Extraction)**: If Claude API calls fail for biomarker extraction on a specific page (timeout, errors, invalid JSON), the system falls back to a regex-based parser (`parse_biomarkers_from_text`) for *that page only*.

## Key Considerations

-   **Cost**: API calls incur costs. Sequential processing for biomarker extraction might increase the number of calls compared to a single large call, but reduces token usage per call and avoids wasted processing on irrelevant pages. Caching (for explanations) and using faster models like Haiku help mitigate costs. Prompt optimization is ongoing.
-   **Latency**: API calls add latency. Metadata extraction is done early. Sequential biomarker extraction processes pages one by one, potentially increasing overall wall-clock time for biomarker extraction compared to a single (potentially failing) large call, but provides incremental progress and avoids complete failure due to timeouts on large inputs.
-   **Accuracy**: Extraction accuracy depends heavily on prompt quality and the model's capabilities for both metadata and biomarkers. The page filtering step might occasionally miss relevant pages or include irrelevant ones. Fallback mechanisms (regex parser) have lower accuracy.
-   **Rate Limits**: Production usage may require handling API rate limits, especially with sequential calls.
-   **Prompt Engineering**: The effectiveness relies on carefully crafted prompts instructing the model on the desired output format and content for each task (metadata, biomarkers per page, explanations).
