import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  Paper, 
  Box, 
  Tabs, 
  Tab, 
  Button, 
  CircularProgress, 
  Grid,
  Breadcrumbs,
  Link,
  Chip,
  Divider,
  Alert
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { getAllBiomarkers, getBiomarkersByFileId, getBiomarkerCategories } from '../services/api';
import BiomarkerTable from '../components/BiomarkerTable';
import { Biomarker } from '../components/BiomarkerTable';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`biomarker-tabpanel-${index}`}
      aria-labelledby={`biomarker-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ py: 3 }}>{children}</Box>}
    </div>
  );
}

const BiomarkerPage: React.FC = () => {
  const { fileId } = useParams<{ fileId: string }>();
  const navigate = useNavigate();
  
  const [tabValue, setTabValue] = useState(0);
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<{
    lab_name?: string;
    report_date?: string;
    filename?: string;
  }>({});
  
  // Fetch biomarkers on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        let biomarkersData: Biomarker[];
        
        // Get biomarkers for specific file or all biomarkers
        if (fileId) {
          biomarkersData = await getBiomarkersByFileId(fileId);
          // Set metadata if available (from first biomarker's PDF)
          if (biomarkersData.length > 0) {
            // Here we would fetch metadata for the file
            // This is simplified and would be replaced with actual API call
            setMetadata({
              lab_name: "Lab Provider", // Placeholder
              report_date: "2023-01-01", // Placeholder
              filename: "lab_report.pdf" // Placeholder
            });
          }
        } else {
          // Get all biomarkers with optional category filter
          biomarkersData = await getAllBiomarkers({
            category: selectedCategory || undefined
          });
        }
        
        setBiomarkers(biomarkersData);
        
        // Fetch available categories
        const categoriesData = await getBiomarkerCategories();
        setCategories(categoriesData);
      } catch (err) {
        console.error('Error fetching biomarkers:', err);
        setError('Failed to load biomarker data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [fileId, selectedCategory]);
  
  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  // Handle category selection
  const handleCategoryClick = (category: string) => {
    setSelectedCategory(selectedCategory === category ? null : category);
  };
  
  // Handle back navigation
  const handleBack = () => {
    navigate(-1);
  };
  
  // Handle upload new PDF
  const handleUploadNew = () => {
    navigate('/upload');
  };
  
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Breadcrumbs navigation */}
      <Breadcrumbs 
        separator={<NavigateNextIcon fontSize="small" />} 
        aria-label="breadcrumb"
        sx={{ mb: 3 }}
      >
        <Link color="inherit" href="/" onClick={(e) => { e.preventDefault(); navigate('/'); }}>
          Home
        </Link>
        {fileId ? (
          <>
            <Link 
              color="inherit" 
              href="/biomarkers" 
              onClick={(e) => { e.preventDefault(); navigate('/biomarkers'); }}
            >
              Biomarkers
            </Link>
            <Typography color="text.primary">Report Results</Typography>
          </>
        ) : (
          <Typography color="text.primary">Biomarkers</Typography>
        )}
      </Breadcrumbs>
      
      {/* Header section */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            {fileId ? 'Lab Report Results' : 'Biomarker Dashboard'}
          </Typography>
          {fileId && metadata.lab_name && (
            <Typography variant="subtitle1" color="text.secondary">
              {metadata.lab_name} {metadata.report_date ? `• ${metadata.report_date}` : ''}
            </Typography>
          )}
        </Box>
        
        <Box>
          <Button
            variant="outlined"
            startIcon={<ArrowBackIcon />}
            onClick={handleBack}
            sx={{ mr: 2 }}
          >
            Back
          </Button>
          
          <Button
            variant="contained"
            startIcon={<UploadFileIcon />}
            onClick={handleUploadNew}
          >
            Upload New Report
          </Button>
        </Box>
      </Box>
      
      {/* Main content */}
      <Paper sx={{ mb: 4 }}>
        {/* Tabs for different views */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="biomarker tabs">
            <Tab label="All Biomarkers" id="biomarker-tab-0" aria-controls="biomarker-tabpanel-0" />
            {fileId && <Tab label="Abnormal Values" id="biomarker-tab-1" aria-controls="biomarker-tabpanel-1" />}
            <Tab label="By Category" id="biomarker-tab-2" aria-controls="biomarker-tabpanel-2" />
          </Tabs>
        </Box>
        
        {/* All biomarkers tab */}
        <TabPanel value={tabValue} index={0}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <BiomarkerTable 
              biomarkers={biomarkers} 
              error={error}
            />
          )}
        </TabPanel>
        
        {/* Abnormal values tab - only available for specific file */}
        {fileId && (
          <TabPanel value={tabValue} index={1}>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                <CircularProgress />
              </Box>
            ) : (
              <BiomarkerTable 
                biomarkers={biomarkers.filter(b => b.is_abnormal)} 
                error={error}
              />
            )}
          </TabPanel>
        )}
        
        {/* By category tab */}
        <TabPanel value={tabValue} index={fileId ? 2 : 1}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <Box>
              <Box sx={{ mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Filter by Category
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {categories.map((category) => (
                    <Chip
                      key={category}
                      label={category}
                      onClick={() => handleCategoryClick(category)}
                      color={selectedCategory === category ? 'primary' : 'default'}
                      variant={selectedCategory === category ? 'filled' : 'outlined'}
                    />
                  ))}
                </Box>
              </Box>
              
              <Divider sx={{ my: 3 }} />
              
              {selectedCategory ? (
                <BiomarkerTable 
                  biomarkers={biomarkers} 
                  error={error}
                />
              ) : (
                <Alert severity="info">
                  Select a category to view biomarkers
                </Alert>
              )}
            </Box>
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default BiomarkerPage; 