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
  useTheme
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import BarChartIcon from '@mui/icons-material/BarChart';
import TableChartIcon from '@mui/icons-material/TableChart';
import TimelineIcon from '@mui/icons-material/Timeline';
import CategoryIcon from '@mui/icons-material/Category';
import SummarizeIcon from '@mui/icons-material/Summarize';
import RefreshIcon from '@mui/icons-material/Refresh';

import { getBiomarkersByFileId, getAllBiomarkers } from '../services/api';
import { Biomarker } from '../types/pdf';
import BiomarkerTable from '../components/BiomarkerTable';

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
  const { fileId } = useParams<{ fileId?: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  
  // State for biomarkers, loading, and error
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [chartType, setChartType] = useState<'bar' | 'line' | 'scatter'>('line');

  // Fetch biomarkers on component mount
  useEffect(() => {
    fetchBiomarkers();
  }, [fileId]);

  // Function to fetch biomarkers
  const fetchBiomarkers = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let data: Biomarker[];
      
      if (fileId) {
        // Fetch biomarkers for specific file
        data = await getBiomarkersByFileId(fileId);
      } else {
        // Fetch all biomarkers
        data = await getAllBiomarkers();
      }
      
      setBiomarkers(data);
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
      <Box sx={{ mt: 3, mb: 4 }}>
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
                {new Date().toLocaleDateString()}
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
        <BiomarkerTable biomarkers={biomarkers} />
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
    </Container>
  );
};

export default VisualizationPage; 