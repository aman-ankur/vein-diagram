import React, { useState, useEffect } from 'react';
import { Box, Typography, Button, CircularProgress, Chip, Tooltip } from '@mui/material';
import { checkApiAvailability } from '../services/api';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import NetworkCheckIcon from '@mui/icons-material/NetworkCheck';

interface APIStatusIndicatorProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  showOnlyOnError?: boolean;
}

const APIStatusIndicator: React.FC<APIStatusIndicatorProps> = ({
  position = 'top-right',
  showOnlyOnError = false,
}) => {
  const [status, setStatus] = useState<'checking' | 'connected' | 'disconnected'>('checking');
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [showIndicator, setShowIndicator] = useState(true);
  
  // Get position styles based on the position prop
  const getPositionStyles = () => {
    switch (position) {
      case 'top-right':
        return { top: 16, right: 16 };
      case 'top-left':
        return { top: 16, left: 16 };
      case 'bottom-right':
        return { bottom: 16, right: 16 };
      case 'bottom-left':
        return { bottom: 16, left: 16 };
      default:
        return { top: 16, right: 16 };
    }
  };

  const checkStatus = async () => {
    try {
      setStatus('checking');
      const isAvailable = await checkApiAvailability();
      setStatus(isAvailable ? 'connected' : 'disconnected');
      
      // If not available and we have auto-retry enabled (during initial retries)
      if (!isAvailable && isRetrying && retryCount < 3) {
        setRetryCount(prevCount => prevCount + 1);
        // Exponential backoff for retries
        const retryDelay = Math.min(3000 * Math.pow(1.5, retryCount), 10000);
        setTimeout(checkStatus, retryDelay); // Try again with increasing delay
      } else if (!isAvailable) {
        setIsRetrying(false);
        // Display more helpful error message to console
        console.warn(
          'Backend API is not available. Please ensure the backend server is running at ' +
          `${import.meta.env.VITE_API_URL || 'http://localhost:8000'} and that CORS is properly configured.`
        );
      } else {
        // Reset if we're connected
        setIsRetrying(false);
        setRetryCount(0);
      }
      
      // Update visibility based on showOnlyOnError
      setShowIndicator(!showOnlyOnError || (showOnlyOnError && !isAvailable));
    } catch (error) {
      console.error('Error checking API status:', error);
      setStatus('disconnected');
      setShowIndicator(true);
    }
  };

  const handleRetry = () => {
    setIsRetrying(true);
    setRetryCount(0);
    checkStatus();
  };

  // Check status on mount and setup interval
  useEffect(() => {
    checkStatus();
    
    // Set up periodic checks
    const intervalId = setInterval(() => {
      // Don't overwrite manual retry
      if (!isRetrying) {
        checkStatus();
      }
    }, 30000); // Check every 30 seconds
    
    return () => clearInterval(intervalId);
  }, []);

  // Show nothing if indicator is hidden
  if (!showIndicator) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        zIndex: 1500,
        ...getPositionStyles(),
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 1,
        background: 'rgba(255, 255, 255, 0.9)',
        padding: 1,
        borderRadius: 2,
        boxShadow: status === 'disconnected' ? '0 0 10px rgba(244, 67, 54, 0.5)' : 'none',
        transition: 'all 0.3s ease',
      }}
    >
      {status === 'checking' && (
        <Tooltip title="Checking API connection">
          <Chip
            icon={<CircularProgress size={16} />}
            label="Checking connection..."
            color="primary"
            variant="outlined"
          />
        </Tooltip>
      )}
      
      {status === 'connected' && (
        <Tooltip title="API is available">
          <Chip
            icon={<CheckCircleIcon fontSize="small" />}
            label="API Connected"
            color="success"
            onDelete={() => setShowIndicator(false)}
            deleteIcon={<Box sx={{ width: 18, height: 18 }} />}
          />
        </Tooltip>
      )}
      
      {status === 'disconnected' && (
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 1 }}>
          <Tooltip title="API is unavailable">
            <Chip
              icon={<ErrorIcon fontSize="small" />}
              label="API Disconnected"
              color="error"
            />
          </Tooltip>
          
          <Button
            variant="contained"
            color="primary"
            size="small"
            startIcon={<NetworkCheckIcon />}
            onClick={handleRetry}
            disabled={isRetrying}
            sx={{ minWidth: 100 }}
          >
            {isRetrying ? (
              <>
                <CircularProgress size={16} color="inherit" sx={{ mr: 1 }} />
                Retrying...
              </>
            ) : (
              'Retry'
            )}
          </Button>
          
          {retryCount > 0 && (
            <Typography variant="caption" color="text.secondary">
              Retry attempts: {retryCount}/3
            </Typography>
          )}
        </Box>
      )}
    </Box>
  );
};

export default APIStatusIndicator; 