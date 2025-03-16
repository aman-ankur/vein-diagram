import React from 'react';
import { 
  Alert, 
  AlertTitle,
  Box,
  Button,
  Typography,
  CircularProgress,
  Collapse
} from '@mui/material';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
import ReplayIcon from '@mui/icons-material/Replay';
import WifiOffIcon from '@mui/icons-material/WifiOff';

interface ErrorHandlerProps {
  error: Error | string | null;
  isLoading?: boolean;
  retry?: () => void;
  showDetails?: boolean;
}

/**
 * ErrorHandler component for displaying API errors with retry functionality
 * @param error - Error object or error message
 * @param isLoading - Whether the request is loading
 * @param retry - Function to retry the request
 * @param showDetails - Whether to show detailed error information
 */
const ErrorHandler: React.FC<ErrorHandlerProps> = ({
  error,
  isLoading = false,
  retry,
  showDetails = false
}) => {
  const [expanded, setExpanded] = React.useState(false);
  
  if (!error) return null;
  
  const errorMessage = typeof error === 'string' ? error : error.message;
  const errorDetails = typeof error === 'string' ? null : error.stack;
  
  const isNetworkError = 
    errorMessage.includes('network') || 
    errorMessage.includes('Network') ||
    errorMessage.includes('fetch') ||
    errorMessage.includes('ECONNREFUSED') ||
    errorMessage.includes('Failed to fetch');
  
  return (
    <Alert
      severity="error"
      icon={isNetworkError ? <WifiOffIcon /> : <ErrorOutlineIcon />}
      action={
        retry ? (
          <Button 
            color="inherit" 
            size="small"
            onClick={retry}
            startIcon={isLoading ? <CircularProgress size={16} color="inherit" /> : <ReplayIcon />}
            disabled={isLoading}
          >
            {isLoading ? 'Retrying...' : 'Retry'}
          </Button>
        ) : undefined
      }
      sx={{ mb: 2 }}
    >
      <AlertTitle>
        {isNetworkError 
          ? 'Network Error' 
          : errorMessage.includes('timeout') 
            ? 'Request Timeout' 
            : 'Error'}
      </AlertTitle>
      
      <Typography variant="body2">
        {isNetworkError 
          ? 'Unable to connect to the server. Please check your internet connection and try again.'
          : errorMessage}
      </Typography>
      
      {showDetails && errorDetails && (
        <Box sx={{ mt: 1 }}>
          <Button 
            size="small" 
            variant="text" 
            color="inherit"
            onClick={() => setExpanded(!expanded)}
          >
            {expanded ? 'Hide' : 'Show'} Details
          </Button>
          
          <Collapse in={expanded}>
            <Box 
              component="pre" 
              sx={{ 
                mt: 1, 
                p: 1, 
                bgcolor: 'rgba(0,0,0,0.1)', 
                borderRadius: 1, 
                fontSize: '0.75rem',
                overflow: 'auto',
                maxHeight: '200px'
              }}
            >
              {errorDetails}
            </Box>
          </Collapse>
        </Box>
      )}
    </Alert>
  );
};

export default ErrorHandler; 