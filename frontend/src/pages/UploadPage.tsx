import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Paper, 
  Button, 
  Container, 
  CircularProgress,
  Alert,
  AlertTitle,
  Snackbar,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Card,
  CardContent,
  LinearProgress,
  useTheme
} from '@mui/material';
import { useDropzone } from 'react-dropzone';
import { CloudUpload as CloudUploadIcon, CheckCircle as CheckCircleIcon, Error as ErrorIcon } from '@mui/icons-material';
import { uploadPDF, getPDFStatus } from '../services/api';
import { getUploadHistory, saveUploadHistory } from '../services/localStorage';
import { MAX_FILE_SIZE, SUPPORTED_FILE_TYPES, STATUS_CHECK_INTERVAL } from '../config';
import { FilePreview } from '../components/FilePreview';
import { UploadResponse, ProcessingStatus } from '../types/pdf';

const steps = [
  {
    label: 'Select file',
    description: 'Drag and drop a PDF file or click to upload.',
  },
  {
    label: 'Upload file',
    description: 'File will be uploaded to the server for processing.',
  },
  {
    label: 'Process file',
    description: 'Server will extract biomarkers from the PDF.',
  },
  {
    label: 'Complete',
    description: 'Processing complete! You can now view the results.',
  },
];

const UploadPage: React.FC = () => {
  const theme = useTheme();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadResponse, setUploadResponse] = useState<UploadResponse | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [uploadHistory, setUploadHistory] = useState<UploadResponse[]>([]);
  
  const pollingRef = useRef<NodeJS.Timeout | null>(null);
  const navigate = useNavigate();

  // Load upload history from localStorage
  useEffect(() => {
    try {
      const history = getUploadHistory();
      if (Array.isArray(history)) {
        setUploadHistory(history);
      } else {
        console.error('Invalid upload history format:', history);
        setUploadHistory([]); // Fallback to empty array
      }
    } catch (error) {
      console.error('Error loading upload history:', error);
      setUploadHistory([]); // Fallback to empty array
    }
  }, []);

  // Clear polling interval on unmount
  useEffect(() => {
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current);
      }
    };
  }, []);

  // File selection handling
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const selectedFile = acceptedFiles[0];
      
      // Validate file type
      if (!SUPPORTED_FILE_TYPES.includes(selectedFile.type)) {
        setError(`Unsupported file type. Please upload a PDF file.`);
        setSnackbarOpen(true);
        return;
      }
      
      // Validate file size
      if (selectedFile.size > MAX_FILE_SIZE) {
        setError(`File is too large. Maximum size is ${MAX_FILE_SIZE / 1000000}MB.`);
        setSnackbarOpen(true);
        return;
      }
      
      setFile(selectedFile);
      setActiveStep(1);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
    },
    maxFiles: 1,
    disabled: uploading || isPolling
  });

  // File upload handling
  const handleUpload = async () => {
    if (!file) return;
    
    try {
      setUploading(true);
      setError(null);
      setUploadProgress(0);
      
      console.log('Uploading file:', file.name);
      
      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 500);
      
      try {
        const response = await uploadPDF(file);
        console.log('Upload response:', response);
        
        // Set upload progress to 100% on success
        setUploadProgress(100);
        
        // Validate response contains fileId
        if (!response || !response.fileId) {
          throw new Error('Invalid response from server: Missing fileId in upload response');
        }
        
        setUploadResponse(response);
        
        // Save to localStorage history
        try {
          // Ensure uploadHistory is an array before spreading it
          const existingHistory = Array.isArray(uploadHistory) ? uploadHistory : [];
          const newHistory = [response, ...existingHistory];
          saveUploadHistory(newHistory.slice(0, 10)); // Keep only 10 most recent
          setUploadHistory(newHistory);
        } catch (historyError) {
          console.error('Error updating upload history:', historyError);
          // Continue with upload process even if history update fails
        }
        
        // Move to the next step
        setActiveStep(2);
        
        // Start polling for status
        startStatusPolling(response.fileId);
      } catch (uploadError: any) {
        console.error('Upload API error:', uploadError);
        
        // Check for specific error types
        let errorMessage = 'Failed to upload file. Please try again.';
        
        if (uploadError.status === 413) {
          errorMessage = 'File is too large. Maximum size is 30MB.';
        } else if (uploadError.status === 415) {
          errorMessage = 'Invalid file type. Only PDF files are accepted.';
        } else if (uploadError.status === 400) {
          errorMessage = uploadError.message || 'Invalid request. Please check your file.';
        } else if (uploadError.status === 500) {
          errorMessage = 'Server error. The system is currently unable to process your file.';
        } else if (uploadError.isNetworkError) {
          errorMessage = 'Network error. Please check your internet connection and try again.';
        } else if (uploadError.message) {
          errorMessage = uploadError.message;
        }
        
        setError(errorMessage);
        setSnackbarOpen(true);
      } finally {
        clearInterval(progressInterval);
        setUploadProgress(0);
      }
    } catch (error: any) {
      console.error('Unexpected upload error:', error);
      setError(error.message || 'An unexpected error occurred. Please try again.');
      setSnackbarOpen(true);
    } finally {
      setUploading(false);
    }
  };

  // Poll for processing status
  const startStatusPolling = (fileId: string) => {
    if (!fileId || fileId === 'undefined') {
      console.error('Invalid fileId provided to startStatusPolling:', fileId);
      setError('Missing file ID. Upload may have failed.');
      setSnackbarOpen(true);
      return;
    }
    
    console.log('Starting status polling for fileId:', fileId);
    setIsPolling(true);
    setRetryCount(0);
    
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
    
    const checkStatus = async () => {
      try {
        const status = await getPDFStatus(fileId);
        console.log('Status update:', status);
        setProcessingStatus(status);
        
        // If completed or processed or failed, stop polling
        if (status.status === 'completed' || status.status === 'processed') {
          console.log('Processing complete! Status:', status.status);
          clearInterval(pollingRef.current!);
          setIsPolling(false);
          setActiveStep(3);
        } else if (status.status === 'failed' || status.status === 'error') {
          console.log('Processing failed! Status:', status.status);
          clearInterval(pollingRef.current!);
          setIsPolling(false);
          setError(`Processing failed: ${status.error || 'Unknown error'}`);
          setSnackbarOpen(true);
        } else {
          console.log('Still processing. Current status:', status.status);
        }
      } catch (error: any) {
        console.error('Status check error:', error);
        setRetryCount(prev => prev + 1);
        
        // Show a more user-friendly error based on error type
        let errorMessage = 'Error checking processing status.';
        
        if (error.status === 404) {
          errorMessage = 'PDF file not found on server. It may have been deleted or expired.';
        } else if (error.status === 500) {
          errorMessage = 'Server error while checking status. Please try again later.';
        } else if (error.isNetworkError) {
          errorMessage = 'Network error. Please check your internet connection.';
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        // Stop after 5 failed retries
        if (retryCount >= 5) {
          clearInterval(pollingRef.current!);
          setIsPolling(false);
          setError(`${errorMessage} Maximum retry attempts reached.`);
          setSnackbarOpen(true);
        } else if (retryCount >= 2) {
          // Show error message after a few retries, but continue polling
          setError(errorMessage);
          setSnackbarOpen(true);
        }
      }
    };
    
    // Check immediately
    checkStatus();
    
    // Then set up interval for subsequent checks
    pollingRef.current = setInterval(checkStatus, STATUS_CHECK_INTERVAL);
  };

  const handleViewResults = () => {
    if (uploadResponse) {
      navigate(`/visualization?fileId=${uploadResponse.fileId}`);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadResponse(null);
    setProcessingStatus(null);
    setActiveStep(0);
    setError(null);
    setIsPolling(false);
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
    }
  };

  const handleSnackbarClose = () => {
    setSnackbarOpen(false);
  };

  const renderStepContent = (step: number) => {
    switch (step) {
      case 0:
        return (
          <Box sx={{ mt: 2 }}>
            <Paper
              {...getRootProps()}
              sx={{
                border: '2px dashed',
                borderColor: isDragActive ? 'primary.main' : 'grey.400',
                borderRadius: 2,
                p: 6,
                textAlign: 'center',
                backgroundColor: isDragActive ? 'rgba(0, 0, 0, 0.04)' : 'transparent',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                '&:hover': {
                  backgroundColor: 'rgba(0, 0, 0, 0.04)',
                  borderColor: 'primary.main',
                },
              }}
            >
              <input {...getInputProps()} />
              <CloudUploadIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {isDragActive ? 'Drop the files here...' : 'Drag & drop files here'}
              </Typography>
              <Typography variant="body2" color="textSecondary">
                or click to select files
              </Typography>
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 1 }}>
                Supported file types: PDF (Max size: {MAX_FILE_SIZE / 1000000}MB)
              </Typography>
            </Paper>
            
            {uploadHistory.length > 0 && (
              <Box sx={{ mt: 4 }}>
                <Typography variant="h6" gutterBottom>
                  Recent Uploads
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {uploadHistory.slice(0, 5).map((item) => (
                    <Card key={item.fileId} variant="outlined">
                      <CardContent sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="subtitle1">{item.filename}</Typography>
                          <Typography variant="caption" color="textSecondary">
                            ID: {item.fileId ? item.fileId.substring(0, 8) : 'N/A'}... • Uploaded: {item.timestamp ? new Date(item.timestamp).toLocaleString() : 'Unknown'}
                          </Typography>
                        </Box>
                        <Button 
                          size="small" 
                          variant="outlined" 
                          onClick={() => navigate(`/visualization?fileId=${item.fileId}`)}
                        >
                          View
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              </Box>
            )}
          </Box>
        );
      case 1:
        return (
          <Box sx={{ mt: 2 }}>
            {file && <FilePreview file={file} />}
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 2 }}>
              <Button onClick={handleReset} disabled={uploading}>
                Cancel
              </Button>
              <Button 
                variant="contained" 
                color="primary" 
                onClick={handleUpload} 
                disabled={uploading || !file}
                startIcon={uploading ? <CircularProgress size={20} /> : undefined}
              >
                {uploading ? 'Uploading...' : 'Upload File'}
              </Button>
            </Box>
            {uploading && (
              <Box sx={{ width: '100%', mt: 2 }}>
                <LinearProgress variant="determinate" value={uploadProgress} />
                <Typography variant="caption" align="center" sx={{ display: 'block', mt: 1 }}>
                  Uploading: {uploadProgress}%
                </Typography>
              </Box>
            )}
          </Box>
        );
      case 2:
        return (
          <Box sx={{ mt: 2 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              <AlertTitle>Processing</AlertTitle>
              Your file is being processed. This may take a few moments.
            </Alert>
            <LinearProgress />
            <Typography variant="caption" sx={{ display: 'block', mt: 1 }}>
              Status: {processingStatus?.status || 'pending'}
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
              <Button onClick={handleReset} disabled={isPolling}>
                Cancel
              </Button>
            </Box>
          </Box>
        );
      case 3:
        return (
          <Box sx={{ mt: 2 }}>
            <Alert severity="success" sx={{ mb: 2 }}>
              <AlertTitle>Success</AlertTitle>
              Processing complete! Your file has been successfully processed.
            </Alert>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
              <Button onClick={handleReset}>
                Upload Another
              </Button>
              <Button 
                variant="contained" 
                color="primary" 
                onClick={handleViewResults}
                startIcon={<CheckCircleIcon />}
              >
                View Results
              </Button>
            </Box>
          </Box>
        );
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ py: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Upload PDF
        </Typography>
        <Typography variant="subtitle1" color="textSecondary" paragraph>
          Upload your PDF lab report to extract biomarkers and visualize your health data.
        </Typography>
        
        <Box sx={{ mt: 4 }}>
          <Stepper activeStep={activeStep} orientation="vertical">
            {steps.map((step, index) => (
              <Step key={step.label}>
                <StepLabel
                  optional={
                    index === 3 ? (
                      <Typography variant="caption">Last step</Typography>
                    ) : null
                  }
                >
                  {step.label}
                </StepLabel>
                <StepContent>
                  <Typography>{step.description}</Typography>
                  {renderStepContent(index)}
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </Box>
      </Box>
      
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        ClickAwayListenerProps={{
          mouseEvent: 'onMouseUp'
        }}
      >
        <Alert onClose={handleSnackbarClose} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default UploadPage; 