# Vein Diagram API Documentation

This document provides a high-level overview of the Vein Diagram backend API endpoints. For detailed request/response schemas and interactive testing, refer to the auto-generated FastAPI documentation (usually available at `/docs` when the backend is running).

## Base URL

All API endpoints are relative to `/api`. (e.g., `http://localhost:8000/api/...`)

## Authentication

*Currently, there is no authentication implemented (MVP stage).*

## Profiles (`/api/profiles`)

Handles management of user profiles.

*   **`POST /`**: Create a new profile.
    *   Request Body: `ProfileCreate` schema (name, dob, gender, patient_id).
    *   Response: `ProfileResponse` schema (including counts).
*   **`GET /`**: List all profiles with pagination and optional search.
    *   Query Params: `skip`, `limit`, `search` (by name or patient_id).
    *   Response: `ProfileList` schema.
*   **`GET /{profile_id}`**: Get details of a specific profile.
    *   Path Param: `profile_id` (UUID string).
    *   Response: `ProfileResponse` schema.
*   **`PUT /{profile_id}`**: Update an existing profile.
    *   Path Param: `profile_id` (UUID string).
    *   Request Body: `ProfileUpdate` schema (optional fields).
    *   Response: `ProfileResponse` schema.
*   **`DELETE /{profile_id}`**: Delete a profile (unlinks associated PDFs/Biomarkers).
    *   Path Param: `profile_id` (UUID string).
    *   Response: `204 No Content`.
*   **`POST /match`**: Extract metadata from a PDF (using Claude if needed) and find matching profiles.
    *   Request Body: `ProfileMatchingRequest` schema (pdf_id - *Note: seems to use `file_id` hash based on code*).
    *   Response: `ProfileMatchingResponse` schema (list of matches with confidence scores, extracted metadata).
*   **`POST /associate`**: Associate a PDF with an existing profile or create a new profile from PDF metadata.
    *   Request Body: `ProfileAssociationRequest` schema (pdf_id - *Note: seems to use `file_id` hash based on code*, profile_id OR create_new_profile, optional metadata_updates).
    *   Response: `ProfileResponse` schema of the associated/created profile.

## PDFs (`/api/pdfs`)

Handles PDF file uploads and status.

*   **`POST /upload`**: Upload a PDF file for processing. Triggers background processing. Handles duplicates based on file hash.
    *   Form Data: `file` (UploadFile), `profile_id` (Optional UUID string).
    *   Response: `PDFResponse` schema (initial status: "pending", uses file hash as `file_id`).
*   **`GET /status/{file_id}`**: Get the processing status and metadata of a specific PDF.
    *   Path Param: `file_id` (File hash).
    *   Response: `PDFStatusResponse` schema.
*   **`GET /list`**: List all uploaded PDFs and their status.
    *   Response: `PDFListResponse` schema.
*   **`DELETE /{file_id}`**: Delete a PDF file record and the file from storage.
    *   Path Param: `file_id` (File hash).
    *   Response: Success message.

## Biomarkers (`/api/biomarkers`, `/api/pdf/{file_id}/biomarkers`)

Handles retrieval and explanation of biomarker data.

*   **`GET /pdf/{file_id}/biomarkers`**: Get biomarkers associated with a specific PDF *file*.
    *   Path Param: `file_id` (File hash).
    *   Query Param: `profile_id` (Optional UUID string).
    *   Response: List of `BiomarkerResponse`.
*   **`GET /biomarkers`**: Get *all* biomarkers across the system, with optional category/profile filtering and pagination.
    *   Query Params: `category`, `profile_id` (Optional UUID string), `limit`, `offset`.
    *   Response: List of `BiomarkerResponse`.
*   **`GET /biomarkers/categories`**: Get a list of unique biomarker categories present in the database.
    *   Response: List of strings.
*   **`GET /biomarkers/search`**: Search for biomarkers by name, optionally filtered by profile.
    *   Query Params: `query`, `profile_id` (Optional UUID string), `limit`.
    *   Response: List of `BiomarkerResponse`.
*   **`GET /biomarkers/{biomarker_id}`**: Get a specific biomarker by its database ID.
    *   Path Param: `biomarker_id` (integer).
    *   Response: `BiomarkerResponse`.
*   **`POST /biomarkers/{biomarker_id}/explain`**: Generate AI explanation for a specific biomarker entry using its database ID. Uses caching.
    *   Path Param: `biomarker_id` (integer).
    *   Request Body: `BiomarkerExplanationRequest` schema.
    *   Response: `BiomarkerExplanationResponse`.

## Health Score (`/api/health-score`)

Handles calculation and retrieval of a health score based on a profile's biomarkers.

*   **`GET /{profile_id}`**: Calculate and retrieve the health score for a specific profile.
    *   Path Param: `profile_id` (UUID string).
    *   Response: `HealthScoreResponse` schema (containing score, influencing factors, trend, etc.).
*   **`POST /biomarkers/explain`**: Generate AI explanation for a biomarker *without* a database ID (generic request). Uses caching.
    *   Request Body: `BiomarkerExplanationRequest` schema (must include name).
    *   Response: `BiomarkerExplanationResponse`.

---
**Important Notes & Potential Gaps:**

*   **Profile-Specific Biomarker Retrieval:** The primary way to get biomarkers for a specific user profile (e.g., for history or visualization) seems to be missing a dedicated endpoint like `/api/profiles/{profile_id}/biomarkers`. Currently, one might filter `/api/biomarkers` or `/api/pdf/{file_id}/biomarkers` by `profile_id`, but a direct profile endpoint would be cleaner.
*   **Favorite Biomarker Endpoints:** Endpoints for managing favorite biomarkers (GET, POST, DELETE favorites for a profile) are not present in the reviewed files and would need to be added to fully support the favorites feature. *(Self-correction: These likely exist under `/api/profiles/{profile_id}/favorites` but weren't explicitly documented here initially).*
*   **PDF ID vs File ID:** The profile matching/association endpoints (`/match`, `/associate`) seem to use `pdf_id` in their request schemas, but the PDF upload endpoint returns a `file_id` (which is the file hash). This needs clarification or alignment. It's likely they should consistently use the `file_id` (hash).
*   **UUID Handling:** Profile routes seem to accept UUIDs as strings in path parameters.
*   **Health Score Calculation Details:** The exact calculation logic and influencing factors determination are handled within the backend service and not detailed in the API response structure itself beyond the schema definition.
