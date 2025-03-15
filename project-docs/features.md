# Vein Diagram: Feature Specifications

## PDF Upload & Processing

### PDF Upload
- **Description**: Allow users to upload PDF lab reports through a drag-and-drop interface or file selector
- **Requirements**:
  - Accept PDF files up to 30MB
  - Provide upload progress indication
  - Validate file type before processing
  - Handle multiple file uploads
- **Edge Cases**:
  - Error handling for corrupted PDFs
  - Timeout management for large files
  - Feedback for unsupported file formats

### Text Extraction
- **Description**: Extract text content from PDF reports using appropriate methods
- **Implementation**:
  - Use PyPDF2 for text-based PDFs
  - Employ Tesseract OCR for image-based PDFs
  - Use Claude API to help parse complex formats
- **Edge Cases**:
  - Handle PDFs with mixed text and images
  - Manage PDFs with unusual layouts
  - Process PDFs with watermarks or headers/footers

### Data Parsing
- **Description**: Identify and extract biomarker names, values, units, and reference ranges
- **Implementation**:
  - Use Claude API to interpret report structure
  - Parse date information from report
  - Categorize biomarkers by type (Blood Count, Metabolic, etc.)
- **Edge Cases**:
  - Variable report formats from different labs
  - Handling abbreviations and alternative biomarker names
  - Identifying units correctly when not explicitly stated

## Visualization Features

### Time-Series Graphs
- **Description**: Generate interactive line charts showing biomarker trends over time
- **Requirements**:
  - Interactive tooltips showing exact values
  - Reference range indicators (shaded areas)
  - Ability to zoom in/out on timeline
  - Toggle display of specific biomarkers
  - Highlight significant changes
- **Edge Cases**:
  - Handling irregular time intervals between tests
  - Displaying multiple units appropriately
  - Managing outliers without distorting visualization

### Correlation Network Graph
- **Description**: Visual network displaying relationships between biomarkers
- **Requirements**:
  - Interactive nodes representing biomarkers
  - Edge thickness indicating correlation strength
  - Color coding for positive/negative correlations
  - Filtering by correlation strength
  - Zooming and panning capabilities
- **Edge Cases**:
  - Managing visual complexity with many biomarkers
  - Handling sparse data with few correlations
  - Preventing misleading correlations with limited data points

### Insights Panel
- **Description**: Display research-backed information about biomarker relationships
- **Requirements**:
  - LLM-generated explanations of correlations
  - Links to relevant educational content
  - Context-sensitive insights based on selected biomarkers
- **Edge Cases**:
  - Ensuring accuracy of generated content
  - Distinguishing between correlation and causation
  - Appropriate disclaimers for health information

## User Interface Features

### Dashboard
- **Description**: Central hub for accessing all reports and visualizations
- **Requirements**:
  - Summary of uploaded reports
  - Quick access to most recent visualizations
  - Upload button prominently displayed
  - Mobile-responsive layout
- **Edge Cases**:
  - Empty state for new users
  - Handling many reports without cluttering UI

### Report Review Interface
- **Description**: Allow users to review and correct parsed data
- **Requirements**:
  - Display extracted biomarker data in editable format
  - Allow manual correction of values or units
  - Confirm successful data storage
- **Edge Cases**:
  - Handling partially extracted data
  - Validating user corrections for data integrity