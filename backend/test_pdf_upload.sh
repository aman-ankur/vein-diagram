#!/bin/bash
# Script to test the PDF upload and biomarker extraction process end-to-end

# Check if a PDF file is provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <path_to_pdf_file>"
    echo "Example: $0 sample_reports/lab_report.pdf"
    exit 1
fi

PDF_FILE=$1
if [ ! -f "$PDF_FILE" ]; then
    echo "Error: File '$PDF_FILE' not found"
    exit 1
fi

echo "Testing PDF upload and biomarker extraction with file: $PDF_FILE"

# Step 1: Upload the PDF
echo "Step 1: Uploading PDF file..."
UPLOAD_RESPONSE=$(curl -s -X POST -F "file=@$PDF_FILE" http://localhost:8000/api/pdf/upload)
FILE_ID=$(echo $UPLOAD_RESPONSE | grep -o '"file_id":"[^"]*"' | cut -d':' -f2 | tr -d '"')

if [ -z "$FILE_ID" ]; then
    echo "Failed to upload PDF. Response: $UPLOAD_RESPONSE"
    exit 1
fi

echo "Successfully uploaded PDF. File ID: $FILE_ID"

# Step 2: Check processing status
echo "Step 2: Checking processing status..."
MAX_TRIES=30
for i in $(seq 1 $MAX_TRIES); do
    STATUS_RESPONSE=$(curl -s http://localhost:8000/api/pdf/status/$FILE_ID)
    STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d':' -f2 | tr -d '"')
    
    echo "Processing status: $STATUS"
    
    if [ "$STATUS" = "completed" ]; then
        echo "PDF processing completed successfully!"
        break
    elif [ "$STATUS" = "error" ]; then
        echo "Error processing PDF. Details: $STATUS_RESPONSE"
        exit 1
    fi
    
    if [ $i -eq $MAX_TRIES ]; then
        echo "Timeout waiting for processing to complete"
        exit 1
    fi
    
    echo "Waiting for processing to complete... ($i/$MAX_TRIES)"
    sleep 2
done

# Step 3: Retrieve biomarkers
echo "Step 3: Retrieving extracted biomarkers..."
BIOMARKERS_RESPONSE=$(curl -s http://localhost:8000/api/biomarkers/pdf/$FILE_ID)
BIOMARKER_COUNT=$(echo $BIOMARKERS_RESPONSE | grep -o '\[' | wc -l)

echo "Retrieved $BIOMARKER_COUNT biomarkers"

# Step 4: Get PDF metadata
echo "Step 4: Retrieving PDF metadata..."
PDF_RESPONSE=$(curl -s http://localhost:8000/api/pdf/$FILE_ID)
echo "PDF metadata: $PDF_RESPONSE"

# Step 5: Show a sample of biomarkers
echo "Step 5: Sample of extracted biomarkers:"
echo $BIOMARKERS_RESPONSE | python3 -m json.tool | head -n 20

echo "Test completed successfully!" 