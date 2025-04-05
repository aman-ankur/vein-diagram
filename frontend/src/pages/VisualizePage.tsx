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
  // CircularProgress removed - unused
  Alert,
  Button,
  Tab,
  Tabs,
  Chip,
  // TextField removed - unused
  // Autocomplete removed - unused
  Skeleton
} from '@mui/material';
import Plot from 'react-plotly.js';
import type { PlotType, Dash } from 'plotly.js'; // Import PlotType and Dash for casting
import {
  getAllBiomarkers,
  getBiomarkersByFileId,
  getBiomarkerCategories,
  // Biomarker removed - import from types instead
} from '../services/api';
import type { Biomarker } from '../types/biomarker.d'; // Corrected import path
import BiomarkerTable from '../components/BiomarkerTable';
import { useNavigate } from 'react-router-dom'; // Removed useLocation

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
      // Use reportDate or date, default to 0 if neither exists
      const dateA = a.reportDate ? new Date(a.reportDate).getTime() : (a.date ? new Date(a.date).getTime() : 0);
      const dateB = b.reportDate ? new Date(b.reportDate).getTime() : (b.date ? new Date(b.date).getTime() : 0);
      return dateA - dateB; // Sort ascending
    });

    // Ensure dates are valid strings before using them
    const validDates = sortedBiomarkers.map(b => b.reportDate || b.date || new Date().toISOString()).filter(d => typeof d === 'string');

    timeSeriesData[name] = {
      dates: validDates,
      values: sortedBiomarkers.map(b => b.value),
      units: sortedBiomarkers[0]?.unit || 'N/A', // Use optional chaining and default
      referenceRange: {
        min: sortedBiomarkers[0]?.reference_range_low ?? null, // Use optional chaining and nullish coalescing
        max: sortedBiomarkers[0]?.reference_range_high ?? null // Use optional chaining and nullish coalescing
      },
      categories: [...new Set(sortedBiomarkers.map(b => b.category || 'Uncategorized'))], // Simplified category collection
      biomarkerIds: sortedBiomarkers.map(b => b.id)
    };
  });

  return timeSeriesData;
};

const VisualizePage: React.FC = () => {
  const navigate = useNavigate();
  // const location = useLocation(); // Removed unused variable

  // State for data and loading
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  const [timeSeriesData, setTimeSeriesData] = useState<Record<string, TimeSeriesData>>({});
  const [biomarkerNames, setBiomarkerNames] = useState<string[]>([]);
  const [biomarkerCategories, setBiomarkerCategories] = useState<string[]>([]);
  const [selectedBiomarker, setSelectedBiomarker] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  // const [selectedFileIds, setSelectedFileIds] = useState<string[]>([]); // Removed unused state
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
        let parsedFileIds: string[] = []; // Initialize as empty array

        if (fileIdsFromSession) {
          try {
            const parsed = JSON.parse(fileIdsFromSession);
            // Ensure parsed value is an array of strings
            if (Array.isArray(parsed) && parsed.every(item => typeof item === 'string')) {
              parsedFileIds = parsed;
            } else {
              console.warn('Invalid format for selectedFileIds in session storage. Expected string array.');
            }
          } catch (parseError) {
            console.error('Error parsing selectedFileIds from session storage:', parseError);
          }
        }
        // setSelectedFileIds(parsedFileIds); // Removed unused state setter

        let biomarkersData: Biomarker[] = [];

        // If we have file IDs, get biomarkers for those files
        if (parsedFileIds.length > 0) {
          // Fetch biomarkers for all selected files
          const biomarkerPromises = parsedFileIds.map((fileId: string) => getBiomarkersByFileId(fileId)); // Added type annotation
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
          // Use a more robust key if ID is available and unique per instance
          const key = biomarker.id ? biomarker.id.toString() : `${biomarker.name}_${biomarker.value}_${biomarker.unit}_${biomarker.reportDate || biomarker.date}`;
          if (!uniqueKeys.has(key)) {
            uniqueKeys.add(key);
            uniqueBiomarkers.push(biomarker);
          }
        });

        // Set biomarkers and construct time series data
        setBiomarkers(uniqueBiomarkers);

        if (uniqueBiomarkers.length > 0) {
          const constructedTimeSeriesData = constructTimeSeriesData(uniqueBiomarkers);
          setTimeSeriesData(constructedTimeSeriesData);

          const names = Object.keys(constructedTimeSeriesData);
          setBiomarkerNames(names);

          if (names.length > 0) {
            setSelectedBiomarker(names[0]);
          }

          // Get unique categories from the processed data
          const categoriesFromData = [...new Set(uniqueBiomarkers.map(b => b.category || 'Uncategorized'))];
          setBiomarkerCategories(['All', ...categoriesFromData]); // Set initial categories
        } else {
          // Reset states if no biomarkers found
          setTimeSeriesData({});
          setBiomarkerNames([]);
          setSelectedBiomarker('');
          setBiomarkerCategories(['All']);
        }

        // Also fetch all available categories from API to ensure completeness
        try {
          const allApiCategories = await getBiomarkerCategories();
          // Merge with existing categories derived from data
          setBiomarkerCategories(prev => ['All', ...new Set([...prev.slice(1), ...allApiCategories])].sort((a, b) => a === 'All' ? -1 : b === 'All' ? 1 : a.localeCompare(b)));
        } catch (err) {
          console.error('Error fetching all categories:', err);
          // Don't set an error, this is not critical, use categories from data
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
  }, []); // Run only on mount

  // Handle biomarker change
  const handleBiomarkerChange = (event: SelectChangeEvent<string>) => {
    setSelectedBiomarker(event.target.value);
  };

  // Handle category change
  const handleCategoryChange = (event: SelectChangeEvent<string>) => {
    const category = event.target.value;
    setSelectedCategory(category);

    // Update biomarker names based on selected category
    const filteredNames = Object.entries(timeSeriesData)
      .filter(([_, data]) => category === 'All' || data.categories.includes(category))
      .map(([name]) => name);

    setBiomarkerNames(filteredNames);

    // Update selected biomarker if current selection is not in filtered list
    if (filteredNames.length > 0 && !filteredNames.includes(selectedBiomarker)) {
      setSelectedBiomarker(filteredNames[0]);
    } else if (filteredNames.length === 0) {
      setSelectedBiomarker(''); // Clear selection if no biomarkers match
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
          <Skeleton variant="rectangular" height={60} sx={{ mb: 3 }} />
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
                  {biomarkerNames.map((biomarkerName) => (
                    <MenuItem key={biomarkerName} value={biomarkerName}>
                      {biomarkerName}
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
                {biomarkerNames.length > 0 ? 'Select a biomarker to view its trend.' : 'No biomarkers match the selected category.'}
              </Typography>
            ) : (
              <Plot
                data={[
                  // Line for biomarker values
                  {
                    x: biomarkerData.dates,
                    y: biomarkerData.values,
                    type: 'scatter' as PlotType,
                    mode: 'lines+markers' as Plotly.ScatterData['mode'], // Cast mode
                    marker: { color: '#6200ee' },
                    name: selectedBiomarker
                  },
                  // Reference range - upper line (if available)
                  ...(biomarkerData.referenceRange.max !== null ? [{
                    x: biomarkerData.dates,
                    y: Array(biomarkerData.dates.length).fill(biomarkerData.referenceRange.max),
                    type: 'scatter' as PlotType,
                    mode: 'lines' as Plotly.ScatterData['mode'],
                    line: { dash: 'dash' as Dash, color: 'red' }, // Cast dash
                    name: 'Upper Limit'
                  }] : []),
                  // Reference range - lower line (if available)
                  ...(biomarkerData.referenceRange.min !== null ? [{
                    x: biomarkerData.dates,
                    y: Array(biomarkerData.dates.length).fill(biomarkerData.referenceRange.min),
                    type: 'scatter' as PlotType,
                    mode: 'lines' as Plotly.ScatterData['mode'],
                    line: { dash: 'dash' as Dash, color: 'green' }, // Cast dash
                    name: 'Lower Limit'
                  }] : [])
                ]}
                layout={{
                  title: `${selectedBiomarker} Trend Over Time`,
                  xaxis: { title: 'Date' },
                  yaxis: {
                    title: `${selectedBiomarker} (${biomarkerData.units})`,
                    // Adjust range calculation to handle potential empty values array or non-numeric values
                    range: biomarkerData.values.length > 0 ? [
                      Math.min(
                        biomarkerData.referenceRange.min ?? Infinity, // Use Infinity if min is null
                        ...biomarkerData.values.filter(v => typeof v === 'number') // Filter non-numeric values
                      ) * 0.9, // Add padding
                      Math.max(
                        biomarkerData.referenceRange.max ?? -Infinity, // Use -Infinity if max is null
                        ...biomarkerData.values.filter(v => typeof v === 'number') // Filter non-numeric values
                      ) * 1.1 // Add padding
                    ] : undefined // Default range if no values
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
                    <strong>Status:</strong>{' '}
                    {biomarkerData.referenceRange.max !== null && biomarkerData.values[biomarkerData.values.length - 1] > biomarkerData.referenceRange.max ? (
                      <span style={{ color: 'red' }}>Above Reference Range</span>
                    ) : biomarkerData.referenceRange.min !== null && biomarkerData.values[biomarkerData.values.length - 1] < biomarkerData.referenceRange.min ? (
                      <span style={{ color: 'orange' }}>Below Reference Range</span>
                    ) : (
                      <span style={{ color: 'green' }}>Within Reference Range</span>
                    )}
                  </Typography>
                  <Typography variant="body1">
                    <strong>Trend:</strong>{' '}
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
