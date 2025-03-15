import React, { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { 
  Typography, 
  Box, 
  Container, 
  Paper, 
  Button, 
  Stack,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  CircularProgress,
  Alert,
  Stepper,
  Step,
  StepLabel,
  Fade,
  useTheme,
  alpha,
  Tooltip,
  IconButton,
  Grid,
  Collapse,
  LinearProgress,
  Snackbar
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DescriptionIcon from '@mui/icons-material/Description';
import DeleteIcon from '@mui/icons-material/Delete';
import InfoIcon from '@mui/icons-material/Info';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import HistoryIcon from '@mui/icons-material/History';
import { useNavigate } from 'react-router-dom';
import storageService, { STORAGE_KEYS } from '../services/localStorage';

// Define interfaces for better type safety
interface FileInfo {
  id: string;
  name: string;
  size: number;
  type: string;
  uploadDate: string;
  status: 'pending' | 'processing' | 'success' | 'error';
  errorMessage?: string;
  parsedData?: any;
}

// Mock function to get file type and validation
const getFileTypeInfo = (file: File) => {
  const extension = file.name.split('.').pop()?.toLowerCase() || '';
  
  const fileTypes = {
    pdf: { 
      valid: true, 
      icon: <DescriptionIcon color="primary" />,
      description: 'PDF document'
    },
    csv: { 
      valid: true, 
      icon: <DescriptionIcon color="primary" />,
      description: 'CSV spreadsheet'
    },
    xlsx: { 
      valid: true, 
      icon: <DescriptionIcon color="primary" />,
      description: 'Excel spreadsheet'
    },
    xls: { 
      valid: true, 
      icon: <DescriptionIcon color="primary" />,
      description: 'Excel spreadsheet'
    },
    txt: { 
      valid: true, 
      icon: <DescriptionIcon color="primary" />,
      description: 'Text file'
    },
    default: { 
      valid: false, 
      icon: <ErrorIcon color="error" />,
      description: 'Unsupported format'
    }
  };
  
  return fileTypes[extension as keyof typeof fileTypes] || fileTypes.default;
};

// Format file size
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Steps for the upload process
const steps = ['Select Files', 'Validate Files', 'Upload Files'];

// Format date for display
const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date);
};

const UploadPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const [files, setFiles] = useState<File[]>([]);
  const [fileInfos, setFileInfos] = useState<FileInfo[]>([]);
  const [previousUploads, setPreviousUploads] = useState<FileInfo[]>([]);
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [processingFile, setProcessingFile] = useState<string | null>(null);
  const [showPreviousUploads, setShowPreviousUploads] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');

  // Load previous uploads from localStorage
  useEffect(() => {
    const savedFiles = storageService.getItem<FileInfo[]>(STORAGE_KEYS.UPLOADED_FILES, []);
    setPreviousUploads(savedFiles);
  }, []);

  // Dropzone configuration
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setFiles(prev => [...prev, ...acceptedFiles]);
    
    // Create file info objects
    const newFileInfos = acceptedFiles.map(file => ({
      id: generateId(),
      name: file.name,
      size: file.size,
      type: file.type,
      uploadDate: new Date().toISOString(),
      status: 'pending' as const
    }));
    
    setFileInfos(prev => [...prev, ...newFileInfos]);
    
    if (activeStep === 0) {
      setActiveStep(1);
    }
  }, [activeStep]);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({ 
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/plain': ['.txt']
    },
    maxSize: 10485760, // 10MB
  });

  // Generate unique ID for files
  const generateId = (): string => {
    return Date.now().toString(36) + Math.random().toString(36).substring(2);
  };

  // Remove a file from the upload list
  const removeFile = (index: number) => {
    const newFiles = [...files];
    newFiles.splice(index, 1);
    setFiles(newFiles);
    
    const newFileInfos = [...fileInfos];
    newFileInfos.splice(index, 1);
    setFileInfos(newFileInfos);
    
    if (newFiles.length === 0) {
      setActiveStep(0);
    }
  };
  
  // Remove a previous upload from history
  const removePreviousUpload = (id: string) => {
    const updatedUploads = previousUploads.filter(file => file.id !== id);
    setPreviousUploads(updatedUploads);
    storageService.setItem(STORAGE_KEYS.UPLOADED_FILES, updatedUploads);
    
    setSnackbarMessage('File removed from history');
    setSnackbarOpen(true);
  };

  // Handle file upload
  const handleUpload = async () => {
    setLoading(true);
    setError(null);
    setActiveStep(2);
    setUploadProgress(0);
    
    try {
      // Simulate file processing with progress
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        setProcessingFile(file.name);
        
        // Update file status to processing
        const updatedFileInfos = [...fileInfos];
        updatedFileInfos[i].status = 'processing';
        setFileInfos(updatedFileInfos);
        
        // Simulate processing time based on file size
        const processingTime = Math.min(2000, file.size / 1024);
        
        // Simulate progress updates
        for (let progress = 0; progress <= 100; progress += 5) {
          setUploadProgress(progress);
          await new Promise(resolve => setTimeout(resolve, processingTime / 20));
        }
        
        // Mark file as processed successfully
        updatedFileInfos[i].status = 'success';
        
        // Simulate parsed data (in a real app, this would come from the backend)
        updatedFileInfos[i].parsedData = {
          biomarkers: [
            { name: 'Cholesterol', value: Math.floor(Math.random() * 200 + 150), unit: 'mg/dL' },
            { name: 'HDL', value: Math.floor(Math.random() * 50 + 40), unit: 'mg/dL' },
            { name: 'LDL', value: Math.floor(Math.random() * 100 + 70), unit: 'mg/dL' },
            { name: 'Triglycerides', value: Math.floor(Math.random() * 150 + 50), unit: 'mg/dL' },
          ]
        };
        
        setFileInfos(updatedFileInfos);
        setUploadProgress(0);
      }
      
      // Save files to localStorage
      const updatedPreviousUploads = [...previousUploads, ...fileInfos];
      setPreviousUploads(updatedPreviousUploads);
      storageService.setItem(STORAGE_KEYS.UPLOADED_FILES, updatedPreviousUploads);
      
      setProcessingFile(null);
      setSuccess(true);
      setSnackbarMessage('Files uploaded successfully!');
      setSnackbarOpen(true);
      
      // After a successful upload, automatically redirect to visualization after a delay
      setTimeout(() => {
        navigate('/visualize');
      }, 2000);
      
    } catch (err) {
      console.error('Upload error:', err);
      setError('An error occurred during upload. Please try again.');
      setSnackbarMessage('Error uploading files');
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };

  // Reset the upload form
  const resetUpload = () => {
    setFiles([]);
    setFileInfos([]);
    setActiveStep(0);
    setSuccess(false);
    setError(null);
    setProcessingFile(null);
    setUploadProgress(0);
  };

  // Handle snackbar close
  const handleSnackbarClose = (event?: React.SyntheticEvent, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbarOpen(false);
  };

  const getStepContent = (stepIndex: number) => {
    switch (stepIndex) {
      case 0:
        return (
          <Box className="fade-in">
            <Paper
              {...getRootProps()}
              sx={{
                p: 5,
                textAlign: 'center',
                borderRadius: 2,
                borderStyle: 'dashed',
                borderWidth: 2,
                borderColor: isDragActive ? 'primary.main' : 'grey.300',
                bgcolor: isDragActive ? alpha(theme.palette.primary.main, 0.05) : 'background.paper',
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                '&:hover': {
                  borderColor: 'primary.main',
                  bgcolor: alpha(theme.palette.primary.main, 0.05),
                },
              }}
            >
              <input {...getInputProps()} />
              <CloudUploadIcon sx={{ fontSize: 60, color: isDragActive ? 'primary.main' : 'grey.500', mb: 2 }} />
              <Typography variant="h5" gutterBottom>
                {isDragActive ? 'Drop your files here' : 'Drag & drop files here'}
              </Typography>
              <Typography variant="body1" color="textSecondary" sx={{ mb: 3 }}>
                or click to browse your files
              </Typography>
              <Button variant="contained" component="span" startIcon={<AttachFileIcon />}>
                Browse Files
              </Button>
              <Typography variant="caption" color="textSecondary" sx={{ display: 'block', mt: 2 }}>
                Supported formats: PDF, CSV, Excel, Text | Max size: 10MB
              </Typography>
            </Paper>
            
            {previousUploads.length > 0 && (
              <Box sx={{ mt: 4 }}>
                <Button 
                  variant="outlined" 
                  startIcon={<HistoryIcon />}
                  onClick={() => setShowPreviousUploads(!showPreviousUploads)}
                  sx={{ mb: 2 }}
                >
                  {showPreviousUploads ? 'Hide' : 'Show'} Previous Uploads ({previousUploads.length})
                </Button>
                
                <Collapse in={showPreviousUploads}>
                  <Paper sx={{ p: 3, mt: 2, borderRadius: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      Previously Uploaded Files
                    </Typography>
                    <List>
                      {previousUploads.map((file, index) => (
                        <React.Fragment key={file.id}>
                          {index > 0 && <Divider component="li" />}
                          <ListItem
                            secondaryAction={
                              <IconButton 
                                edge="end" 
                                aria-label="delete" 
                                onClick={() => removePreviousUpload(file.id)}
                              >
                                <DeleteIcon />
                              </IconButton>
                            }
                          >
                            <ListItemIcon>
                              <DescriptionIcon color="primary" />
                            </ListItemIcon>
                            <ListItemText
                              primary={file.name}
                              secondary={
                                <>
                                  {formatFileSize(file.size)} • Uploaded {formatDate(new Date(file.uploadDate))}
                                </>
                              }
                            />
                          </ListItem>
                        </React.Fragment>
                      ))}
                    </List>
                  </Paper>
                </Collapse>
              </Box>
            )}
          </Box>
        );
        
      case 1:
        return (
          <Box className="fade-in">
            <Paper sx={{ p: 3, borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom>
                File Validation
              </Typography>
              
              <List>
                {files.map((file, index) => {
                  const fileTypeInfo = getFileTypeInfo(file);
                  
                  return (
                    <React.Fragment key={index}>
                      {index > 0 && <Divider component="li" />}
                      <ListItem
                        secondaryAction={
                          <IconButton edge="end" aria-label="delete" onClick={() => removeFile(index)}>
                            <DeleteIcon />
                          </IconButton>
                        }
                      >
                        <ListItemIcon>
                          {fileTypeInfo.icon}
                        </ListItemIcon>
                        <ListItemText
                          primary={file.name}
                          secondary={
                            <>
                              {formatFileSize(file.size)} • {fileTypeInfo.description}
                              {!fileTypeInfo.valid && (
                                <Typography component="span" color="error" sx={{ display: 'block' }}>
                                  <ErrorIcon fontSize="small" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                                  Unsupported file format
                                </Typography>
                              )}
                            </>
                          }
                        />
                      </ListItem>
                    </React.Fragment>
                  );
                })}
              </List>
              
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Button 
                  onClick={() => {
                    setFiles([]);
                    setFileInfos([]);
                    setActiveStep(0);
                  }}
                  variant="outlined"
                >
                  Clear All
                </Button>
                <Box>
                  <Button
                    onClick={() => setActiveStep(0)}
                    sx={{ mr: 1 }}
                  >
                    Back
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleUpload}
                    disabled={files.length === 0 || files.some(file => !getFileTypeInfo(file).valid)}
                  >
                    Upload Files
                  </Button>
                </Box>
              </Box>
            </Paper>
            
            <Box sx={{ mt: 3 }}>
              <Alert severity="info" icon={<HelpOutlineIcon />}>
                <Typography variant="body2">
                  We'll extract biomarkers from your files and prepare them for visualization.
                  Supported test types include blood panels, metabolic panels, and hormone tests.
                </Typography>
              </Alert>
            </Box>
          </Box>
        );
        
      case 2:
        return (
          <Box className="fade-in">
            <Paper sx={{ p: 3, borderRadius: 2 }}>
              <Typography variant="h6" gutterBottom>
                {success ? 'Upload Complete' : 'Processing Files'}
              </Typography>
              
              {loading && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Processing: {processingFile}
                  </Typography>
                  <LinearProgress variant="determinate" value={uploadProgress} sx={{ mb: 1 }} />
                  <Typography variant="caption" color="textSecondary">
                    {uploadProgress}% complete
                  </Typography>
                </Box>
              )}
              
              {error && (
                <Alert severity="error" sx={{ mb: 3 }}>
                  {error}
                </Alert>
              )}
              
              {success && (
                <Alert severity="success" icon={<CheckCircleIcon />} sx={{ mb: 3 }}>
                  All files have been successfully processed. You will be redirected to the visualization page.
                </Alert>
              )}
              
              <List>
                {fileInfos.map((fileInfo, index) => (
                  <React.Fragment key={fileInfo.id}>
                    {index > 0 && <Divider component="li" />}
                    <ListItem>
                      <ListItemIcon>
                        {fileInfo.status === 'success' && <CheckCircleIcon color="success" />}
                        {fileInfo.status === 'processing' && <CircularProgress size={24} />}
                        {fileInfo.status === 'error' && <ErrorIcon color="error" />}
                        {fileInfo.status === 'pending' && <DescriptionIcon color="action" />}
                      </ListItemIcon>
                      <ListItemText
                        primary={fileInfo.name}
                        secondary={
                          <>
                            {formatFileSize(fileInfo.size)} • 
                            {fileInfo.status === 'success' && ' Successfully processed'}
                            {fileInfo.status === 'processing' && ' Processing...'}
                            {fileInfo.status === 'error' && ` Error: ${fileInfo.errorMessage || 'Unknown error'}`}
                            {fileInfo.status === 'pending' && ' Pending'}
                          </>
                        }
                      />
                    </ListItem>
                  </React.Fragment>
                ))}
              </List>
              
              <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                <Button 
                  onClick={resetUpload}
                  variant="outlined"
                  disabled={loading}
                >
                  Upload More Files
                </Button>
                
                <Button
                  variant="contained"
                  onClick={() => navigate('/visualize')}
                  disabled={loading || !success}
                >
                  View Visualizations
                </Button>
              </Box>
            </Paper>
          </Box>
        );
        
      default:
        return 'Unknown step';
    }
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Upload Health Data
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Upload your lab results to visualize and track your biomarkers over time.
        </Typography>
      </Box>
      
      <Stepper activeStep={activeStep} sx={{ mb: 4, py: 2 }}>
        {steps.map((label) => (
          <Step key={label}>
            <StepLabel>{label}</StepLabel>
          </Step>
        ))}
      </Stepper>
      
      {getStepContent(activeStep)}
      
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={handleSnackbarClose}
        message={snackbarMessage}
      />
    </Container>
  );
};

export default UploadPage; 