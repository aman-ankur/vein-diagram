import React from 'react';

interface ProcessingStatusProps {
  status: 'pending' | 'processing' | 'completed' | 'error' | 'timeout' | null;
  errorMessage?: string;
}

/**
 * Component to display the processing status of an uploaded PDF
 */
const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ status, errorMessage }) => {
  if (!status) return null;

  return (
    <div className="my-6">
      {status === 'pending' && (
        <div className="flex items-center justify-center space-x-2 text-yellow-600">
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>Your file is in the queue and will be processed shortly...</p>
        </div>
      )}
      
      {status === 'processing' && (
        <div className="flex items-center justify-center space-x-2 text-primary-600">
          <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p>Processing your lab report...</p>
        </div>
      )}
      
      {status === 'completed' && (
        <div className="flex items-center justify-center space-x-2 text-green-600">
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
          <p>Processing completed successfully!</p>
        </div>
      )}
      
      {status === 'error' && (
        <div className="flex items-center justify-center space-x-2 text-red-600">
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>{errorMessage || 'An error occurred while processing your file.'}</p>
        </div>
      )}
      
      {status === 'timeout' && (
        <div className="flex items-center justify-center space-x-2 text-yellow-600">
          <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <p>Processing is taking longer than expected. We'll notify you when it's complete.</p>
        </div>
      )}
    </div>
  );
};

export default ProcessingStatus; 