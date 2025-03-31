import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Paper, 
  Grid, 
  CircularProgress, 
  Tabs, 
  Tab,
  Alert,
  Button,
  useTheme,
  Tooltip, // Import Tooltip
  IconButton 
} from '@mui/material';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom'; // Import Link
import BarChartIcon from '@mui/icons-material/BarChart';
import TableChartIcon from '@mui/icons-material/TableChart';
import HistoryIcon from '@mui/icons-material/History'; // Import HistoryIcon
import TimelineIcon from '@mui/icons-material/Timeline';
import CategoryIcon from '@mui/icons-material/Category';
import SummarizeIcon from '@mui/icons-material/Summarize';
import RefreshIcon from '@mui/icons-material/Refresh';

import { getBiomarkersByFileId, getAllBiomarkers, getBiomarkerExplanation } from '../services/api';
import { Biomarker } from '../types/pdf';
import BiomarkerTable from '../components/BiomarkerTable';
import ExplanationModal from '../components/ExplanationModal';
import type { BiomarkerExplanation } from '../types/api';
import { useProfile } from '../contexts/ProfileContext';

// Define interface for TabPanel props
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// TabPanel component for tabbed content
const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`visualization-tabpanel-${index}`}
      aria-labelledby={`visualization-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

const VisualizationPage: React.FC = () => {
  const navigate = useNavigate();
  const theme = useTheme();
  const location = useLocation();
  
  // Get fileId from query parameter instead of path parameter
  const queryParams = new URLSearchParams(location.search);
  const fileId = queryParams.get('fileId');
  
  const { activeProfile } = useProfile();
  
  // Enhanced console logging for debugging
  useEffect(() => {
    console.log("========== VISUALIZATION PAGE DEBUG ==========");
    console.log("Component mounted with:");
    console.log("fileId from query:", fileId);
    console.log("full URL search:", location.search);
    console.log("activeProfile:", activeProfile ? {
      id: activeProfile.id,
      name: activeProfile.name,
      type: typeof activeProfile.id
    } : "null");
    console.log("==============================================");
  }, [fileId, activeProfile, location.search]);
  
  // State for biomarkers, loading, and error
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [chartType, setChartType] = useState<'bar' | 'line' | 'scatter'>('line');

  // State for AI explanation modal
  const [explanationModalOpen, setExplanationModalOpen] = useState<boolean>(false);
  const [currentBiomarker, setCurrentBiomarker] = useState<Biomarker | null>(null);
  const [explanationLoading, setExplanationLoading] = useState<boolean>(false);
  const [explanationError, setExplanationError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<BiomarkerExplanation | null>(null);

  // Fetch biomarkers on component mount or when activeProfile changes
  useEffect(() => {
    fetchBiomarkers();
  }, [fileId, activeProfile]);

  // Function to fetch biomarkers
  const fetchBiomarkers = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let data: Biomarker[];
      const profileId = activeProfile?.id;
      
      console.log('Fetching biomarkers with profile context:', { 
        fileId, 
        profileId, 
        activeProfile: activeProfile ? {
          id: activeProfile.id,
          name: activeProfile.name,
          idType: typeof activeProfile.id
        } : null 
      });
      
      if (!profileId) {
        console.warn('No active profile found. This may cause data from different profiles to be mixed together.'); // Emoji removed
      } else {
        console.log(`Active profile found: ${profileId} (${activeProfile?.name})`); // Emoji removed
      }
      
      // Force profileId to be a string to prevent type issues
      const profileIdStr = profileId?.toString();
      
      // Log the value we're actually going to send
      console.log(`FINAL PROFILE ID TO SEND: "${profileIdStr}" (${typeof profileIdStr})`); // Emoji removed
      
      if (fileId) {
        try {
          // DIRECT FETCH APPROACH: Bypass the API client completely
          console.log(`DIRECT FETCH: Using fetch API directly to ensure parameters are included`); // Emoji removed
          
          // Build URL with profile_id included directly in the URL as a query parameter
          const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
          const url = `${apiBaseUrl}/api/pdf/${fileId}/biomarkers?profile_id=${encodeURIComponent(profileIdStr || '')}`;
          
          console.log(`Making direct fetch to: ${url}`); // Emoji removed
          
          const response = await fetch(url, {
            method: 'GET',
            headers: {
              'Accept': 'application/json',
            },
            credentials: 'include' // Include cookies
          });
          
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          
          const jsonData = await response.json();
          console.log(`Direct fetch response received with ${jsonData.length} biomarkers`); // Emoji removed
          
          // Use the regular mapping function to keep consistency
          data = jsonData.map((item: any) => ({
            id: item.id,
            name: item.name,
            value: item.value,
            unit: item.unit || '',
            referenceRange: item.reference_range_text || 
                          (item.reference_range_low !== null && item.reference_range_high !== null ? 
                            `${item.reference_range_low}-${item.reference_range_high}` : undefined),
            category: item.category || 'Other',
            isAbnormal: item.is_abnormal || false,
            fileId, // Keep fileId from the URL param
            date: item.created_at || new Date().toISOString(),
            reportDate: item.pdf?.report_date || item.pdf?.uploaded_date || item.created_at || new Date().toISOString()
          }));
        } catch (fetchError) {
          console.error(`Direct fetch failed, falling back to API client:`, fetchError); // Emoji removed
          // Fall back to the regular API client
          console.log(`Calling getBiomarkersByFileId with fileId=${fileId} and profileId=${profileIdStr || 'undefined'}`);
          data = await getBiomarkersByFileId(fileId, profileIdStr);
        }
        
        console.log(`Received ${data.length} biomarkers for file ${fileId}`);
      } else {
        // Fetch all biomarkers with profile filter
        console.log(`Calling getAllBiomarkers with profile_id=${profileIdStr || 'undefined'}`);
        
        data = await getAllBiomarkers({
          profile_id: profileIdStr
        });
        
        console.log(`Received ${data.length} biomarkers in total`);
      }
      
      // Log the first couple of biomarkers to see what we're getting
      if (data.length > 0) {
        console.log('Sample biomarker data:', data.slice(0, 2));
      }
      
      // Deduplicate biomarkers (Consider if this is still needed or if backend handles it)
      const uniqueBiomarkers: Biomarker[] = [];
      const uniqueKeys = new Set<string>();
      
      data.forEach(biomarker => {
        // Use a more robust key if ID is available and unique per instance
        const key = biomarker.id ? biomarker.id.toString() : `${biomarker.name}_${biomarker.value}_${biomarker.unit}_${biomarker.reportDate}`; 
        if (!uniqueKeys.has(key)) {
          uniqueKeys.add(key);
          uniqueBiomarkers.push(biomarker);
        }
      });
      
      console.log(`After deduplication: ${uniqueBiomarkers.length} unique biomarkers`);
      setBiomarkers(uniqueBiomarkers);
    } catch (error) {
      console.error('Error fetching biomarkers:', error);
      setError('Failed to load biomarker data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Handler for tab change
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Handler for retry
  const handleRetry = () => {
    fetchBiomarkers();
  };

  // Handler for chart type change
  const handleChartTypeChange = (type: 'bar' | 'line' | 'scatter') => {
    setChartType(type);
  };

  // Function to handle opening the explanation modal
  const handleExplainBiomarker = async (biomarker: Biomarker) => {
    console.log('=== EXPLAIN BIOMARKER FUNCTION CALLED ===');
    console.log('Biomarker data received:', biomarker);
    
    // Make sure biomarker has expected fields
    if (!biomarker || !biomarker.name) {
      console.error('Invalid biomarker data received:', biomarker);
      setExplanationError('Cannot explain this biomarker: invalid data');
      return;
    }
    
    console.log('Opening explanation modal for biomarker:', biomarker);
    
    // First open the modal with loading state
    setCurrentBiomarker(biomarker);
    setExplanationModalOpen(true);
    setExplanationLoading(true);
    setExplanationError(null);
    setExplanation(null);
    
    try {
      // Calculate the abnormal status safely
      const isAbnormal = biomarker.isAbnormal !== undefined
        ? biomarker.isAbnormal
        : (typeof biomarker.value === 'number' && typeof biomarker.reference_range_low === 'number' && typeof biomarker.reference_range_high === 'number')
          ? (biomarker.value < biomarker.reference_range_low || biomarker.value > biomarker.reference_range_high)
          : false; // Default to false if types don't match or ranges are null/undefined

      // Format reference range safely
      const referenceRange = biomarker.referenceRange ?? // Use nullish coalescing
        (typeof biomarker.reference_range_low === 'number' && typeof biomarker.reference_range_high === 'number'
          ? `${biomarker.reference_range_low}-${biomarker.reference_range_high}`
          : "Not available");
      
      console.log('Calculated parameters:');
      console.log('- isAbnormal:', isAbnormal);
      console.log('- referenceRange:', referenceRange);
      
      // Make API call
      const result = await getBiomarkerExplanation(
        biomarker.id,
        biomarker.name,
        biomarker.value,
        biomarker.unit,
        referenceRange,
        isAbnormal
      );
      
      console.log('Received explanation result:', result);
      
      // Verify result structure
      if (!result || !result.general_explanation || !result.specific_explanation) {
        console.error('Invalid explanation data received:', result);
        setExplanationError('Invalid explanation data received. Please try again.');
        return;
      }
      
      // Update state with result
      setExplanation(result);
    } catch (error) {
      console.error('=== ERROR IN EXPLAIN BIOMARKER HANDLER ===');
      console.error('Error details:', error);
      
      // Set user-friendly error message
      let errorMessage = 'An unexpected error occurred. Please try again later.';
      
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'object' && error !== null && 'message' in error) {
        errorMessage = String(error.message);
      }
      
      console.log('Setting error message:', errorMessage);
      setExplanationError(errorMessage);
    } finally {
      // Always set loading to false
      setExplanationLoading(false);
    }
  };
  
  // Handle closing the explanation modal
  const handleCloseExplanationModal = () => {
    setExplanationModalOpen(false);
  };

  // Render loading state
  if (loading) {
    return (
      <Container maxWidth="lg">
        <Box sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center',
          minHeight: '50vh',
          py: 4 
        }}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Loading biomarker data...
          </Typography>
        </Box>
      </Container>
    );
  }

  // Render error state
  if (error) {
    return (
      <Container maxWidth="lg">
        <Paper sx={{ p: 3, mt: 3 }}>
          <Alert 
            severity="error" 
            action={
              <Button color="inherit" size="small" onClick={handleRetry}>
                <RefreshIcon sx={{ mr: 1 }} />
                Retry
              </Button>
            }
          >
            {error}
          </Alert>
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button 
              variant="contained" 
              onClick={() => navigate('/upload')}
            >
              Upload New File
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  // If no biomarkers found
  if (biomarkers.length === 0) {
    return (
      <Container maxWidth="lg">
        <Paper sx={{ p: 3, mt: 3 }}>
          <Alert severity="info">
            No biomarker data available. Please upload a lab report to get started.
          </Alert>
          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Button 
              variant="contained" 
              onClick={() => navigate('/upload')}
            >
              Upload Lab Report
            </Button>
          </Box>
        </Paper>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mt: 3, mb: 4, display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}> {/* Added flex styles */}
        <Box sx={{ flexGrow: 1 }}> {/* Allow title/text to grow */}
          <Typography variant="h4" component="h1" gutterBottom>
            {fileId ? 'File Analysis' : 'Biomarker Overview'}
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {fileId 
              ? 'View and analyze biomarkers extracted from your uploaded file'
              : 'View all biomarkers across your uploaded lab reports'
            }
          </Typography>
        </Box>
        {/* History Button */}
        {activeProfile && (
          <Tooltip title={`View the complete biomarker history for profile: ${activeProfile.name}`}>
            <Button
              component={Link}
              to={`/profile/${activeProfile.id}/history`}
              variant="outlined"
              startIcon={<HistoryIcon />}
              sx={{ ml: 2, mt: { xs: 1, sm: 0 } }} // Add margin top on small screens
            >
              View Biomarker History
            </Button>
          </Tooltip>
        )}
      </Box>

      {/* PDF Metadata Section (only when viewing a specific file) */}
      {fileId && (
        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Document Information
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary">
                File ID
              </Typography>
              <Typography variant="body1">
                {fileId}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary">
                Biomarkers Found
              </Typography>
              <Typography variant="body1">
                {biomarkers.length}
              </Typography>
            </Grid>
            <Grid item xs={12} md={4}>
              <Typography variant="body2" color="text.secondary">
                Processed On
              </Typography>
              <Typography variant="body1">
                {/* Use a consistent date format if available, otherwise fallback */}
                {biomarkers[0]?.reportDate ? new Date(biomarkers[0].reportDate).toLocaleDateString() : 'N/A'}
              </Typography>
            </Grid>
          </Grid>
        </Paper>
      )}

      {/* Chart Controls */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange} 
          aria-label="biomarker visualization tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<TableChartIcon />} label="Table View" />
          <Tab icon={<TimelineIcon />} label="Chart View" />
          <Tab icon={<CategoryIcon />} label="Categories" />
          <Tab icon={<SummarizeIcon />} label="Summary" />
        </Tabs>
      </Box>

      {/* Table View */}
      <TabPanel value={activeTab} index={0}>
        <BiomarkerTable 
          biomarkers={biomarkers} 
          onExplainWithAI={handleExplainBiomarker}
          // Pass other necessary props like isLoading, error, onRefresh if needed by table
        />
      </TabPanel>

      {/* Chart View */}
      <TabPanel value={activeTab} index={1}>
        <Paper sx={{ p: 3 }}>
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Biomarker Visualization
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant={chartType === 'line' ? 'contained' : 'outlined'}
                onClick={() => handleChartTypeChange('line')}
                startIcon={<TimelineIcon />}
              >
                Line
              </Button>
              <Button
                variant={chartType === 'bar' ? 'contained' : 'outlined'}
                onClick={() => handleChartTypeChange('bar')}
                startIcon={<BarChartIcon />}
              >
                Bar
              </Button>
              <Button
                variant={chartType === 'scatter' ? 'contained' : 'outlined'}
                onClick={() => handleChartTypeChange('scatter')}
                startIcon={<TimelineIcon />}
              >
                Scatter
              </Button>
            </Box>
          </Box>
          
          <Box sx={{ height: '400px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography variant="body1" color="text.secondary">
              Chart visualization will be implemented here
            </Typography>
          </Box>
        </Paper>
      </TabPanel>

      {/* Categories View */}
      <TabPanel value={activeTab} index={2}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Biomarkers by Category
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Category view will be implemented here
          </Typography>
        </Paper>
      </TabPanel>

      {/* Summary View */}
      <TabPanel value={activeTab} index={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Biomarker Summary
          </Typography>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 2, 
                  bgcolor: theme.palette.background.default,
                  border: `1px solid ${theme.palette.divider}`
                }}
              >
                <Typography variant="subtitle1" gutterBottom>
                  Abnormal Values
                </Typography>
                <Typography variant="h4" color="error.main">
                  {biomarkers.filter(b => b.isAbnormal).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  out of {biomarkers.length} total biomarkers
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper 
                elevation={0} 
                sx={{ 
                  p: 2, 
                  bgcolor: theme.palette.background.default,
                  border: `1px solid ${theme.palette.divider}`
                }}
              >
                <Typography variant="subtitle1" gutterBottom>
                  Categories
                </Typography>
                <Typography variant="h4">
                  {new Set(biomarkers.map(b => b.category)).size}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  different categories of biomarkers
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Paper>
      </TabPanel>

      {/* AI Explanation Modal - Temporarily commented out due to persistent syntax error */}
      {/* {currentBiomarker && (
        <ExplanationModal
          open={explanationModalOpen}
          onClose={handleCloseExplanationModal}
          biomarkerName={currentBiomarker.name}
          biomarkerValue={currentBiomarker.value}
          biomarkerUnit={currentBiomarker.unit}
          referenceRange={
            currentBiomarker.referenceRange ?? 
            (typeof currentBiomarker.reference_range_low === 'number' && typeof currentBiomarker.reference_range_high === 'number'
              ? `${currentBiomarker.reference_range_low}-${currentBiomarker.reference_range_high}`
              : "Not available")
          }
          isLoading={explanationLoading}
          error={explanationError}
          explanation={explanation}
        />
      )} */}
    </Container>
  );
};

export default VisualizationPage;
