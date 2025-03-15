import React, { useState, useEffect } from 'react';
import { Box, Button, Container, Typography, Paper, Alert, AlertTitle, Grid } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { styled } from '@mui/material/styles';
import { uploadPDF, getPDFStatus, getBiomarkersByFileId } from '../services/api';
import ProcessingStatus from '../components/ProcessingStatus';
import UploadGuide from '../components/UploadGuide';
import BiomarkerTable from '../components/BiomarkerTable';
import { ProcessingStatus as ProcessingStatusType } from '../types/pdf';
import { Biomarker } from '../components/BiomarkerTable';
import { MAX_FILE_SIZE, SUPPORTED_FILE_TYPES, STATUS_POLLING_INTERVAL } from '../config';

// Styled component for the upload area
const UploadArea = styled('div')(({ theme }) => ({
  border: `2px dashed ${theme.palette.primary.main}`,
  borderRadius: theme.shape.borderRadius,
  padding: theme.spacing(6),
  textAlign: 'center',
  backgroundColor: theme.palette.background.default,
  cursor: 'pointer',
  transition: 'border-color 0.3s ease-in-out',
  '&:hover': {
    borderColor: theme.palette.primary.dark,
  },
}));

/**
 * Page for uploading and processing PDF lab reports
 */
const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [fileId, setFileId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<ProcessingStatusType | null>(null);
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  const [loadingBiomarkers, setLoadingBiomarkers] = useState(false);
  const [biomarkersError, setBiomarkersError] = useState<string | null>(null);

  // Handle file selection
  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0] || null;
    
    if (selectedFile) {
      // Validate file type
      if (!SUPPORTED_FILE_TYPES.includes(selectedFile.type)) {
        setError('Please upload a PDF file.');
        setFile(null);
        return;
      }
      
      // Validate file size
      if (selectedFile.size > MAX_FILE_SIZE) {
        setError(`File size exceeds the maximum allowed size of ${MAX_FILE_SIZE / (1024 * 1024)}MB.`);
        setFile(null);
        return;
      }
      
      setFile(selectedFile);
      setError(null);
    }
  };

  // Handle file upload
  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }
    
    try {
      setUploading(true);
      setError(null);
      setBiomarkers([]);
      
      const response = await uploadPDF(file);
      
      setFileId(response.file_id);
      setStatus({
        file_id: response.file_id,
        status: 'pending',
        message: 'PDF uploaded successfully. Processing...',
      });
    } catch (err) {
      console.error('Error uploading file:', err);
      setError('Failed to upload file. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  // Poll for status updates when fileId is available
  useEffect(() => {
    let intervalId: NodeJS.Timeout;
    
    const checkStatus = async () => {
      if (!fileId) return;
      
      try {
        const statusResponse = await getPDFStatus(fileId);
        setStatus(statusResponse);
        
        // If processing is complete, fetch biomarkers
        if (statusResponse.status === 'processed') {
          try {
            setLoadingBiomarkers(true);
            setBiomarkersError(null);
            const biomarkersData = await getBiomarkersByFileId(fileId);
            setBiomarkers(biomarkersData);
          } catch (err) {
            console.error('Error fetching biomarkers:', err);
            setBiomarkersError('Failed to load biomarker data. Please try refreshing the page.');
          } finally {
            setLoadingBiomarkers(false);
          }
          // Clear interval once processing is complete
          clearInterval(intervalId);
        } else if (statusResponse.status === 'error') {
          // Clear interval on error
          clearInterval(intervalId);
        }
      } catch (err) {
        console.error('Error checking status:', err);
        clearInterval(intervalId);
      }
    };
    
    if (fileId) {
      checkStatus(); // Check immediately
      intervalId = setInterval(checkStatus, STATUS_POLLING_INTERVAL);
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [fileId]);

  // Function to handle drag and drop file selection
  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const droppedFile = event.dataTransfer.files[0];
    
    if (droppedFile) {
      // Validate file type
      if (!SUPPORTED_FILE_TYPES.includes(droppedFile.type)) {
        setError('Please upload a PDF file.');
        return;
      }
      
      // Validate file size
      if (droppedFile.size > MAX_FILE_SIZE) {
        setError(`File size exceeds the maximum allowed size of ${MAX_FILE_SIZE / (1024 * 1024)}MB.`);
        return;
      }
      
      setFile(droppedFile);
      setError(null);
    }
  };

  // Prevent default behavior for drag events
  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  // Reset form to upload a new file
  const handleReset = () => {
    setFile(null);
    setFileId(null);
    setStatus(null);
    setError(null);
    setBiomarkers([]);
    setBiomarkersError(null);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Grid container spacing={4}>
        <Grid item xs={12} md={5}>
          <UploadGuide />
        </Grid>
        
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 3, mb: 4 }}>
            <Typography variant="h5" component="h1" gutterBottom>
              Upload Lab Report
            </Typography>
            
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <AlertTitle>Error</AlertTitle>
                {error}
              </Alert>
            )}
            
            {!fileId ? (
              // Upload form
              <Box>
                <input
                  type="file"
                  accept=".pdf"
                  onChange={handleFileChange}
                  style={{ display: 'none' }}
                  id="file-upload"
                />
                
                <label htmlFor="file-upload">
                  <UploadArea
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                  >
                    <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Drag and drop your lab report PDF here
                    </Typography>
                    <Typography variant="body2" color="textSecondary" gutterBottom>
                      or
                    </Typography>
                    <Button variant="contained" component="span">
                      Select PDF File
                    </Button>
                    {file && (
                      <Typography variant="body2" sx={{ mt: 2 }}>
                        Selected: {file.name}
                      </Typography>
                    )}
                  </UploadArea>
                </label>
                
                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleUpload}
                    disabled={!file || uploading}
                    sx={{ minWidth: 200 }}
                  >
                    {uploading ? 'Uploading...' : 'Upload Report'}
                  </Button>
                </Box>
              </Box>
            ) : (
              // Status display and results
              <Box>
                <ProcessingStatus status={status} />
                
                {status?.status === 'processed' && (
                  <Box sx={{ mt: 4 }}>
                    <Typography variant="h6" gutterBottom>
                      Processing Complete
                    </Typography>
                    
                    {status.lab_name && (
                      <Typography variant="body1">
                        <strong>Lab Provider:</strong> {status.lab_name}
                      </Typography>
                    )}
                    
                    {status.report_date && (
                      <Typography variant="body1">
                        <strong>Report Date:</strong> {status.report_date}
                      </Typography>
                    )}
                    
                    {status.parsing_confidence !== undefined && (
                      <Typography variant="body1">
                        <strong>Confidence Score:</strong> {(status.parsing_confidence * 100).toFixed(1)}%
                      </Typography>
                    )}
                    
                    <Box sx={{ mt: 2, mb: 4 }}>
                      <Button
                        variant="outlined"
                        color="primary"
                        onClick={handleReset}
                      >
                        Upload Another Report
                      </Button>
                    </Box>
                  </Box>
                )}
                
                {status?.status === 'error' && (
                  <Box sx={{ mt: 3 }}>
                    <Alert severity="error">
                      <AlertTitle>Processing Error</AlertTitle>
                      {status.error_message || 'An error occurred while processing the file.'}
                    </Alert>
                    <Box sx={{ mt: 2 }}>
                      <Button
                        variant="outlined"
                        color="primary"
                        onClick={handleReset}
                      >
                        Try Again
                      </Button>
                    </Box>
                  </Box>
                )}
              </Box>
            )}
          </Paper>
          
          {/* Biomarker display */}
          {(status?.status === 'processed' || biomarkers.length > 0) && (
            <Paper sx={{ p: 3 }}>
              <BiomarkerTable 
                biomarkers={biomarkers} 
                isLoading={loadingBiomarkers}
                error={biomarkersError}
              />
            </Paper>
          )}
        </Grid>
      </Grid>
    </Container>
  );
};

export default UploadPage; 