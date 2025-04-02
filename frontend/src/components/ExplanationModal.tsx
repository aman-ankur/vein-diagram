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
  Paper,
  alpha,
  Chip,
  Avatar,
  Grid
} from '@mui/material';
import { 
  Close as CloseIcon, 
  Psychology as PsychologyIcon,
  Info as InfoIcon,
  BarChart as BarChartIcon
} from '@mui/icons-material';
import { Biomarker } from '../types/biomarker';
import { BiomarkerExplanation as BiomarkerExplanationType } from '../types/api';

// Updated ExplanationModal props
interface ExplanationModalProps {
  open: boolean;
  onClose: () => void;
  biomarker: Biomarker | null;
  explanation: BiomarkerExplanationType | null;
  loading: boolean;
  error: string | null;
}

const ExplanationModal: React.FC<ExplanationModalProps> = ({
  open,
  onClose,
  biomarker,
  explanation,
  loading,
  error
}) => {
  const theme = useTheme();
  
  if (!biomarker) return null;
  
  const referenceRange = biomarker.referenceRange || 
    (biomarker.reference_range_low !== null && biomarker.reference_range_high !== null 
      ? `${biomarker.reference_range_low}-${biomarker.reference_range_high}` 
      : "Not available");
  
  const isOutsideRange = () => {
    if (biomarker.isAbnormal !== undefined) {
      return biomarker.isAbnormal;
    }
    
    if (biomarker.reference_range_low != null && biomarker.reference_range_high != null) {
      return biomarker.value < biomarker.reference_range_low || biomarker.value > biomarker.reference_range_high;
    }
    
    if (!biomarker.referenceRange) {
      return undefined;
    }

    const referenceRange = biomarker.referenceRange.trim();
    
    // Try to parse ranges in format "X-Y"
    const dashMatch = referenceRange.match(/^(\d+\.?\d*)\s*-\s*(\d+\.?\d*)$/);
    if (dashMatch) {
      const [_, min, max] = dashMatch;
      return biomarker.value < parseFloat(min) || biomarker.value > parseFloat(max);
    }
    
    // Try to parse ranges in format "< X" or "<= X"
    const lessThanMatch = referenceRange.match(/^<\s*=?\s*(\d+\.?\d*)$/);
    if (lessThanMatch) {
      const [_, max] = lessThanMatch;
      return biomarker.value > parseFloat(max);
    }
    
    // Try to parse ranges in format "> X" or ">= X"
    const greaterThanMatch = referenceRange.match(/^>\s*=?\s*(\d+\.?\d*)$/);
    if (greaterThanMatch) {
      const [_, min] = greaterThanMatch;
      return biomarker.value < parseFloat(min);
    }
    
    return undefined;
  };
  
  const getStatusColor = () => {
    const abnormal = isOutsideRange();
    
    if (abnormal === undefined) {
      return theme.palette.grey[500];
    }
    
    return abnormal ? theme.palette.error.main : theme.palette.success.main;
  };
  
  const getStatusText = () => {
    const abnormal = isOutsideRange();
    
    if (abnormal === undefined) {
      return "Unknown";
    }
    
    return abnormal ? "Outside Normal Range" : "Within Normal Range";
  };
  
  return (
    <Dialog 
      open={open} 
      onClose={onClose}
      maxWidth="md"
      fullWidth
      aria-labelledby="explanation-dialog-title"
      PaperProps={{
        elevation: 1,
        sx: {
          borderRadius: '20px',
          overflow: 'hidden',
          backgroundColor: theme.palette.background.paper
        }
      }}
    >
      <DialogTitle 
        id="explanation-dialog-title" 
        sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          py: 2.5,
          px: 3,
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Avatar 
            sx={{ 
              bgcolor: alpha(theme.palette.primary.main, 0.1), 
              color: theme.palette.primary.main,
              mr: 1.5
            }}
          >
            <PsychologyIcon />
          </Avatar>
          <Box>
            <Typography 
              variant="h6" 
              component="div" 
              sx={{ 
                fontWeight: 600, 
                color: theme.palette.text.primary,
                lineHeight: 1.2
              }}
            >
              {biomarker.name}
            </Typography>
            <Typography 
              variant="body2" 
              color="text.secondary"
              sx={{ mt: 0.5 }}
            >
              AI-powered analysis and explanation
            </Typography>
          </Box>
        </Box>
        
        <IconButton 
          onClick={onClose} 
          aria-label="close"
          sx={{
            bgcolor: alpha(theme.palette.background.paper, 0.6),
            '&:hover': {
              bgcolor: alpha(theme.palette.background.paper, 0.8)
            }
          }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      
      <DialogContent sx={{ p: 0 }}>
        {/* Biomarker Data Summary */}
        <Box sx={{ 
          p: 3, 
          backgroundColor: alpha(theme.palette.background.default, 0.5),
          borderBottom: `1px solid ${alpha(theme.palette.divider, 0.05)}`
        }}>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 2.5,
                  height: '100%', 
                  borderRadius: 3,
                  backgroundColor: alpha(theme.palette.background.paper, 0.7),
                  backdropFilter: 'blur(10px)',
                  border: `1px solid ${alpha(theme.palette.divider, 0.05)}`,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center'
                }}
              >
                <Typography 
                  variant="overline" 
                  sx={{ 
                    color: theme.palette.text.secondary,
                    fontSize: '0.75rem',
                    letterSpacing: 1
                  }}
                >
                  Your Value
                </Typography>
                <Typography 
                  variant="h4" 
                  sx={{ 
                    fontWeight: 600,
                    color: getStatusColor(),
                    display: 'flex',
                    alignItems: 'baseline',
                    mt: 1
                  }}
                >
                  {typeof biomarker.value === 'number' ? biomarker.value.toFixed(2) : biomarker.value}
                  <Typography 
                    component="span" 
                    sx={{ 
                      fontSize: '1rem', 
                      ml: 0.5,
                      color: alpha(theme.palette.text.primary, 0.6)
                    }}
                  >
                    {biomarker.unit}
                  </Typography>
                </Typography>
                <Chip 
                  label={getStatusText()}
                  sx={{
                    mt: 2,
                    backgroundColor: alpha(getStatusColor(), 0.1),
                    color: getStatusColor(),
                    fontWeight: 500,
                    borderRadius: '8px',
                    height: 28,
                    border: 'none'
                  }}
                />
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 2.5,
                  height: '100%', 
                  borderRadius: 3,
                  backgroundColor: alpha(theme.palette.background.paper, 0.7),
                  backdropFilter: 'blur(10px)',
                  border: `1px solid ${alpha(theme.palette.divider, 0.05)}`,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center'
                }}
              >
                <Typography 
                  variant="overline" 
                  sx={{ 
                    color: theme.palette.text.secondary,
                    fontSize: '0.75rem',
                    letterSpacing: 1
                  }}
                >
                  Reference Range
                </Typography>
                <Typography 
                  variant="h5" 
                  sx={{ 
                    fontWeight: 500,
                    color: theme.palette.text.primary,
                    mt: 1
                  }}
                >
                  {referenceRange}
                </Typography>
                <Typography 
                  variant="body2"
                  color="text.secondary"
                  sx={{ mt: 2, fontSize: '0.75rem' }}
                >
                  Standard range for healthy individuals
                </Typography>
              </Paper>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 2.5,
                  height: '100%', 
                  borderRadius: 3,
                  backgroundColor: alpha(theme.palette.background.paper, 0.7),
                  backdropFilter: 'blur(10px)',
                  border: `1px solid ${alpha(theme.palette.divider, 0.05)}`,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center'
                }}
              >
                <Typography 
                  variant="overline" 
                  sx={{ 
                    color: theme.palette.text.secondary,
                    fontSize: '0.75rem',
                    letterSpacing: 1
                  }}
                >
                  Category
                </Typography>
                <Typography 
                  variant="h5" 
                  sx={{ 
                    fontWeight: 500,
                    color: theme.palette.primary.main,
                    mt: 1
                  }}
                >
                  {biomarker.category || 'General'}
                </Typography>
                <Typography 
                  variant="body2"
                  color="text.secondary"
                  sx={{ mt: 2, fontSize: '0.75rem' }}
                >
                  {biomarker.reportDate ? `Last measured: ${new Date(biomarker.reportDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}` : 'Biomarker classification group'}
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>
        
        {/* Explanation Content */}
        <Box sx={{ p: 3 }}>
          {loading ? (
            <Box 
              sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                justifyContent: 'center', 
                py: 8 
              }}
            >
              <CircularProgress 
                size={48} 
                thickness={4} 
                sx={{ color: theme.palette.primary.main }} 
              />
              <Typography 
                variant="h6" 
                sx={{ mt: 3, fontWeight: 500 }}
              >
                Analyzing your biomarker data
              </Typography>
              <Typography 
                variant="body2" 
                color="text.secondary" 
                sx={{ mt: 1, textAlign: 'center', maxWidth: 400 }}
              >
                Please wait while our AI generates a personalized explanation based on your test results.
              </Typography>
            </Box>
          ) : error ? (
            <Box 
              sx={{ 
                p: 3, 
                borderRadius: 3,
                backgroundColor: alpha(theme.palette.error.main, 0.05),
                border: `1px solid ${alpha(theme.palette.error.main, 0.1)}`,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center'
              }}
            >
              <Typography 
                variant="h6" 
                color="error.main" 
                sx={{ mb: 1.5, fontWeight: 500 }}
              >
                Unable to Generate Explanation
              </Typography>
              <Typography 
                variant="body2" 
                sx={{ mb: 2, textAlign: 'center', maxWidth: 500 }}
              >
                {error}
              </Typography>
              <Button 
                variant="outlined" 
                color="primary"
                onClick={onClose}
                sx={{ 
                  mt: 2,
                  borderRadius: '10px',
                  px: 3,
                  py: 1,
                  textTransform: 'none'
                }}
              >
                Close
              </Button>
            </Box>
          ) : explanation ? (
            <>
              <Box sx={{ mb: 4 }}>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    mb: 2.5
                  }}
                >
                  <InfoIcon 
                    sx={{ 
                      mr: 1.5, 
                      color: theme.palette.primary.main 
                    }} 
                  />
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontWeight: 600,
                      color: theme.palette.text.primary
                    }}
                  >
                    About {biomarker.name}
                  </Typography>
                </Box>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3,
                    borderRadius: 3,
                    backgroundColor: alpha(theme.palette.background.paper, 0.5),
                    backdropFilter: 'blur(10px)',
                    border: `1px solid ${alpha(theme.palette.divider, 0.05)}`,
                  }}
                >
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      lineHeight: 1.7,
                      color: alpha(theme.palette.text.primary, 0.9)
                    }}
                  >
                    {explanation.general_explanation}
                  </Typography>
                </Paper>
              </Box>
              
              <Box>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center',
                    mb: 2.5
                  }}
                >
                  <BarChartIcon 
                    sx={{ 
                      mr: 1.5, 
                      color: theme.palette.secondary.main 
                    }} 
                  />
                  <Typography 
                    variant="h6" 
                    sx={{ 
                      fontWeight: 600,
                      color: theme.palette.text.primary
                    }}
                  >
                    Your Results Analyzed
                  </Typography>
                </Box>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3,
                    borderRadius: 3,
                    backgroundColor: alpha(theme.palette.background.paper, 0.5),
                    backdropFilter: 'blur(10px)',
                    border: `1px solid ${alpha(theme.palette.divider, 0.05)}`,
                  }}
                >
                  <Typography 
                    variant="body1" 
                    sx={{ 
                      lineHeight: 1.7,
                      color: alpha(theme.palette.text.primary, 0.9),
                      whiteSpace: 'pre-line'
                    }}
                  >
                    {explanation.specific_explanation}
                  </Typography>
                </Paper>
              </Box>
            </>
          ) : (
            <Box 
              sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                justifyContent: 'center', 
                py: 8 
              }}
            >
              <Typography 
                variant="h6" 
                sx={{ fontWeight: 500 }}
              >
                No data available
              </Typography>
              <Typography 
                variant="body2" 
                color="text.secondary" 
                sx={{ mt: 1, textAlign: 'center' }}
              >
                Try refreshing the page or selecting a different biomarker.
              </Typography>
            </Box>
          )}
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ px: 3, py: 2, borderTop: `1px solid ${alpha(theme.palette.divider, 0.1)}` }}>
        <Button 
          onClick={onClose}
          sx={{
            borderRadius: '10px',
            textTransform: 'none',
            px: 3,
            fontWeight: 500
          }}
        >
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ExplanationModal; 