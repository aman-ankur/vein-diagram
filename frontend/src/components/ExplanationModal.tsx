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
  biomarker_id: number;
  name: string;
  general_explanation: string;
  specific_explanation: string;
  created_at: string;
  from_cache: boolean;
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
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      
      <DialogContent sx={{ p: 0 }}>
        <Box sx={{ p: 3 }}>
          <Box sx={{ mb: 2, display: 'flex', flexWrap: 'wrap', gap: 2 }}>
            <Paper elevation={1} sx={{ p: 1.5, borderRadius: 2, flex: '1 1 auto', minWidth: '150px' }}>
              <Typography variant="overline" color="text.secondary">
                Your Value
              </Typography>
              <Typography variant="h5" color="primary.main" sx={{ fontWeight: 'bold' }}>
                {biomarkerValue} {biomarkerUnit}
              </Typography>
            </Paper>
            
            <Paper elevation={1} sx={{ p: 1.5, borderRadius: 2, flex: '1 1 auto', minWidth: '150px' }}>
              <Typography variant="overline" color="text.secondary">
                Reference Range
              </Typography>
              <Typography variant="h6">
                {referenceRange || 'Not available'}
              </Typography>
            </Paper>
          </Box>
          
          {isLoading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', my: 8 }}>
              <CircularProgress size={60} thickness={4} />
              <Typography variant="h6" sx={{ ml: 2 }}>
                Generating explanation...
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
            </Box>
          ) : explanation ? (
            <>
              <Box sx={{ mb: 4 }}>
                <Typography variant="h6" gutterBottom color="primary" sx={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  pb: 1,
                  borderBottom: `1px solid ${theme.palette.divider}`
                }}>
                  About this Biomarker
                </Typography>
                <Typography variant="body1" sx={{ mt: 2, lineHeight: 1.7 }}>
                  {explanation.general_explanation}
                </Typography>
              </Box>
              
              <Divider sx={{ my: 3 }} />
              
              <Box>
                <Typography variant="h6" gutterBottom color="primary" sx={{ 
                  display: 'flex', 
                  alignItems: 'center',
                  pb: 1,
                  borderBottom: `1px solid ${theme.palette.divider}`
                }}>
                  Your Results Explained
                </Typography>
                <Typography variant="body1" sx={{ mt: 2, lineHeight: 1.7 }}>
                  {explanation.specific_explanation}
                </Typography>
              </Box>
              
              <Paper 
                elevation={0} 
                sx={{ 
                  mt: 4, 
                  p: 2, 
                  backgroundColor: theme.palette.grey[100],
                  borderRadius: 2,
                  border: `1px solid ${theme.palette.grey[300]}`
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
            </Box>
          )}
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ p: 2, backgroundColor: theme.palette.grey[50] }}>
        <Button onClick={onClose} variant="outlined">
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExplanationModal; 