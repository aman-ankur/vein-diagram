import React from 'react';
import { 
  Box, 
  CircularProgress, 
  Typography, 
  LinearProgress,
  Paper,
  alpha
} from '@mui/material';
import { useTheme } from '@mui/material/styles';

interface LoadingIndicatorProps {
  message?: string;
  variant?: 'circular' | 'linear';
  size?: 'small' | 'medium' | 'large';
  fullPage?: boolean;
  value?: number; // For determinate progress
  showValue?: boolean;
  withBackdrop?: boolean;
}

/**
 * LoadingIndicator component for displaying loading states throughout the application
 */
const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  message = 'Loading...',
  variant = 'circular',
  size = 'medium',
  fullPage = false,
  value,
  showValue = false,
  withBackdrop = false
}) => {
  const theme = useTheme();

  // Size mappings for circular progress
  const sizeMap = {
    small: 24,
    medium: 40,
    large: 60
  };

  // Determine if progress is determinate
  const isDeterminate = value !== undefined && value >= 0 && value <= 100;
  
  // Render either circular or linear progress
  const renderProgress = () => {
    if (variant === 'circular') {
      return (
        <CircularProgress 
          size={sizeMap[size]} 
          variant={isDeterminate ? 'determinate' : 'indeterminate'} 
          value={value}
          color="primary"
        />
      );
    } else {
      return (
        <Box sx={{ width: '100%', maxWidth: 400 }}>
          <LinearProgress 
            variant={isDeterminate ? 'determinate' : 'indeterminate'} 
            value={value}
            color="primary"
            sx={{ height: size === 'small' ? 4 : size === 'medium' ? 6 : 8 }}
          />
          {isDeterminate && showValue && (
            <Typography variant="caption" color="text.secondary" align="center" sx={{ display: 'block', mt: 1 }}>
              {Math.round(value)}%
            </Typography>
          )}
        </Box>
      );
    }
  };

  // Full page loading indicator
  if (fullPage) {
    return (
      <Box
        sx={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          bgcolor: withBackdrop ? alpha(theme.palette.background.paper, 0.8) : 'transparent',
          zIndex: theme.zIndex.modal,
          backdropFilter: withBackdrop ? 'blur(5px)' : 'none',
        }}
      >
        <Paper 
          elevation={withBackdrop ? 5 : 0}
          sx={{ 
            p: withBackdrop ? 4 : 0,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            bgcolor: withBackdrop ? theme.palette.background.paper : 'transparent',
            maxWidth: '80vw'
          }}
        >
          {renderProgress()}
          
          {message && (
            <Typography 
              variant={size === 'small' ? 'body2' : 'body1'} 
              color="text.secondary"
              align="center"
              sx={{ mt: 2 }}
            >
              {message}
            </Typography>
          )}
        </Paper>
      </Box>
    );
  }

  // Standard loading indicator
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        p: 3,
      }}
    >
      {renderProgress()}
      
      {message && (
        <Typography 
          variant={size === 'small' ? 'body2' : 'body1'} 
          color="text.secondary"
          align="center"
          sx={{ mt: 2 }}
        >
          {message}
        </Typography>
      )}
    </Box>
  );
};

export default LoadingIndicator; 