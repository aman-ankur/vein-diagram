Data Flow:

User uploads PDF through the frontend
Backend processes PDF using PyPDF2 and/or Tesseract OCR
Extracted text is sent to Claude API for structured data parsing
Parsed data is stored in SQLite database
Frontend requests visualization data via API
Backend generates visualization data and returns to frontend
Frontend renders interactive visualizations using Plotly.js