# Feature Request: Biomarker View Modes - Current PDF vs. Profile History

## Overview

Enhance the biomarker results view to provide users with two distinct viewing modes:
1. **Current PDF View** - Shows only biomarkers extracted from the most recently processed PDF
2. **Profile History View** - Shows all historical biomarkers for the associated profile

## Business Value

- Improves user experience by reducing information overload after processing a new PDF
- Enables users to easily compare current results with historical data
- Maintains access to comprehensive patient history while focusing on recent results

## User Stories

**As a user:**
- I want to see only the biomarkers from the PDF I just uploaded by default
- I want to easily switch to viewing all historical biomarkers for this profile
- I want the system to clearly indicate which viewing mode I'm currently using
- I want to navigate between these views without losing context

## Technical Requirements

### Backend Integration
- Utilize existing API endpoints:
 - `/api/pdf/{file_id}/biomarkers` - For current PDF view
 - `/api/biomarkers?profile_id={profileId}` - For profile history view

### Frontend Components

1. **View Toggle Component**
  - Implement a toggle control (segmented buttons, tabs, or dropdown)
  - Clearly label options: "Current Results" and "Profile History"
  - Visually indicate active selection
  - Position prominently at the top of the results page

2. **Results Header Component**
  - Display contextual information based on current view:
    - Current PDF: "Showing results from [PDF filename] ([date])"
    - History: "Showing all biomarker history for [profile name]"

3. **State Management**
  - Add view mode to application state
  - Preserve state during navigation
  - Update URL to reflect current view (e.g., `/results/{pdfId}?view=history`)

### UI/UX Design

1. **Default View**
  - After PDF processing completes, default to "Current Results" view
  - Display only biomarkers from the most recently processed PDF

2. **Profile History View**
  - Add source information for each biomarker (PDF name, date)
  - Consider grouping by test date or source PDF
  - Include visual indicators for trends over time

3. **Navigation**
  - Ensure browser back/forward buttons respect view mode
  - Maintain view preference during session

## Implementation Details

```typescript
// State management interface
interface BiomarkerViewState {
 mode: 'current' | 'history';
 currentPdfId: string;
 profileId: string;
}

// API functions
async function fetchCurrentPdfBiomarkers(pdfId: string) {
 return fetch(`/api/pdf/${pdfId}/biomarkers`).then(res => res.json());
}

async function fetchProfileBiomarkers(profileId: string) {
 return fetch(`/api/biomarkers?profile_id=${profileId}`).then(res => res.json());
}

// Component props
interface ResultsViewProps {
 profileId: string;
 currentPdfId: string;
 initialViewMode?: 'current' | 'history';
}