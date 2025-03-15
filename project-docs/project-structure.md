# Vein Diagram: Project Structure

## System Architecture

The Vein Diagram application follows a three-tier architecture:

```mermaid
graph LR
    Frontend -->|API Calls| Backend
    Backend -->|Database Operations| Database
    Backend -->|OCR Processing| OCR Service
    Backend -->|LLM Queries| LLM Service