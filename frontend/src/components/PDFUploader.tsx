import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { pdfService } from '../services/api';

interface PDFUploaderProps {
  onUploadSuccess: (fileId: string, filename: string) => void;
  onUploadError: (error: string) => void;
}

/**
 * PDF uploader component with drag-and-drop functionality
 * Handles file validation, upload, and status display
 */
const PDFUploader: React.FC<PDFUploaderProps> = ({ onUploadSuccess, onUploadError }) => {
  const [uploading, setUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);

  /**
   * Handle file drop event
   */
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    // Only accept one file at a time for simplicity
    const file = acceptedFiles[0];
    if (!file) return;

    // Validate file
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      onUploadError('Only PDF files are accepted');
      return;
    }

    if (file.size > 30 * 1024 * 1024) { // 30MB max size
      onUploadError('File size exceeds the 30MB limit');
      return;
    }

    setUploading(true);
    setUploadProgress(10); // Show initial progress

    try {
      // Simulate progress updates (for UX)
      const progressInterval = setInterval(() => {
        setUploadProgress((prevProgress) => {
          const newProgress = prevProgress + 10;
          return newProgress >= 90 ? 90 : newProgress; // Cap at 90% until complete
        });
      }, 500);

      // Upload the file
      const response = await pdfService.uploadPdf(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      // Handle successful upload
      onUploadSuccess(response.data.file_id, response.data.filename);
    } catch (error) {
      // Handle upload error
      let errorMessage = 'An error occurred during upload';
      if (typeof error === 'object' && error !== null && 'message' in error) {
        errorMessage = (error as { message: string }).message;
      }
      onUploadError(errorMessage);
    } finally {
      setUploading(false);
    }
  }, [onUploadSuccess, onUploadError]);

  // Configure dropzone
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    multiple: false,
    disabled: uploading
  });

  return (
    <div className="w-full max-w-lg mx-auto">
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-500 bg-primary-50'
            : 'border-gray-300 hover:border-primary-400'
        } ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <div className="space-y-4">
            <div className="flex justify-center">
              <svg className="animate-spin h-10 w-10 text-primary-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
            <p className="text-sm text-gray-500">Uploading... {uploadProgress}%</p>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-primary-600 h-2.5 rounded-full transition-all duration-300" 
                style={{ width: `${uploadProgress}%` }}
              ></div>
            </div>
          </div>
        ) : isDragActive ? (
          <div className="space-y-4">
            <svg className="mx-auto h-12 w-12 text-primary-500" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <p className="text-lg font-medium text-primary-600">Drop the PDF here</p>
          </div>
        ) : (
          <div className="space-y-4">
            <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
              <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            <p className="text-lg font-medium text-gray-700">Drag and drop your lab report PDF here</p>
            <p className="text-sm text-gray-500">or click to select a file</p>
            <p className="text-xs text-gray-400 mt-2">Maximum file size: 30MB</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PDFUploader; 