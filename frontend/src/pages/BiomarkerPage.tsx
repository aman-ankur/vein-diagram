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
  Alert,
  useTheme
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { getAllBiomarkers, getBiomarkersByFileId, getBiomarkerCategories, getBiomarkerExplanation } from '../services/api';
import BiomarkerTable from '../components/BiomarkerTable';
import BiomarkerVisualization from '../components/BiomarkerVisualization';
import ExplanationModal from '../components/ExplanationModal';
import { Biomarker } from '../components/BiomarkerTable';
import { BiomarkerExplanation } from '../components/ExplanationModal';

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
  const theme = useTheme();
  
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
  
  // State for AI explanation modal
  const [explanationModalOpen, setExplanationModalOpen] = useState<boolean>(false);
  const [currentBiomarker, setCurrentBiomarker] = useState<Biomarker | null>(null);
  const [explanationLoading, setExplanationLoading] = useState<boolean>(false);
  const [explanationError, setExplanationError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<BiomarkerExplanation | null>(null);
  
  // This is a dummy function just for testing - will be replaced with actual history feature
  const onViewHistory = (biomarker: Biomarker) => {
    console.log('View history for biomarker:', biomarker);
    // In a real implementation, this would show a history view
  };
  
  // Fetch biomarkers on component mount
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        let biomarkersData: Biomarker[];
        
        if (fileId) {
          // Fetch biomarkers for the specific file
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
        
        setBiomarkers(uniqueBiomarkers);
        
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
    setCurrentBiomarker(biomarker);
    setExplanationModalOpen(true);
    setExplanationLoading(true);
    setExplanationError(null);
    setExplanation(null);
    
    try {
      const isAbnormal = biomarker.isAbnormal !== undefined 
        ? biomarker.isAbnormal 
        : (biomarker.reference_range_low !== undefined && biomarker.reference_range_high !== undefined)
          ? (biomarker.value < biomarker.reference_range_low || biomarker.value > biomarker.reference_range_high)
          : false;
      
      const referenceRange = biomarker.referenceRange || 
        (biomarker.reference_range_low !== null && biomarker.reference_range_high !== null 
          ? `${biomarker.reference_range_low}-${biomarker.reference_range_high}` 
          : "Not available");
      
      console.log('Calculated parameters:');
      console.log('- isAbnormal:', isAbnormal);
      console.log('- referenceRange:', referenceRange);
      
      console.log('Calling API with parameters:', {
        id: biomarker.id,
        name: biomarker.name,
        value: biomarker.value,
        unit: biomarker.unit,
        referenceRange,
        isAbnormal
      });
      
      const result = await getBiomarkerExplanation(
        biomarker.id,
        biomarker.name,
        biomarker.value,
        biomarker.unit,
        referenceRange,
        isAbnormal
      );
      
      console.log('Received explanation result:', result);
      setExplanation(result);
    } catch (error) {
      console.error('=== ERROR IN EXPLAIN BIOMARKER HANDLER ===');
      console.error('Error type:', typeof error);
      console.error('Full error details:', error);
      
      setExplanationError(
        error instanceof Error 
          ? error.message 
          : typeof error === 'object' && error !== null && 'message' in error
            ? String(error.message)
            : 'An unexpected error occurred'
      );
      
      console.error('Set error message to:', explanationError);
    } finally {
      setExplanationLoading(false);
      console.log('Explanation loading set to false');
    }
  };
  
  // Handle closing the explanation modal
  const handleCloseExplanationModal = () => {
    setExplanationModalOpen(false);
  };
  
  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
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
            <Tab label="Visualizations" id="biomarker-tab-3" aria-controls="biomarker-tabpanel-3" />
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
              onExplainWithAI={handleExplainBiomarker}
              onViewHistory={onViewHistory}
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
                biomarkers={biomarkers.filter(b => b.isAbnormal)} 
                error={error}
                onExplainWithAI={handleExplainBiomarker}
                onViewHistory={onViewHistory}
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
                <Typography 
                  variant="h6" 
                  gutterBottom
                  sx={{ 
                    color: theme.palette.mode === 'dark' 
                      ? theme.palette.grey[100] 
                      : theme.palette.grey[900] 
                  }}
                >
                  Filter by Category
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {categories.map((category) => (
                    <Chip
                      key={category}
                      label={category}
                      onClick={() => handleCategoryClick(category)}
                      sx={{
                        backgroundColor: selectedCategory === category
                          ? theme.palette.mode === 'dark'
                            ? theme.palette.primary.dark
                            : theme.palette.primary.main
                          : theme.palette.mode === 'dark'
                            ? 'rgba(255, 255, 255, 0.16)'
                            : 'rgba(0, 0, 0, 0.08)',
                        color: selectedCategory === category
                          ? '#fff'
                          : theme.palette.mode === 'dark'
                            ? theme.palette.primary.light
                            : theme.palette.primary.main,
                        '&:hover': {
                          backgroundColor: selectedCategory === category
                            ? theme.palette.mode === 'dark'
                              ? theme.palette.primary.main
                              : theme.palette.primary.dark
                            : theme.palette.mode === 'dark'
                              ? 'rgba(255, 255, 255, 0.24)'
                              : 'rgba(0, 0, 0, 0.12)'
                        }
                      }}
                    />
                  ))}
                </Box>
              </Box>
              
              <Divider sx={{ my: 3 }} />
              
              {selectedCategory ? (
                <BiomarkerTable 
                  biomarkers={biomarkers} 
                  error={error}
                  onExplainWithAI={handleExplainBiomarker}
                  onViewHistory={onViewHistory}
                />
              ) : (
                <Alert severity="info">
                  Select a category to view biomarkers
                </Alert>
              )}
            </Box>
          )}
        </TabPanel>

        {/* Visualizations tab */}
        <TabPanel value={tabValue} index={fileId ? 3 : 2}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <BiomarkerVisualization 
              biomarkers={biomarkers} 
              error={error}
              onExplainWithAI={handleExplainBiomarker}
            />
          )}
        </TabPanel>
      </Paper>
      
      {/* AI Explanation Modal */}
      {currentBiomarker && (
        <ExplanationModal
          open={explanationModalOpen}
          onClose={handleCloseExplanationModal}
          biomarkerName={currentBiomarker.name}
          biomarkerValue={currentBiomarker.value}
          biomarkerUnit={currentBiomarker.unit}
          referenceRange={currentBiomarker.referenceRange || 
            (currentBiomarker.reference_range_low !== null && currentBiomarker.reference_range_high !== null 
              ? `${currentBiomarker.reference_range_low}-${currentBiomarker.reference_range_high}` 
              : "Not available")}
          isLoading={explanationLoading}
          error={explanationError}
          explanation={explanation}
        />
      )}
    </Container>
  );
};

export default BiomarkerPage; 