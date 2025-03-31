import React, { useEffect } from 'react';
import { Box, Typography, Paper, Button } from '@mui/material';
import { styled } from '@mui/material/styles';
import FactsCarousel from './FactsCarousel';
import { ProcessingStatus } from '../types/pdf';

interface LoadingOverlayProps {
  isActive: boolean;
  status: ProcessingStatus | null;
  onClose?: () => void;
}

const OverlayContainer = styled(Box)(({ theme }) => ({
  position: 'fixed',
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  backgroundColor: 'rgba(0, 0, 0, 0.7)',
  display: 'flex',
  flexDirection: 'column',
  justifyContent: 'center',
  alignItems: 'center',
  zIndex: 9999,
  padding: theme.spacing(2),
  opacity: 0,
  visibility: 'hidden',
  transition: 'opacity 0.3s ease-in-out, visibility 0.3s ease-in-out',
  '&.active': {
    opacity: 1,
    visibility: 'visible',
  },
}));

const ContentContainer = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(4),
  maxWidth: '600px',
  width: '100%',
  display: 'flex',
  flexDirection: 'column',
  alignItems: 'center',
  borderRadius: theme.shape.borderRadius,
  backgroundColor: theme.palette.background.paper,
}));

const StatusText = styled(Typography)(({ theme }) => ({
  marginTop: theme.spacing(3),
  textAlign: 'center',
  color: theme.palette.text.secondary,
}));

const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ isActive, status, onClose }) => {
  // Add keyboard support to allow user to dismiss with Escape key
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && isActive && onClose) {
        onClose();
      }
    };

    if (isActive) {
      window.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isActive, onClose]);

  // When active, prevent background scrolling
  useEffect(() => {
    if (isActive) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isActive]);

  return (
    <OverlayContainer 
      className={isActive ? 'active' : ''} 
      role="dialog"
      aria-modal="true"
      aria-labelledby="processing-title"
      aria-describedby="processing-description"
    >
      <ContentContainer>
        <Typography id="processing-title" variant="h5" component="h2" gutterBottom>
          Processing Your Document
        </Typography>
        
        <Typography 
          id="processing-description" 
          variant="body2" 
          color="textSecondary" 
          sx={{ mb: 3, textAlign: 'center' }}
        >
          Please wait while we extract and analyze the information from your PDF.
          This usually takes about 10-15 seconds.
        </Typography>
        
        <FactsCarousel isActive={isActive} />
        
        <StatusText variant="body2">
          Status: {status?.status || 'Starting processing...'}
          {status?.progress && ` (${status.progress}%)`}
        </StatusText>

        {onClose && (
          <Button 
            variant="text" 
            color="primary" 
            onClick={onClose} 
            sx={{ mt: 3 }}
            aria-label="Cancel processing and return to upload page"
          >
            Cancel Processing
          </Button>
        )}
      </ContentContainer>
    </OverlayContainer>
  );
};

export default LoadingOverlay; 