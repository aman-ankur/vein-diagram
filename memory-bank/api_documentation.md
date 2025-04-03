# Vein Diagram API Documentation

This document provides a high-level overview of the Vein Diagram backend API endpoints. For detailed request/response schemas and interactive testing, refer to the auto-generated FastAPI documentation (usually available at `/docs` when the backend is running).

## Base URL

All API endpoints are relative to `/api`. (e.g., `http://localhost:8000/api/...`)

## Authentication

Authentication is handled via Supabase Auth. The backend API expects a Supabase JWT in the `Authorization: Bearer <token>` header for protected routes. Validation is performed by middleware/dependencies (likely in `app/core/auth.py`). See `authentication_details.md` for more details.

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
*   **`POST /{profile_id}/favorites`**: Add a biomarker name to the profile's favorites list.
    *   Path Param: `profile_id` (UUID string).
    *   Request Body: `AddFavoriteRequest` schema (`{"biomarker_name": "string"}`).
    *   Response: `ProfileResponse` schema (updated profile).
*   **`DELETE /{profile_id}/favorites/{biomarker_name}`**: Remove a biomarker name from the profile's favorites list.
    *   Path Params: `profile_id` (UUID string), `biomarker_name` (string).
    *   Response: `ProfileResponse` schema (updated profile).
*   **`PUT /{profile_id}/favorites/order`**: Update the order of the entire favorites list.
    *   Path Param: `profile_id` (UUID string).
    *   Request Body: `FavoriteOrderUpdate` schema (`{"ordered_favorites": ["string", ...]}`).
    *   Response: `ProfileResponse` schema (updated profile).
*   **`POST /{profile_id}/favorites`**: Add a biomarker name to the profile's favorites list.
    *   Path Param: `profile_id` (UUID string).
    *   Request Body: `AddFavoriteRequest` schema (`{"biomarker_name": "string"}`).
    *   Response: `ProfileResponse` schema (updated profile).
*   **`DELETE /{profile_id}/favorites/{biomarker_name}`**: Remove a biomarker name from the profile's favorites list.
    *   Path Params: `profile_id` (UUID string), `biomarker_name` (string).
    *   Response: `ProfileResponse` schema (updated profile).
*   **`PUT /{profile_id}/favorites/order`**: Update the order of the entire favorites list.
    *   Path Param: `profile_id` (UUID string).
    *   Request Body: `FavoriteOrderUpdate` schema (`{"ordered_favorites": ["string", ...]}`).
    *   Response: `ProfileResponse` schema (updated profile).
*   **`POST /merge`**: Merge multiple source profiles into a single target profile. Re-associates biomarkers/PDFs, deduplicates biomarkers, and deletes source profiles.
    *   Request Body: `ProfileMergeRequest` schema (`{"source_profile_ids": ["uuid", ...], "target_profile_id": "uuid"}`).
    *   Response: `{"message": "Profiles merged successfully"}` (on success).

## PDFs (`/api/pdfs`)

Handles PDF file uploads and status.

*   **`POST /upload`**: Upload a PDF file for processing. Triggers background processing (`process_pdf_background` via FastAPI `BackgroundTasks` without passing the DB session). Handles duplicates based on file hash.
    *   Form Data: `file` (UploadFile), `profile_id` (Optional UUID string).
    *   Response: `PDFResponse` schema (initial status: "pending", uses file hash as `file_id`).
*   **`GET /status/{file_id}`**: Get the processing status and metadata of a specific PDF. Polled by the frontend to track background processing progress.
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
*   **`DELETE /biomarkers/{biomarker_id}`**: Delete a specific biomarker entry by its database ID.
    *   Path Param: `biomarker_id` (integer).
    *   Response: `{"message": "Biomarker deleted successfully"}`.

## Health Score (`/api/health-score`)

Handles calculation and retrieval of a health score based on a profile's biomarkers.

*   **`GET /{profile_id}`**: Calculate and retrieve the health score for a specific profile.
    *   Path Param: `profile_id` (UUID string).
    *   Response: `HealthScoreResponse` schema (containing score, influencing factors, trend, etc.).
*   **`POST /biomarkers/explain`**: Generate AI explanation for a biomarker *without* a database ID (generic request). Uses caching.
    *   Request Body: `BiomarkerExplanationRequest` schema (must include name).
    *   Response: `BiomarkerExplanationResponse`.

## Health Score (`/api/health-score`)

Handles calculation and retrieval of a health score based on a profile's biomarkers.

*   **`GET /{profile_id}`**: Calculate and retrieve the health score for a specific profile.
    *   Path Param: `profile_id` (UUID string).
    *   Response: `HealthScoreResponse` schema (containing score, influencing factors, trend, etc.).

---
**Important Notes & Potential Gaps:**

*   **Profile-Specific Biomarker Retrieval:** The primary way to get biomarkers for a specific user profile (e.g., for history or visualization) is by using the `profile_id` query parameter on the `/api/biomarkers` endpoint. While functional, a dedicated `/api/profiles/{profile_id}/biomarkers` endpoint could be considered for clarity in the future.
*   **PDF ID vs File ID:** The profile matching/association endpoints (`/match`, `/associate`) use `file_id` (the file hash) in their request schemas, aligning with the `file_id` returned by the PDF upload endpoint.
*   **UUID Handling:** Profile routes accept UUIDs as strings in path parameters and internally convert/use them as UUID objects.
*   **Health Score Calculation Details:** The exact calculation logic and influencing factors determination are handled within the backend service (`health_score_service.py`) and not detailed in the API response structure itself beyond the `HealthScoreResponse` schema definition.
