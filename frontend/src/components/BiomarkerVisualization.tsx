import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, CircularProgress, Alert, Button, Grid, List, ListItem, ListItemText, Chip, Tooltip } from '@mui/material'; // Removed Tabs, Tab
import type { Biomarker } from '../types/biomarker';
// Removed unused Plotly import
// Removed unused createPlotlyComponent import
import PsychologyIcon from '@mui/icons-material/Psychology';
import WarningIcon from '@mui/icons-material/Warning';

// Removed unused Plot constant

// Example biomarker descriptions for educational content
const BIOMARKER_INFO: Record<string, { description: string, normalRange: string, impact: string }> = {
  'Hemoglobin': {
    description: 'A protein in your red blood cells that carries oxygen from your lungs to the rest of your body.',
    normalRange: 'Males: 13.5-17.5 g/dL, Females: 12.0-15.5 g/dL',
    impact: 'Low levels may indicate anemia. High levels can be seen in lung diseases or living at high altitudes.'
  },
  'Glucose': {
    description: 'A type of sugar in your blood that is a major source of energy for cells.',
    normalRange: 'Fasting: 70-99 mg/dL',
    impact: 'High levels may indicate diabetes or prediabetes. Low levels can cause dizziness and fatigue.'
  },
  'Cholesterol': {
    description: 'A waxy substance found in your blood that your body needs to build cells.',
    normalRange: 'Total: Below 200 mg/dL',
    impact: 'High levels increase risk of heart disease. Different types (HDL, LDL) have different impacts.'
  },
  'Vitamin D': {
    description: 'A nutrient that helps your body absorb calcium and maintain bone health.',
    normalRange: '20-50 ng/mL',
    impact: 'Low levels may lead to bone problems. Too much can cause calcium buildup in blood.'
  },
  'TSH': {
    description: 'Thyroid Stimulating Hormone controls thyroid gland function and hormone release.',
    normalRange: '0.4-4.0 mIU/L',
    impact: 'High levels may indicate hypothyroidism. Low levels can indicate hyperthyroidism.'
  }
};

// Default info for biomarkers not in our list
const DEFAULT_INFO = {
  description: 'A health indicator measured in your lab test.',
  normalRange: 'Refer to your lab report for specific reference ranges.',
  impact: 'Abnormal values may require further investigation by your healthcare provider.'
};

interface BiomarkerVisualizationProps {
  biomarkers: Biomarker[];
  isLoading?: boolean;
  error?: string | null;
  onExplainWithAI?: (biomarker: Biomarker) => void;
  showSource?: boolean;
}

// Removed unused TabPanelProps interface and TabPanel component

/**
 * BiomarkerVisualization component displays biomarker data in visual charts
 * and provides educational information about what the markers mean.
 */
const BiomarkerVisualization: React.FC<BiomarkerVisualizationProps> = ({
  biomarkers,
  isLoading = false,
  error = null,
  onExplainWithAI,
  showSource = false
}) => {
  // Removed unused tabValue state and handleTabChange function
  const [selectedBiomarker, setSelectedBiomarker] = useState<Biomarker | null>(null);

  // When biomarkers change, select the first one by default
  useEffect(() => {
    if (biomarkers && biomarkers.length > 0) {
      setSelectedBiomarker(biomarkers[0]);
    }
  }, [biomarkers]);

  // Get biomarker info
  const getBiomarkerInfo = (name: string) => {
    // Try exact match
    if (BIOMARKER_INFO[name]) {
      return BIOMARKER_INFO[name];
    }
    
    // Try case-insensitive match
    const lowerName = name.toLowerCase();
    const key = Object.keys(BIOMARKER_INFO).find(k => k.toLowerCase() === lowerName);
    
    if (key) {
      return BIOMARKER_INFO[key];
    }
    
    // Return default info
    return DEFAULT_INFO;
  };

  // Removed unused prepareBarChartData function

  const renderReferenceRangeIndicator = (biomarker: Biomarker) => {
    if (!biomarker) return null;

    const hasLow = biomarker.reference_range_low != null; // Use != null check
    const hasHigh = biomarker.reference_range_high != null; // Use != null check

    if (!hasLow && !hasHigh) {
      return null;
    }
    
    const rangeText = biomarker.referenceRange ||
      ((hasLow && hasHigh) ? `${biomarker.reference_range_low}-${biomarker.reference_range_high}` :
       (hasLow ? `> ${biomarker.reference_range_low}` : `< ${biomarker.reference_range_high ?? 'N/A'}`)); // Added nullish coalescing

    const isOutOfRange = biomarker.isAbnormal ||
      (hasLow && biomarker.value < (biomarker.reference_range_low ?? -Infinity)) || // Added nullish coalescing
      (hasHigh && biomarker.value > (biomarker.reference_range_high ?? Infinity)); // Added nullish coalescing

    return (
      <Box sx={{ mt: 1, mb: 3, display: 'flex', alignItems: 'center' }}>
        <Typography variant="body2" sx={{ mr: 2 }}>
          Normal Range: {rangeText} {biomarker.unit}
        </Typography>
        <Box 
          sx={{ 
            height: 10, 
            width: '100%', 
            bgcolor: 'grey.200',
            borderRadius: 5,
            position: 'relative',
          }}
        >
          {hasLow && hasHigh && (
            <Box 
              sx={{ 
                position: 'absolute',
                height: '100%',
                left: '20%',
                right: '20%',
                bgcolor: 'success.light',
                borderRadius: 5,
              }}
            />
          )}
          <Box 
            sx={{ 
              position: 'absolute',
              height: '100%',
              width: 12,
              bgcolor: isOutOfRange ? 'error.main' : 'primary.main',
              borderRadius: '50%',
              left: `${Math.max(Math.min(
                hasLow && hasHigh ? 
                  // Scale value between low and high to 20%-80% of the bar
                  // Added nullish coalescing for safety, although hasLow/hasHigh should guard this
                  20 + (biomarker.value - (biomarker.reference_range_low ?? 0)) /
                  ((biomarker.reference_range_high ?? biomarker.value) - (biomarker.reference_range_low ?? 0)) * 60 : 50
              , 95), 5)}%`,
              transform: 'translateX(-50%)',
              top: 0,
            }}
          />
        </Box>
      </Box>
    );
  };

  // Removed unused renderTrendChart function

  // If loading or error, show appropriate message
  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        {error}
      </Alert>
    );
  }

  if (!biomarkers || biomarkers.length === 0) {
    return (
      <Alert severity="info">
        No biomarkers available to visualize. Please upload a lab report.
      </Alert>
    );
  }

  return (
    <Box>
      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          {/* List of biomarkers */}
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Select a Biomarker
            </Typography>
            <List>
              {biomarkers.map((biomarker) => (
                <ListItem
                  key={biomarker.id}
                  // Removed 'button' prop
                  // Removed 'selected' prop to fix TS error
                  onClick={() => setSelectedBiomarker(biomarker)}
                  sx={{
                    cursor: 'pointer',
                    '&:hover': { backgroundColor: 'action.hover' },
                    // Apply selected background color conditionally
                    ...(selectedBiomarker?.id === biomarker.id && {
                      backgroundColor: 'action.selected',
                      '&:hover': {
                        backgroundColor: 'action.selected', // Keep selected color on hover
                      },
                    }),
                  }}
                >
                  <ListItemText
                    primary={biomarker.name} 
                    secondary={`${biomarker.value} ${biomarker.unit}`} 
                  />
                  {showSource && biomarker.fileId && (
                    <Tooltip title="Source Report">
                      <Chip 
                        size="small" 
                        label={new Date(biomarker.reportDate || biomarker.date || '').toLocaleDateString()} 
                        sx={{ ml: 1 }} 
                      />
                    </Tooltip>
                  )}
                  {biomarker.isAbnormal && (
                    <Tooltip title="Abnormal Value">
                      <WarningIcon 
                        color="warning" 
                        fontSize="small" 
                        sx={{ ml: 1 }} 
                      />
                    </Tooltip>
                  )}
                </ListItem>
              ))}
            </List>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={9}>
          {/* Content area */}
          <Paper sx={{ p: 3 }}>
            {selectedBiomarker ? (
              <>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                  <Box>
                    <Typography variant="h5" component="h2" gutterBottom>
                      {selectedBiomarker.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" paragraph>
                      {selectedBiomarker.category || 'Uncategorized'} • 
                      Last tested: {new Date(selectedBiomarker.reportDate || selectedBiomarker.date || '').toLocaleDateString()}
                      {showSource && selectedBiomarker.fileId && (
                        <> • Source: {selectedBiomarker.fileName || `Report ${selectedBiomarker.fileId.substring(0, 6)}`}</>
                      )}
                    </Typography>
                  </Box>
                  {onExplainWithAI && (
                    <Button
                      variant="contained"
                      color="primary"
                      startIcon={<PsychologyIcon />}
                      onClick={() => onExplainWithAI(selectedBiomarker)}
                    >
                      Explain with AI
                    </Button>
                  )}
                </Box>
                
                <Typography variant="subtitle1" sx={{ fontWeight: 'bold' }}>
                  Current Value: {selectedBiomarker.value} {selectedBiomarker.unit}
                </Typography>
                
                {renderReferenceRangeIndicator(selectedBiomarker)}
                
                <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
                  <Typography variant="h6" gutterBottom>
                    What is {selectedBiomarker.name}?
                  </Typography>
                  <Typography variant="body1" paragraph>
                    {getBiomarkerInfo(selectedBiomarker.name).description}
                  </Typography>
                  
                  <Typography variant="h6" gutterBottom>
                    Normal Range
                  </Typography>
                  <Typography variant="body1" paragraph>
                    {getBiomarkerInfo(selectedBiomarker.name).normalRange}
                  </Typography>
                  
                  <Typography variant="h6" gutterBottom>
                    Health Impact
                  </Typography>
                  <Typography variant="body1">
                    {getBiomarkerInfo(selectedBiomarker.name).impact}
                  </Typography>
                </Paper>
                
                <Alert severity="info">
                  <Typography variant="body2">
                    This information is for educational purposes only and should not replace professional medical advice.
                    Always consult with your healthcare provider about your lab results.
                  </Typography>
                </Alert>
              </>
            ) : (
              <Typography variant="body1" color="text.secondary" align="center">
                Select a biomarker from the list to view details
              </Typography>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default BiomarkerVisualization;
