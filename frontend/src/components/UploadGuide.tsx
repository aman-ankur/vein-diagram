import React from 'react';

/**
 * Component to explain PDF upload requirements and supported formats
 */
const UploadGuide: React.FC = () => {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-lg p-6 mt-8">
      <h3 className="text-lg font-semibold text-blue-800 mb-3">Lab Report Upload Guide</h3>
      
      <div className="space-y-4 text-sm text-blue-700">
        <div>
          <h4 className="font-medium mb-1">Supported Lab Providers</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li>Quest Diagnostics</li>
            <li>LabCorp</li>
            <li>BioReference Laboratories</li>
            <li>Mayo Clinic Laboratories</li>
            <li>Most hospital and clinic lab reports</li>
          </ul>
        </div>
        
        <div>
          <h4 className="font-medium mb-1">File Requirements</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li>PDF format only (.pdf extension)</li>
            <li>Maximum file size: 30MB</li>
            <li>Both text-based and image-based PDFs are supported</li>
            <li>File should not be password-protected or encrypted</li>
          </ul>
        </div>
        
        <div>
          <h4 className="font-medium mb-1">Processing Time</h4>
          <p>
            Most lab reports are processed within 30 seconds. Image-based PDFs requiring OCR
            may take longer to process. Very complex reports may take up to 2 minutes.
          </p>
        </div>
        
        <div>
          <h4 className="font-medium mb-1">Tips for Best Results</h4>
          <ul className="list-disc pl-5 space-y-1">
            <li>Use the original PDF file from your lab provider</li>
            <li>Ensure the file contains clear text and is not scanned at a low resolution</li>
            <li>Upload the complete report including reference ranges</li>
            <li>Reports should include test date, your name, and lab name for best results</li>
          </ul>
        </div>
        
        <div>
          <h4 className="font-medium mb-1">Privacy & Security</h4>
          <p>
            Your lab reports are processed securely. We extract only biomarker data, dates, and
            reference ranges. Personal identifying information is not stored in our database.
          </p>
        </div>
      </div>
    </div>
  );
};

export default UploadGuide; 