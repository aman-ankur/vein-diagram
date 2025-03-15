import React, { useState } from 'react';
import { 
  Typography, 
  Container, 
  Box, 
  Paper, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  Grid,
  Card,
  CardContent,
  SelectChangeEvent,
  CircularProgress,
  Alert
} from '@mui/material';
import Plot from 'react-plotly.js';

// Mock data for demo purposes
const mockBiomarkers = [
  'Glucose',
  'Total Cholesterol',
  'HDL Cholesterol',
  'LDL Cholesterol',
  'Triglycerides',
  'Vitamin D',
  'Hemoglobin A1C',
  'Creatinine'
];

// Mock data for time series
const mockTimeSeriesData = {
  'Glucose': {
    dates: ['2023-01-05', '2023-03-12', '2023-06-20', '2023-09-15', '2023-12-01'],
    values: [99, 95, 102, 89, 92],
    units: 'mg/dL',
    referenceRange: { min: 70, max: 99 }
  },
  'Total Cholesterol': {
    dates: ['2023-01-05', '2023-06-20', '2023-12-01'],
    values: [210, 195, 185],
    units: 'mg/dL',
    referenceRange: { min: 125, max: 200 }
  },
  'HDL Cholesterol': {
    dates: ['2023-01-05', '2023-06-20', '2023-12-01'],
    values: [62, 65, 68],
    units: 'mg/dL',
    referenceRange: { min: 40, max: 60 }
  },
  'LDL Cholesterol': {
    dates: ['2023-01-05', '2023-06-20', '2023-12-01'],
    values: [128, 115, 105],
    units: 'mg/dL',
    referenceRange: { min: 0, max: 100 }
  },
  'Triglycerides': {
    dates: ['2023-01-05', '2023-06-20', '2023-12-01'],
    values: [150, 120, 135],
    units: 'mg/dL',
    referenceRange: { min: 0, max: 150 }
  },
  'Vitamin D': {
    dates: ['2023-03-12', '2023-09-15'],
    values: [28, 42],
    units: 'ng/mL',
    referenceRange: { min: 30, max: 100 }
  },
  'Hemoglobin A1C': {
    dates: ['2023-01-05', '2023-06-20', '2023-12-01'],
    values: [5.4, 5.3, 5.2],
    units: '%',
    referenceRange: { min: 4.0, max: 5.6 }
  },
  'Creatinine': {
    dates: ['2023-01-05', '2023-06-20', '2023-12-01'],
    values: [0.9, 0.95, 0.87],
    units: 'mg/dL',
    referenceRange: { min: 0.6, max: 1.2 }
  }
};

const VisualizePage: React.FC = () => {
  const [selectedBiomarker, setSelectedBiomarker] = useState<string>('Glucose');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  const handleBiomarkerChange = (event: SelectChangeEvent<string>) => {
    setSelectedBiomarker(event.target.value);
    // In a real app, you might want to fetch data here
    
    // Simulate loading for demo
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
    }, 800);
  };
  
  // Get data for the selected biomarker
  const biomarkerData = mockTimeSeriesData[selectedBiomarker as keyof typeof mockTimeSeriesData];
  
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography 
          variant="h3" 
          component="h1" 
          align="center" 
          color="primary" 
          gutterBottom
          sx={{ fontWeight: 'bold' }}
        >
          Biomarker Visualization
        </Typography>
        
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="biomarker-select-label">Biomarker</InputLabel>
                <Select
                  labelId="biomarker-select-label"
                  id="biomarker-select"
                  value={selectedBiomarker}
                  label="Biomarker"
                  onChange={handleBiomarkerChange}
                >
                  {mockBiomarkers.map((biomarker) => (
                    <MenuItem key={biomarker} value={biomarker}>
                      {biomarker}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              {biomarkerData && (
                <Box sx={{ textAlign: 'right' }}>
                  <Typography variant="body1">
                    <strong>Units:</strong> {biomarkerData.units}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Reference Range:</strong> {biomarkerData.referenceRange.min} - {biomarkerData.referenceRange.max} {biomarkerData.units}
                  </Typography>
                </Box>
              )}
            </Grid>
          </Grid>
        </Paper>
        
        <Card raised sx={{ mb: 4 }}>
          <CardContent sx={{ p: 3 }}>
            {isLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
                <CircularProgress />
              </Box>
            ) : error ? (
              <Alert severity="error">
                {error}
              </Alert>
            ) : biomarkerData ? (
              <Plot
                data={[
                  // Line for biomarker values
                  {
                    x: biomarkerData.dates,
                    y: biomarkerData.values,
                    type: 'scatter',
                    mode: 'lines+markers',
                    marker: { color: '#6200ee' },
                    name: selectedBiomarker
                  },
                  // Reference range - upper line
                  {
                    x: biomarkerData.dates,
                    y: Array(biomarkerData.dates.length).fill(biomarkerData.referenceRange.max),
                    type: 'scatter',
                    mode: 'lines',
                    line: { dash: 'dash', color: 'red' },
                    name: 'Upper Limit'
                  },
                  // Reference range - lower line
                  {
                    x: biomarkerData.dates,
                    y: Array(biomarkerData.dates.length).fill(biomarkerData.referenceRange.min),
                    type: 'scatter',
                    mode: 'lines',
                    line: { dash: 'dash', color: 'green' },
                    name: 'Lower Limit'
                  }
                ]}
                layout={{
                  title: `${selectedBiomarker} Trend Over Time`,
                  xaxis: { title: 'Date' },
                  yaxis: { 
                    title: `${selectedBiomarker} (${biomarkerData.units})`,
                    range: [
                      Math.min(biomarkerData.referenceRange.min * 0.8, ...biomarkerData.values),
                      Math.max(biomarkerData.referenceRange.max * 1.2, ...biomarkerData.values)
                    ]
                  },
                  legend: { orientation: 'h', y: -0.2 },
                  height: 500,
                  margin: { l: 50, r: 50, t: 80, b: 80 }
                }}
                config={{ responsive: true }}
                style={{ width: '100%' }}
              />
            ) : (
              <Typography variant="body1" align="center">
                No data available for the selected biomarker.
              </Typography>
            )}
          </CardContent>
        </Card>
        
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom color="primary">
                  Insights
                </Typography>
                {biomarkerData && (
                  <>
                    <Typography variant="body1" paragraph>
                      <strong>Latest Value:</strong> {biomarkerData.values[biomarkerData.values.length - 1]} {biomarkerData.units} 
                      ({biomarkerData.dates[biomarkerData.dates.length - 1]})
                    </Typography>
                    <Typography variant="body1" paragraph>
                      <strong>Status:</strong> {' '}
                      {biomarkerData.values[biomarkerData.values.length - 1] > biomarkerData.referenceRange.max ? (
                        <span style={{ color: 'red' }}>Above Reference Range</span>
                      ) : biomarkerData.values[biomarkerData.values.length - 1] < biomarkerData.referenceRange.min ? (
                        <span style={{ color: 'orange' }}>Below Reference Range</span>
                      ) : (
                        <span style={{ color: 'green' }}>Within Reference Range</span>
                      )}
                    </Typography>
                    <Typography variant="body1">
                      <strong>Trend:</strong> {' '}
                      {biomarkerData.values.length > 1 ? (
                        biomarkerData.values[biomarkerData.values.length - 1] > biomarkerData.values[biomarkerData.values.length - 2] ? (
                          <span style={{ color: 'blue' }}>Increasing</span>
                        ) : biomarkerData.values[biomarkerData.values.length - 1] < biomarkerData.values[biomarkerData.values.length - 2] ? (
                          <span style={{ color: 'green' }}>Decreasing</span>
                        ) : (
                          <span>Stable</span>
                        )
                      ) : (
                        <span>Not enough data to determine trend</span>
                      )}
                    </Typography>
                  </>
                )}
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom color="primary">
                  Information
                </Typography>
                <Typography variant="body2" paragraph>
                  {selectedBiomarker === 'Glucose' && 
                    "Glucose is a type of sugar in your blood. It's your body's main source of energy. High blood glucose levels can indicate diabetes or prediabetes."}
                  {selectedBiomarker === 'Total Cholesterol' && 
                    "Total cholesterol is the sum of HDL, LDL, and VLDL cholesterol in your blood. High levels can increase your risk of heart disease."}
                  {selectedBiomarker === 'HDL Cholesterol' && 
                    "HDL (High-Density Lipoprotein) is often called 'good' cholesterol. It helps remove other forms of cholesterol from your bloodstream."}
                  {selectedBiomarker === 'LDL Cholesterol' && 
                    "LDL (Low-Density Lipoprotein) is often called 'bad' cholesterol. High levels can lead to plaque buildup in your arteries."}
                  {selectedBiomarker === 'Triglycerides' && 
                    "Triglycerides are a type of fat in your blood. High levels, often caused by excess calories, can increase heart disease risk."}
                  {selectedBiomarker === 'Vitamin D' && 
                    "Vitamin D is essential for calcium absorption and bone health. It also plays a role in immune function and inflammation reduction."}
                  {selectedBiomarker === 'Hemoglobin A1C' && 
                    "Hemoglobin A1C represents your average blood sugar level over the past 2-3 months. It's commonly used to diagnose diabetes and monitor blood sugar control."}
                  {selectedBiomarker === 'Creatinine' && 
                    "Creatinine is a waste product filtered by your kidneys. High levels in blood can indicate kidney problems."}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default VisualizePage; 