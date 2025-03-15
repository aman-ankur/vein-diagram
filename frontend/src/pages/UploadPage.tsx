import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Header from '../components/Header';
import Footer from '../components/Footer';
import PDFUploader from '../components/PDFUploader';
import ProcessingStatus from '../components/ProcessingStatus';
import UploadGuide from '../components/UploadGuide';
import { pdfService } from '../services/api';

/**
 * Page for uploading and processing PDF lab reports
 */
const UploadPage: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [uploadedFileId, setUploadedFileId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<'pending' | 'processing' | 'completed' | 'error' | 'timeout' | null>(null);

  /**
   * Handle successful upload
   */
  const handleUploadSuccess = async (fileId: string, filename: string) => {
    setError(null);
    setUploadedFileId(fileId);
    setSuccessMessage(`Successfully uploaded ${filename}`);
    setProcessingStatus('processing');

    // Poll for the processing status
    try {
      await pollProcessingStatus(fileId);
    } catch (err) {
      setError('Error checking processing status');
      setProcessingStatus('error');
    }
  };

  /**
   * Poll the processing status of the uploaded file
   */
  const pollProcessingStatus = async (fileId: string) => {
    // Poll every 2 seconds
    const pollInterval = setInterval(async () => {
      try {
        const response = await pdfService.getPdfStatus(fileId);
        if (response.data.status === 'processed') {
          clearInterval(pollInterval);
          setProcessingStatus('completed');
          // We could navigate to a visualization page here in the future
        } else if (response.data.status === 'error') {
          clearInterval(pollInterval);
          setProcessingStatus('error');
          setError(response.data.error_message || 'An error occurred during processing');
        }
      } catch (error) {
        clearInterval(pollInterval);
        setProcessingStatus('error');
        throw error;
      }
    }, 2000);

    // Set a timeout to stop polling after 2 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (processingStatus === 'processing') {
        setProcessingStatus('timeout');
        setError('Processing is taking longer than expected. Please check back later.');
      }
    }, 2 * 60 * 1000);
  };

  /**
   * Handle upload errors
   */
  const handleUploadError = (errorMessage: string) => {
    setError(errorMessage);
    setSuccessMessage(null);
    setProcessingStatus(null);
  };

  /**
   * Navigate to visualizations or upload another file
   */
  const handleContinue = () => {
    if (uploadedFileId && processingStatus === 'completed') {
      // In the future, navigate to visualization page with the uploadedFileId
      navigate('/');
    } else {
      // Reset state to allow uploading another file
      setError(null);
      setSuccessMessage(null);
      setUploadedFileId(null);
      setProcessingStatus(null);
    }
  };

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      <main className="flex-grow container mx-auto px-4 py-8">
        <section className="max-w-3xl mx-auto">
          <h1 className="text-3xl font-bold text-center mb-8">Upload Lab Report</h1>
          
          {/* Success/error message */}
          {error && (
            <div className="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {successMessage && (
            <div className="bg-green-50 border-l-4 border-green-500 p-4 mb-6">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-green-700">{successMessage}</p>
                </div>
              </div>
            </div>
          )}

          {/* Processing status */}
          <ProcessingStatus status={processingStatus} errorMessage={error || undefined} />

          {/* Show uploader only if not currently processing */}
          {(!processingStatus || processingStatus === 'error' || processingStatus === 'timeout') && (
            <div className="card mb-8">
              <h2 className="text-xl font-semibold mb-4">Upload your PDF lab report</h2>
              <p className="text-gray-600 mb-6">
                Drag and drop your lab report PDF file below, or click to select a file from your computer.
                We support lab reports from major providers like Quest Diagnostics and LabCorp.
              </p>
              <PDFUploader 
                onUploadSuccess={handleUploadSuccess} 
                onUploadError={handleUploadError} 
              />
            </div>
          )}

          {/* Continue button after processing completes */}
          {(processingStatus === 'completed' || processingStatus === 'error' || processingStatus === 'timeout') && (
            <div className="text-center mt-8">
              <button 
                onClick={handleContinue}
                className="btn btn-primary"
              >
                {processingStatus === 'completed' ? 'View Results' : 'Upload Another File'}
              </button>
            </div>
          )}

          {/* Upload Guide */}
          <UploadGuide />
        </section>
      </main>
      <Footer />
    </div>
  );
};

export default UploadPage; 