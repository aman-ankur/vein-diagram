import React, { useState, useEffect } from 'react';
import { Box, Typography, Paper, Tabs, Tab, CircularProgress, Alert } from '@mui/material';
import { Biomarker } from './BiomarkerTable';
import Plotly from 'plotly.js-basic-dist';
import createPlotlyComponent from 'react-plotly.js/factory';

// Create the Plot component
const Plot = createPlotlyComponent(Plotly);

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
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`visualization-tabpanel-${index}`}
      aria-labelledby={`visualization-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

/**
 * BiomarkerVisualization component displays biomarker data in visual charts
 * and provides educational information about what the markers mean.
 */
const BiomarkerVisualization: React.FC<BiomarkerVisualizationProps> = ({
  biomarkers,
  isLoading = false,
  error = null
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [selectedBiomarker, setSelectedBiomarker] = useState<Biomarker | null>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

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

  // Prepare data for charts
  const prepareBarChartData = () => {
    const sortedBiomarkers = [...biomarkers]
      .sort((a, b) => {
        // If both have reference ranges, sort by percentage of range
        if (a.reference_range_high !== null && a.reference_range_low !== null &&
            b.reference_range_high !== null && b.reference_range_low !== null) {
          const aRange = a.reference_range_high - a.reference_range_low;
          const bRange = b.reference_range_high - b.reference_range_low;
          const aPercentage = aRange > 0 ? (a.value - a.reference_range_low) / aRange : 0;
          const bPercentage = bRange > 0 ? (b.value - b.reference_range_low) / bRange : 0;
          return bPercentage - aPercentage; // Descending by percentage
        }
        // Otherwise sort by abnormal status
        return (b.is_abnormal ? 1 : 0) - (a.is_abnormal ? 1 : 0);
      })
      .slice(0, 10); // Show only top 10 biomarkers
      
    return {
      x: sortedBiomarkers.map(b => b.name),
      y: sortedBiomarkers.map(b => b.value),
      marker: {
        color: sortedBiomarkers.map(b => 
          b.is_abnormal ? 'rgba(255, 99, 71, 0.7)' : 'rgba(75, 192, 192, 0.7)'
        ),
      },
      type: 'bar',
    };
  };

  const renderReferenceRangeIndicator = (biomarker: Biomarker) => {
    if (!biomarker) return null;
    
    const hasLow = biomarker.reference_range_low !== null;
    const hasHigh = biomarker.reference_range_high !== null;
    
    if (!hasLow && !hasHigh) {
      return null;
    }
    
    const rangeText = biomarker.reference_range_text || 
      ((hasLow && hasHigh) ? `${biomarker.reference_range_low}-${biomarker.reference_range_high}` :
       (hasLow ? `> ${biomarker.reference_range_low}` : `< ${biomarker.reference_range_high}`));
       
    const isOutOfRange = biomarker.is_abnormal || 
      (hasLow && biomarker.value < biomarker.reference_range_low) ||
      (hasHigh && biomarker.value > biomarker.reference_range_high);
    
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
                  20 + (biomarker.value - biomarker.reference_range_low) / 
                  (biomarker.reference_range_high - biomarker.reference_range_low) * 60 : 50
              , 95), 5)}%`,
              transform: 'translateX(-50%)',
              top: 0,
            }}
          />
        </Box>
      </Box>
    );
  };

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
    <Paper sx={{ width: '100%', mb: 4 }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          aria-label="biomarker visualization tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Overview" id="visualization-tab-0" aria-controls="visualization-tabpanel-0" />
          <Tab label="Biomarker Information" id="visualization-tab-1" aria-controls="visualization-tabpanel-1" />
        </Tabs>
      </Box>
      
      <TabPanel value={tabValue} index={0}>
        <Typography variant="h6" gutterBottom>
          Biomarker Values Overview
        </Typography>
        
        <Box sx={{ height: 400, width: '100%' }}>
          <Plot
            data={[prepareBarChartData()]}
            layout={{
              autosize: true,
              title: 'Top Biomarkers',
              yaxis: {
                title: 'Value',
              },
              xaxis: {
                title: 'Biomarker',
              },
              margin: { l: 50, r: 50, b: 100, t: 50, pad: 4 },
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler={true}
          />
        </Box>
        
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          * Red bars indicate values outside the normal range
        </Typography>
      </TabPanel>
      
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 2 }}>
          <Box sx={{ width: { xs: '100%', md: '30%' } }}>
            <Typography variant="h6" gutterBottom>
              Select a Biomarker
            </Typography>
            <Box sx={{ maxHeight: 400, overflow: 'auto' }}>
              {biomarkers.map((biomarker) => (
                <Box 
                  key={biomarker.id}
                  onClick={() => setSelectedBiomarker(biomarker)}
                  sx={{
                    p: 1,
                    cursor: 'pointer',
                    bgcolor: selectedBiomarker?.id === biomarker.id ? 'primary.light' : 'background.paper',
                    borderRadius: 1,
                    mb: 0.5,
                    '&:hover': {
                      bgcolor: 'primary.light',
                    },
                  }}
                >
                  <Typography 
                    variant="body1"
                    sx={{ 
                      fontWeight: biomarker.is_abnormal ? 'bold' : 'normal',
                      color: biomarker.is_abnormal ? 'error.main' : 'text.primary',
                    }}
                  >
                    {biomarker.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {biomarker.value} {biomarker.unit}
                  </Typography>
                </Box>
              ))}
            </Box>
          </Box>
          
          <Box sx={{ flex: 1 }}>
            {selectedBiomarker && (
              <>
                <Typography variant="h5" sx={{ mb: 2 }}>
                  {selectedBiomarker.name}
                </Typography>
                
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
            )}
          </Box>
        </Box>
      </TabPanel>
    </Paper>
  );
};

export default BiomarkerVisualization; 