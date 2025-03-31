# Vein Diagram: Claude API Integration

This document outlines how the Vein Diagram application integrates with the Anthropic Claude API to enhance functionality.

## Purpose

The Claude API is leveraged for two primary tasks:

1.  **Biomarker Explanations**: Generating user-friendly explanations for specific biomarker results, including general information about the biomarker and context based on the user's specific value and reference range. (Handled by `app/services/llm_service.py`)
2.  **Metadata Extraction**: Extracting structured patient and report metadata (like name, DOB, gender, patient ID, lab name, report date) from the unstructured text content of uploaded PDF lab reports. This aids in profile matching and data organization. (Handled by `app/services/metadata_parser.py`)

## Configuration

-   **API Key**: The integration requires an Anthropic API key, which must be set in the environment variable `ANTHROPIC_API_KEY` (or `CLAUDE_API_KEY` as a fallback). If the key is not found, the services will use mock/fallback responses.
-   **API Endpoint**: `https://api.anthropic.com/v1/messages`
-   **Anthropic Version Header**: `2023-06-01`

## Models Used

-   **Biomarker Explanations**: `claude-3-haiku-20240307` (Chosen for speed and cost-effectiveness for explanation tasks).
-   **Metadata Extraction**: `claude-3-sonnet-20240229` (Chosen for potentially better accuracy in structured data extraction from text).

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
-   **Input**: Preprocessed text content from a PDF page.
-   **Structure**:
    -   System Prompt: Instructs Claude to act as a metadata extraction expert, focusing *only* on specific fields (lab_name, report_date, patient_name, patient_dob, patient_gender, patient_id, patient_age) and outputting *only* valid JSON in a predefined format (`{"metadata": {...}}`). Explicitly tells Claude to ignore biomarker results.
    -   User Prompt: Provides the preprocessed text fragment.
-   **Parsing**: The service uses regex to find the JSON block in the response and `json.loads` to parse it. Includes logic (`_repair_json`) to attempt fixing minor JSON formatting issues before parsing.

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
-   **Request Errors (`httpx.RequestError`)**: Logs the error and returns "unavailable" messages or an empty dictionary.
-   **Response Parsing Errors**:
    -   Explanation: Logs the error and attempts fallback splitting or returns generic messages.
    -   Metadata: Logs the error, attempts JSON repair, and returns an empty dictionary if parsing/repair fails.
-   **Unexpected Errors**: Catches general exceptions, logs them, and returns generic error messages/empty dictionaries.

## Key Considerations

-   **Cost**: API calls incur costs. Caching and using faster models like Haiku help mitigate this. Prompt optimization is ongoing.
-   **Latency**: API calls add latency, especially for metadata extraction during profile matching. Timeouts are implemented. Background tasks are used for caching updates.
-   **Accuracy**: Extraction and explanation accuracy depend heavily on prompt quality and the model's capabilities. Fallback mechanisms (like pattern matching for biomarkers, although not detailed here) might exist elsewhere.
-   **Rate Limits**: Production usage may require handling API rate limits.
-   **Prompt Engineering**: The effectiveness relies on carefully crafted prompts instructing the model on the desired output format and content.
