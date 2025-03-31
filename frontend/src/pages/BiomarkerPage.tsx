import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
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
  AlertTitle,
  useTheme,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import HistoryIcon from '@mui/icons-material/History';
import { getAllBiomarkers, getBiomarkersByFileId, getBiomarkerCategories, getBiomarkerExplanation, getPDFStatus, PDFProcessingStatus } from '../services/api';
import { getAllProfiles } from '../services/profileService';
import BiomarkerTable from '../components/BiomarkerTable';
import BiomarkerVisualization from '../components/BiomarkerVisualization';
import ExplanationModal from '../components/ExplanationModal';
import ViewToggle from '../components/ViewToggle';
import type { Biomarker } from '../types/biomarker';
import { BiomarkerExplanation } from '../types/api';
import { UserProfile } from '../types/Profile';

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
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const theme = useTheme();
  
  // Get the view param from URL or default to 'current'
  const viewParam = searchParams.get('view');
  
  const [tabValue, setTabValue] = useState(0);
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentView, setCurrentView] = useState<'current' | 'history'>(
    viewParam === 'history' ? 'history' : 'current'
  );
  const [profileId, setProfileId] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<{
    lab_name?: string;
    report_date?: string;
    filename?: string;
    profile_name?: string;
  }>({});
  
  // State for AI explanation modal
  const [explanationModalOpen, setExplanationModalOpen] = useState<boolean>(false);
  const [currentBiomarker, setCurrentBiomarker] = useState<Biomarker | null>(null);
  const [explanationLoading, setExplanationLoading] = useState<boolean>(false);
  const [explanationError, setExplanationError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<BiomarkerExplanation | null>(null);
  
  const [profiles, setProfiles] = useState<UserProfile[]>([]);
  const [profilesLoading, setProfilesLoading] = useState(false);
  
  // This is a dummy function just for testing - will be replaced with actual history feature
  const onViewHistory = (biomarker: Biomarker) => {
    console.log('View history for biomarker:', biomarker);
    // In a real implementation, this would show a history view
  };
  
  // Handle view toggle change
  const handleViewChange = (view: 'current' | 'history') => {
    setCurrentView(view);
    
    // Update the URL to reflect the current view
    if (view === 'current') {
      searchParams.delete('view');
    } else {
      searchParams.set('view', view);
    }
    setSearchParams(searchParams);
  };
  
  // Fetch biomarkers on component mount or when dependencies change
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        let biomarkersData: Biomarker[];
        let extractedProfileId = profileId; // Start with current profileId if exists
        
        // Check if we have profile_id in URL params for direct history view
        const profileIdParam = searchParams.get('profile_id');
        if (profileIdParam && !extractedProfileId) {
          console.log(`Found profile_id in URL params: ${profileIdParam}`);
          extractedProfileId = profileIdParam;
          setProfileId(profileIdParam);
        }
        
        if (fileId) {
          // First, get the PDF status to check if it has a profile association
          try {
            console.log(`Checking PDF status for file ${fileId} to get profile association`);
            const pdfStatus = await getPDFStatus(fileId);
            
            // Log the full PDF status for debugging
            console.log('PDF status full response:', pdfStatus);
            
            if (pdfStatus && pdfStatus.profileId) {
              extractedProfileId = pdfStatus.profileId;
              console.log(`Found profile ID from PDF status: ${extractedProfileId}`);
              setProfileId(extractedProfileId);
              
              // Update metadata
              setMetadata({
                lab_name: pdfStatus.lab_name || "Lab Provider",
                report_date: pdfStatus.processed_date || new Date().toISOString().split('T')[0],
                filename: pdfStatus.filename || "lab_report.pdf",
                profile_name: pdfStatus.profile_name || "Patient Profile"
              });
            } else {
              console.log("No profile association found in PDF status");
            }
          } catch (statusError) {
            console.error("Error fetching PDF status:", statusError);
            console.error("Status error details:", JSON.stringify(statusError, null, 2));
          }
          
          // For a specific file, behavior depends on current view mode
          if (currentView === 'current') {
            // Current PDF view - Get biomarkers just for this file
            // Pass the profileId if we have one, which helps to maintain consistency
            console.log(`Fetching biomarkers for file ${fileId} with profileId ${extractedProfileId || 'undefined'}`);
            biomarkersData = await getBiomarkersByFileId(fileId, extractedProfileId || undefined);
            
            // If we still don't have a profile ID, try to extract it from biomarker data
            if (!extractedProfileId && biomarkersData.length > 0) {
              const possibleProfileId = biomarkersData[0].profileId;
              if (possibleProfileId) {
                console.log(`Found profile ID from biomarker: ${possibleProfileId}`);
                extractedProfileId = possibleProfileId;
                setProfileId(possibleProfileId);
              }
            }
          } else {
            // History view - Get all biomarkers for the profile associated with this file
            if (extractedProfileId) {
              console.log(`Fetching all biomarkers for profile ${extractedProfileId} (history view)`);
              biomarkersData = await getAllBiomarkers({
                profile_id: extractedProfileId,
                category: selectedCategory || undefined
              });
            } else {
              // No profile ID available, fall back to current file biomarkers
              console.warn("No profile ID found, falling back to current file biomarkers");
              biomarkersData = await getBiomarkersByFileId(fileId);
              setCurrentView('current');
            }
          }
        } else {
          // No fileId
          if (currentView === 'history' && extractedProfileId) {
            // History view with a profile ID - Get all biomarkers for this profile
            console.log(`Fetching all biomarkers for profile ${extractedProfileId} (history view without fileId)`);
            biomarkersData = await getAllBiomarkers({
              profile_id: extractedProfileId,
              category: selectedCategory || undefined
            });
          } else {
            // Default view - get all biomarkers with optional category filter
            console.log('Fetching all biomarkers (no profile or file filter)');
            biomarkersData = await getAllBiomarkers({
              category: selectedCategory || undefined
            });
          }
        }
        
        // Deduplicate biomarkers
        const uniqueBiomarkers: Biomarker[] = [];
        const uniqueKeys = new Set<string>();
        
        biomarkersData.forEach(biomarker => {
          // Check for profile ID again
          if (biomarker.profileId && !extractedProfileId) {
            console.log(`Found profile ID in biomarker response: ${biomarker.profileId}`);
            extractedProfileId = biomarker.profileId;
            setProfileId(biomarker.profileId);
          }
          
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
  }, [fileId, selectedCategory, currentView, profileId, searchParams]);
  
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
    console.log('Function reference:', handleExplainBiomarker);
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
      // Calculate the abnormal status
      const isAbnormal = biomarker.isAbnormal !== undefined 
        ? biomarker.isAbnormal 
        : (biomarker.reference_range_low !== undefined && biomarker.reference_range_high !== undefined)
          ? (biomarker.value < biomarker.reference_range_low || biomarker.value > biomarker.reference_range_high)
          : false;
      
      // Format reference range
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
      console.error('Error type:', typeof error);
      console.error('Full error details:', error);
      
      // Set user-friendly error message
      let errorMessage = 'An unexpected error occurred. Please try again later.';
      
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'object' && error !== null && 'message' in error) {
        errorMessage = String(error.message);
      }
      
      console.log('Setting error message:', errorMessage);
      setExplanationError(errorMessage);
      
      // Keep the modal open to show the error
    } finally {
      // Always set loading to false
      setExplanationLoading(false);
      console.log('Explanation loading set to false');
    }
  };
  
  // Handle closing the explanation modal
  const handleCloseExplanationModal = () => {
    setExplanationModalOpen(false);
  };
  
  // Add this after your other useEffect hooks
  useEffect(() => {
    // Fetch available profiles for the profile selector
    const fetchProfiles = async () => {
      try {
        setProfilesLoading(true);
        const profilesData = await getAllProfiles();
        setProfiles(profilesData);
      } catch (err) {
        console.error('Error fetching profiles:', err);
      } finally {
        setProfilesLoading(false);
      }
    };
    
    fetchProfiles();
  }, []);
  
  // Handle profile selection for history view
  const handleProfileSelect = (event: SelectChangeEvent<string>) => {
    const selectedProfileId = event.target.value;
    if (selectedProfileId) {
      setProfileId(selectedProfileId);
      setCurrentView('history');
      
      // Update URL params
      searchParams.set('profile_id', selectedProfileId);
      searchParams.set('view', 'history');
      setSearchParams(searchParams);
    }
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
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            {fileId ? 'Lab Report Results' : 'Biomarker Dashboard'}
          </Typography>
          {fileId && metadata.lab_name && (
            <Typography variant="subtitle1" color="text.secondary">
              {metadata.lab_name} {metadata.report_date ? `• ${metadata.report_date}` : ''}
              {metadata.profile_name ? ` • ${metadata.profile_name}` : ''}
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
      
      {/* View toggle - show on both overview and specific file pages */}
      <Box sx={{ mb: 4 }}>
        <Paper elevation={2} sx={{ p: 2, borderRadius: 2 }}>
          <Typography variant="h6" gutterBottom>
            View Options
          </Typography>
          
          <ViewToggle 
            currentView={currentView} 
            onViewChange={handleViewChange}
            disabled={!profileId}
            disabledText={profileId ? undefined : "Please associate a PDF with a profile to enable history view"}
          />
          
          {!fileId && (
            <Box sx={{ mt: 2, p: 1, borderTop: 1, borderColor: 'divider' }}>
              <Typography variant="subtitle2" gutterBottom>
                Select a profile to view history:
              </Typography>
              <FormControl fullWidth sx={{ mt: 1 }}>
                <InputLabel id="profile-select-label">Profile</InputLabel>
                <Select
                  labelId="profile-select-label"
                  id="profile-select"
                  value={profileId || ''}
                  label="Profile"
                  onChange={handleProfileSelect}
                  disabled={profilesLoading}
                >
                  <MenuItem value="">
                    <em>Select a profile</em>
                  </MenuItem>
                  {profiles.map((profile) => (
                    <MenuItem key={profile.id} value={profile.id}>
                      {profile.name} {profile.date_of_birth ? `(DOB: ${new Date(profile.date_of_birth).toLocaleDateString()})` : ''}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Box>
          )}
          
          {!profileId && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <AlertTitle>No Profile Selected</AlertTitle>
              {fileId 
                ? "This PDF is not associated with a profile. To enable the history view, please associate this PDF with a profile."
                : "Please select a profile or upload a PDF associated with a profile to view history."
              }
            </Alert>
          )}
          
          {profileId && currentView === 'history' && (
            <Alert severity="info" sx={{ mt: 2 }}>
              <AlertTitle>History View</AlertTitle>
              You are viewing all biomarkers from all reports associated with this profile.
              The Source column shows which report each biomarker came from.
            </Alert>
          )}
        </Paper>
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
              showSource={currentView === 'history'}
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
                showSource={currentView === 'history'}
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
                  showSource={currentView === 'history'}
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
              showSource={currentView === 'history'}
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