
```markdown
# Vein Diagram: User Flow

## Core User Journey

```mermaid
flowchart TD
    A[User Lands on Homepage] --> B[Uploads PDF Lab Report]
    B --> C[System Processes Report]
    C --> D[User Reviews Extracted Data]
    D --> E{Data Correct?}
    E -->|Yes| F[View Time-Series Visualizations]
    E -->|No| G[Edit Extracted Data]
    G --> F
    F --> H[Explore Correlation Network]
    H --> I[Review Insights]
    I --> J[Upload Another Report]
    J --> B





Detailed User Flows
1. Initial Report Upload Flow

User lands on the dashboard

Views empty state with upload prompt
Clicks "Upload Lab Report" button


Report upload

Selects PDF from their device or drops file in upload area
Views upload progress indicator
System validates file format


Processing phase

Backend extracts text using PyPDF2 and/or Tesseract OCR
Claude API parses text into structured biomarker data
User sees processing indicator


Review extracted data

System displays parsed biomarkers with names, values, and units
User can manually correct any errors
User confirms data is correct


Initial visualization display

System generates single-point time-series chart
User views basic biomarker information
System prompts to upload more reports for trend analysis



2. Subsequent Report Upload Flow

User uploads additional report

Selects new PDF
System processes as before
User reviews and confirms extracted data


Enhanced visualization display

Time-series charts now show trends across multiple dates
System highlights significant changes
Correlation network becomes available with sufficient data


Visualization exploration

User toggles between different biomarkers
User zooms in/out on time periods
User explores correlation strength between markers



3. Insights Exploration Flow

User selects biomarker or correlation

Clicks on specific biomarker in time-series
Clicks on connection in correlation network


Insights generation

System queries Claude API with biomarker information
Backend generates research-backed explanation
User views insight panel with explanations


Educational content access

User clicks to learn more about specific biomarkers
System displays educational information
User returns to visualizations with better understanding