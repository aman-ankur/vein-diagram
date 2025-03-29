import React from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  Typography, 
  Box, 
  CircularProgress,
  Divider,
  IconButton,
  useTheme,
  Paper
} from '@mui/material';
import { Close as CloseIcon, Psychology as PsychologyIcon } from '@mui/icons-material';

// Define interfaces for the component props
export interface BiomarkerExplanation {
  biomarker_id?: number;
  name: string;
  general_explanation: string;
  specific_explanation: string;
  created_at?: string;
  from_cache?: boolean;
}

interface ExplanationModalProps {
  open: boolean;
  onClose: () => void;
  biomarkerName: string;
  biomarkerValue: number;
  biomarkerUnit: string;
  referenceRange: string;
  isLoading: boolean;
  error: string | null;
  explanation: BiomarkerExplanation | null;
}

/**
 * Modal component for displaying AI-generated explanations of biomarker data
 */
const ExplanationModal: React.FC<ExplanationModalProps> = ({
  open,
  onClose,
  biomarkerName,
  biomarkerValue,
  biomarkerUnit,
  referenceRange,
  isLoading,
  error,
  explanation
}) => {
  const theme = useTheme();
  
  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="md"
      fullWidth
      aria-labelledby="explanation-dialog-title"
      PaperProps={{
        elevation: 5,
        sx: {
          borderRadius: 2,
          overflow: 'hidden'
        }
      }}
    >
      <DialogTitle id="explanation-dialog-title" sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        backgroundColor: theme.palette.primary.main,
        color: theme.palette.primary.contrastText,
        py: 2
      }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <PsychologyIcon />
          <Typography variant="h6" component="div">
            {biomarkerName} Explained
          </Typography>
        </Box>
        <IconButton 
          edge="end" 
          color="inherit" 
          onClick={onClose} 
          aria-label="close"
          disabled={isLoading}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      
      <DialogContent sx={{ p: 0 }}>
        <Box sx={{ p: 3 }}>
          <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Paper elevation={1} sx={{ p: 1.5, borderRadius: 2, flex: '1 1 auto', minWidth: '150px' }}>
              <Typography variant="overline" color={theme.palette.mode === 'dark' ? 'primary.light' : 'text.secondary'}>
                Your Value
              </Typography>
              <Typography variant="h5" color={theme.palette.mode === 'dark' ? 'primary.light' : 'primary.main'} sx={{ fontWeight: 'bold' }}>
                {biomarkerValue} {biomarkerUnit}
              </Typography>
            </Paper>
            
            <Paper elevation={1} sx={{ p: 1.5, borderRadius: 2, flex: '1 1 auto', minWidth: '150px' }}>
              <Typography variant="overline" color={theme.palette.mode === 'dark' ? 'primary.light' : 'text.secondary'}>
                Reference Range
              </Typography>
              <Typography variant="h6" color={theme.palette.mode === 'dark' ? 'text.primary' : 'inherit'}>
                {referenceRange || 'Not available'}
              </Typography>
            </Paper>
          </Box>
          
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', my: 8, flexDirection: 'column' }}>
              <CircularProgress size={60} thickness={4} color="primary" />
              <Typography variant="h6" sx={{ mt: 2 }}>
                Generating explanation...
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                This may take a few moments while we analyze the biomarker data.
              </Typography>
            </Box>
          ) : error ? (
            <Box sx={{ 
              backgroundColor: theme.palette.error.light, 
              color: theme.palette.error.contrastText,
              p: 3, 
              borderRadius: 2,
              my: 2 
            }}>
              <Typography variant="h6" gutterBottom>
                Error Loading Explanation
              </Typography>
              <Typography variant="body1">
                {error}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                Please try again later or contact support if the problem persists.
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                sx={{ mt: 2 }}
                onClick={() => {
                  // Notify parent to retry
                  if (onClose) {
                    onClose();
                    // Small delay before potentially reopening the modal
                    setTimeout(() => {
                      if (explanation) {
                        // This is a hacky way to trigger a retry, in a real implementation
                        // the parent component would have a proper retry mechanism
                        const retryEvent = new CustomEvent('retry-explanation', { 
                          detail: { biomarkerName } 
                        });
                        window.dispatchEvent(retryEvent);
                      }
                    }, 300);
                  }
                }}
              >
                Try Again
              </Button>
            </Box>
          ) : explanation ? (
            <>
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" gutterBottom sx={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  pb: 1,
                  borderBottom: `1px solid ${theme.palette.divider}`,
                  color: theme.palette.mode === 'dark' ? theme.palette.primary.light : theme.palette.primary.main
                }}>
                  About this Biomarker
                </Typography>
                <Typography variant="body1" sx={{ mt: 2, lineHeight: 1.7, color: theme.palette.mode === 'dark' ? 'text.primary' : 'inherit' }}>
                  {explanation.general_explanation}
                </Typography>
              </Box>
              
              <Divider sx={{ my: 3 }} />
              
              <Box>
                <Typography variant="h6" gutterBottom sx={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  pb: 1,
                  borderBottom: `1px solid ${theme.palette.divider}`,
                  color: theme.palette.mode === 'dark' ? theme.palette.primary.light : theme.palette.primary.main
                }}>
                  Your Results Explained
                </Typography>
                <Typography variant="body1" sx={{ mt: 2, lineHeight: 1.7, whiteSpace: 'pre-line', color: theme.palette.mode === 'dark' ? 'text.primary' : 'inherit' }}>
                  {explanation.specific_explanation}
                </Typography>
              </Box>
              
              <Paper 
                elevation={0} 
                sx={{ 
                  mt: 4, 
                  p: 2, 
                  backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : theme.palette.grey[100],
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : theme.palette.grey[300]}`
                }}
              >
                <Typography variant="caption" color="text.secondary">
                  <strong>Important:</strong> This information is for educational purposes only and 
                  should not be considered medical advice. Always consult with a healthcare 
                  professional for interpretation of your lab results and medical decisions.
                </Typography>
              </Paper>
            </>
          ) : (
            <Box sx={{ textAlign: 'center', my: 4 }}>
              <Typography variant="body1" color="text.secondary">
                No explanation available. Please try again.
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                sx={{ mt: 2 }}
                onClick={() => {
                  if (onClose) onClose();
                }}
              >
                Close
              </Button>
            </Box>
          )}
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ p: 2, backgroundColor: theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.05)' : theme.palette.grey[50] }}>
        <Button onClick={onClose} variant="outlined" disabled={isLoading}>
          Close
        </Button>
        {explanation && (
          <Button 
            onClick={() => {
              // Copy explanation to clipboard
              const text = `${biomarkerName} (${biomarkerValue} ${biomarkerUnit}):\n\n${explanation.general_explanation}\n\n${explanation.specific_explanation}`;
              navigator.clipboard.writeText(text)
                .then(() => {
                  // Could add a toast notification here
                  console.log('Explanation copied to clipboard');
                })
                .catch(err => {
                  console.error('Failed to copy explanation:', err);
                });
            }}
            variant="contained"
          >
            Copy to Clipboard
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
};

export default ExplanationModal; 