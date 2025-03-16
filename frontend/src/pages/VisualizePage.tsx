import React, { useState, useEffect } from 'react';
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
  Alert,
  Button,
  Tab,
  Tabs,
  Chip,
  TextField,
  Autocomplete,
  Skeleton
} from '@mui/material';
import Plot from 'react-plotly.js';
import { 
  getAllBiomarkers, 
  getBiomarkersByFileId,
  getBiomarkerCategories, 
  Biomarker 
} from '../services/api';
import BiomarkerTable from '../components/BiomarkerTable';
import { useNavigate, useLocation } from 'react-router-dom';

// Interface for time-series data
interface TimeSeriesData {
  dates: string[];
  values: number[];
  units: string;
  referenceRange: { min: number | null; max: number | null };
  categories: string[];
  biomarkerIds: number[];
}

// Group biomarkers by name and construct time series
const constructTimeSeriesData = (biomarkers: Biomarker[]): Record<string, TimeSeriesData> => {
  const timeSeriesData: Record<string, TimeSeriesData> = {};
  
  // Group biomarkers by name
  const biomarkersByName = biomarkers.reduce((acc, biomarker) => {
    const name = biomarker.name;
    if (!acc[name]) {
      acc[name] = [];
    }
    acc[name].push(biomarker);
    return acc;
  }, {} as Record<string, Biomarker[]>);
  
  // Construct time series for each biomarker
  Object.entries(biomarkersByName).forEach(([name, biomarkers]) => {
    // Sort biomarkers by date (assuming biomarker has a date property)
    const sortedBiomarkers = [...biomarkers].sort((a, b) => {
      const dateA = a.testDate ? new Date(a.testDate).getTime() : 0;
      const dateB = b.testDate ? new Date(b.testDate).getTime() : 0;
      return dateA - dateB;
    });
    
    timeSeriesData[name] = {
      dates: sortedBiomarkers.map(b => b.testDate || new Date().toISOString().split('T')[0]),
      values: sortedBiomarkers.map(b => b.value),
      units: sortedBiomarkers[0].unit,
      referenceRange: {
        min: sortedBiomarkers[0].reference_range_low,
        max: sortedBiomarkers[0].reference_range_high
      },
      categories: sortedBiomarkers.map(b => b.category || 'Uncategorized').filter((v, i, a) => a.indexOf(v) === i),
      biomarkerIds: sortedBiomarkers.map(b => b.id)
    };
  });
  
  return timeSeriesData;
};

const VisualizePage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  
  // State for data and loading
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  const [timeSeriesData, setTimeSeriesData] = useState<Record<string, TimeSeriesData>>({});
  const [biomarkerNames, setBiomarkerNames] = useState<string[]>([]);
  const [biomarkerCategories, setBiomarkerCategories] = useState<string[]>([]);
  const [selectedBiomarker, setSelectedBiomarker] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<number>(0);
  
  // Load data on mount
  useEffect(() => {
    const loadData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Check if we have file IDs in session storage (from upload page)
        const fileIdsFromSession = sessionStorage.getItem('selectedFileIds');
        const parsedFileIds = fileIdsFromSession ? JSON.parse(fileIdsFromSession) : [];
        setSelectedFileIds(parsedFileIds);
        
        let biomarkersData: Biomarker[] = [];
        
        // If we have file IDs, get biomarkers for those files
        if (parsedFileIds.length > 0) {
          // Fetch biomarkers for all selected files
          const biomarkerPromises = parsedFileIds.map(fileId => getBiomarkersByFileId(fileId));
          const biomarkerResults = await Promise.all(biomarkerPromises);
          
          // Combine all biomarkers
          biomarkersData = biomarkerResults.flat();
        } else {
          // Otherwise, get all biomarkers
          biomarkersData = await getAllBiomarkers();
        }
        
        // Deduplicate biomarkers
        const uniqueBiomarkers: Biomarker[] = [];
        const uniqueKeys = new Set<string>();
        
        biomarkersData.forEach(biomarker => {
          const key = `${biomarker.name}_${biomarker.value}_${biomarker.unit}`;
          if (!uniqueKeys.has(key)) {
            uniqueKeys.add(key);
            uniqueBiomarkers.push(biomarker);
          }
        });
        
        // Set biomarkers and construct time series data
        setBiomarkers(uniqueBiomarkers);
        
        if (uniqueBiomarkers.length > 0) {
          const timeSeriesData = constructTimeSeriesData(uniqueBiomarkers);
          setTimeSeriesData(timeSeriesData);
          
          const biomarkerNames = Object.keys(timeSeriesData);
          setBiomarkerNames(biomarkerNames);
          
          if (biomarkerNames.length > 0) {
            setSelectedBiomarker(biomarkerNames[0]);
          }
          
          // Get unique categories
          const categories = [...new Set(uniqueBiomarkers.map(b => b.category || 'Uncategorized'))];
          setBiomarkerCategories(['All', ...categories]);
        }
        
        // Also fetch all available categories from API
        try {
          const allCategories = await getBiomarkerCategories();
          // Merge with existing categories
          const uniqueCategories = [...new Set(['All', ...biomarkerCategories, ...allCategories])];
          setBiomarkerCategories(uniqueCategories);
        } catch (err) {
          console.error('Error fetching categories:', err);
          // Don't set an error, this is not critical
        }
        
      } catch (err: any) {
        console.error('Error loading data:', err);
        setError(`Error loading biomarker data: ${err.message || 'Unknown error'}`);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadData();
    
    // Clean up session storage
    return () => {
      sessionStorage.removeItem('selectedFileIds');
    };
  }, []);
  
  // Handle biomarker change
  const handleBiomarkerChange = (event: SelectChangeEvent<string>) => {
    setSelectedBiomarker(event.target.value);
  };
  
  // Handle category change
  const handleCategoryChange = (event: SelectChangeEvent<string>) => {
    setSelectedCategory(event.target.value);
    
    // Update biomarker names based on selected category
    if (event.target.value === 'All') {
      // Show all biomarkers
      setBiomarkerNames(Object.keys(timeSeriesData));
    } else {
      // Filter biomarkers by category
      const filteredNames = Object.entries(timeSeriesData)
        .filter(([_, data]) => data.categories.includes(event.target.value))
        .map(([name]) => name);
      
      setBiomarkerNames(filteredNames);
      
      // Update selected biomarker if current selection is not in filtered list
      if (filteredNames.length > 0 && !filteredNames.includes(selectedBiomarker)) {
        setSelectedBiomarker(filteredNames[0]);
      }
    }
  };
  
  // Handle tab change
  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  // Get data for the selected biomarker
  const biomarkerData = timeSeriesData[selectedBiomarker];
  
  const renderTabs = () => {
    return (
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          aria-label="visualization tabs"
          variant="fullWidth"
        >
          <Tab label="Time Series" id="tab-0" aria-controls="tabpanel-0" />
          <Tab label="All Biomarkers" id="tab-1" aria-controls="tabpanel-1" />
        </Tabs>
      </Box>
    );
  };
  
  const renderTimeSeries = () => {
    if (isLoading) {
      return (
        <Box sx={{ p: 3 }}>
          <Skeleton variant="rectangular" height={400} width="100%" />
        </Box>
      );
    }
    
    if (error) {
      return (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      );
    }
    
    if (biomarkers.length === 0) {
      return (
        <Box sx={{ p: 3, textAlign: 'center' }}>
          <Alert severity="info" sx={{ mb: 3 }}>
            No biomarker data available. Please upload some lab results.
          </Alert>
          <Button variant="contained" onClick={() => navigate('/upload')}>
            Go to Upload Page
          </Button>
        </Box>
      );
    }
    
    return (
      <>
        <Paper elevation={2} sx={{ p: 3, mb: 4 }}>
          <Grid container spacing={3} alignItems="center">
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="category-select-label">Category</InputLabel>
                <Select
                  labelId="category-select-label"
                  id="category-select"
                  value={selectedCategory}
                  label="Category"
                  onChange={handleCategoryChange}
                >
                  {biomarkerCategories.map((category) => (
                    <MenuItem key={category} value={category}>
                      {category}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={6}>
              <FormControl fullWidth>
                <InputLabel id="biomarker-select-label">Biomarker</InputLabel>
                <Select
                  labelId="biomarker-select-label"
                  id="biomarker-select"
                  value={selectedBiomarker}
                  label="Biomarker"
                  onChange={handleBiomarkerChange}
                  disabled={biomarkerNames.length === 0}
                >
                  {biomarkerNames.map((biomarker) => (
                    <MenuItem key={biomarker} value={biomarker}>
                      {biomarker}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>
        
        <Card raised sx={{ mb: 4 }}>
          <CardContent sx={{ p: 3 }}>
            {!biomarkerData ? (
              <Typography variant="body1" align="center">
                No data available for the selected biomarker.
              </Typography>
            ) : (
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
                  // Reference range - upper line (if available)
                  ...(biomarkerData.referenceRange.max !== null ? [{
                    x: biomarkerData.dates,
                    y: Array(biomarkerData.dates.length).fill(biomarkerData.referenceRange.max),
                    type: 'scatter',
                    mode: 'lines',
                    line: { dash: 'dash', color: 'red' },
                    name: 'Upper Limit'
                  }] : []),
                  // Reference range - lower line (if available)
                  ...(biomarkerData.referenceRange.min !== null ? [{
                    x: biomarkerData.dates,
                    y: Array(biomarkerData.dates.length).fill(biomarkerData.referenceRange.min),
                    type: 'scatter',
                    mode: 'lines',
                    line: { dash: 'dash', color: 'green' },
                    name: 'Lower Limit'
                  }] : [])
                ]}
                layout={{
                  title: `${selectedBiomarker} Trend Over Time`,
                  xaxis: { title: 'Date' },
                  yaxis: { 
                    title: `${selectedBiomarker} (${biomarkerData.units})`,
                    range: [
                      Math.min(
                        biomarkerData.referenceRange.min !== null ? biomarkerData.referenceRange.min * 0.8 : Math.min(...biomarkerData.values) * 0.8,
                        ...biomarkerData.values
                      ),
                      Math.max(
                        biomarkerData.referenceRange.max !== null ? biomarkerData.referenceRange.max * 1.2 : Math.max(...biomarkerData.values) * 1.2,
                        ...biomarkerData.values
                      )
                    ]
                  },
                  legend: { orientation: 'h', y: -0.2 },
                  height: 500,
                  margin: { l: 50, r: 50, t: 80, b: 80 }
                }}
                config={{ responsive: true }}
                style={{ width: '100%' }}
              />
            )}
          </CardContent>
        </Card>
        
        {biomarkerData && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom color="primary">
                    Insights
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Latest Value:</strong> {biomarkerData.values[biomarkerData.values.length - 1]} {biomarkerData.units} 
                    ({biomarkerData.dates[biomarkerData.dates.length - 1]})
                  </Typography>
                  <Typography variant="body1" paragraph>
                    <strong>Status:</strong> {' '}
                    {biomarkerData.referenceRange.max !== null && biomarkerData.values[biomarkerData.values.length - 1] > biomarkerData.referenceRange.max ? (
                      <span style={{ color: 'red' }}>Above Reference Range</span>
                    ) : biomarkerData.referenceRange.min !== null && biomarkerData.values[biomarkerData.values.length - 1] < biomarkerData.referenceRange.min ? (
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
                  {biomarkerData.categories.length > 0 && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body1" gutterBottom>
                        <strong>Categories:</strong>
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {biomarkerData.categories.map(category => (
                          <Chip key={category} label={category} size="small" color="primary" variant="outlined" />
                        ))}
                      </Box>
                    </Box>
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
                    {getBiomarkerInfo(selectedBiomarker)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </>
    );
  };
  
  const renderAllBiomarkers = () => {
    return (
      <Box sx={{ mt: 2 }}>
        <BiomarkerTable 
          biomarkers={biomarkers} 
          isLoading={isLoading}
          error={error}
        />
      </Box>
    );
  };
  
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
        
        {renderTabs()}
        
        <Box role="tabpanel" hidden={activeTab !== 0} id="tabpanel-0" aria-labelledby="tab-0">
          {activeTab === 0 && renderTimeSeries()}
        </Box>
        
        <Box role="tabpanel" hidden={activeTab !== 1} id="tabpanel-1" aria-labelledby="tab-1">
          {activeTab === 1 && renderAllBiomarkers()}
        </Box>
      </Box>
    </Container>
  );
};

// Helper function to get biomarker information text
const getBiomarkerInfo = (biomarkerName: string): string => {
  const biomarkerInfo: Record<string, string> = {
    'Glucose': "Glucose is a type of sugar in your blood. It's your body's main source of energy. High blood glucose levels can indicate diabetes or prediabetes.",
    'Total Cholesterol': "Total cholesterol is the sum of HDL, LDL, and VLDL cholesterol in your blood. High levels can increase your risk of heart disease.",
    'HDL Cholesterol': "HDL (High-Density Lipoprotein) is often called 'good' cholesterol. It helps remove other forms of cholesterol from your bloodstream.",
    'LDL Cholesterol': "LDL (Low-Density Lipoprotein) is often called 'bad' cholesterol. High levels can lead to plaque buildup in your arteries.",
    'Triglycerides': "Triglycerides are a type of fat in your blood. High levels, often caused by excess calories, can increase heart disease risk.",
    'Vitamin D': "Vitamin D is essential for calcium absorption and bone health. It also plays a role in immune function and inflammation reduction.",
    'Hemoglobin A1C': "Hemoglobin A1C represents your average blood sugar level over the past 2-3 months. It's commonly used to diagnose diabetes and monitor blood sugar control.",
    'Creatinine': "Creatinine is a waste product filtered by your kidneys. High levels in blood can indicate kidney problems."
  };
  
  return biomarkerInfo[biomarkerName] || 
    `${biomarkerName} is an important biomarker in your health panel. Regular monitoring can help track changes in your health status over time.`;
};

export default VisualizePage; 