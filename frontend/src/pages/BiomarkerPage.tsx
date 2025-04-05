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
  // Breadcrumbs removed - unused
  // Link removed - unused
  Chip,
  // Divider removed - unused
  Alert,
  AlertTitle,
  useTheme,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Card,
  CardContent,
  IconButton,
  alpha,
  Fade,
  useMediaQuery
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import UploadFileIcon from '@mui/icons-material/UploadFile';
// NavigateNextIcon removed - unused
// HistoryIcon removed - unused
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import LocalHospitalOutlinedIcon from '@mui/icons-material/LocalHospitalOutlined';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
// PDFProcessingStatus removed - unused
import { getAllBiomarkers, getBiomarkersByFileId, getBiomarkerCategories, getBiomarkerExplanation, getPDFStatus } from '../services/api';
import { getProfiles } from '../services/profileService'; // Corrected import name
import BiomarkerTable from '../components/BiomarkerTable';
import BiomarkerVisualization from '../components/BiomarkerVisualization';
import ExplanationModal from '../components/ExplanationModal';
import ViewToggle from '../components/ViewToggle';
import type { Biomarker } from '../types/biomarker.d'; // Adjusted path if needed based on file structure
import { BiomarkerExplanation } from '../types/api';
import { Profile } from '../types/Profile'; // Corrected import name

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

// New component for report metadata display
const ReportMetadataCard: React.FC<{
  metadata: {
    lab_name?: string;
    report_date?: string;
    filename?: string;
    profile_name?: string;
  }
}> = ({ metadata }) => {
  const theme = useTheme();
  
  return (
    <Card 
      elevation={0}
      sx={{ 
        backgroundColor: alpha(theme.palette.background.paper, 0.7),
        backdropFilter: 'blur(10px)',
        borderRadius: '16px',
        mb: 3,
        border: `1px solid ${alpha(theme.palette.divider, 0.05)}`
      }}
    >
      <CardContent sx={{ p: 2.5 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <LocalHospitalOutlinedIcon sx={{ mr: 1, color: theme.palette.text.secondary }} />
              <Box>
                <Typography variant="caption" color="text.secondary">Lab Provider</Typography>
                <Typography variant="body2" fontWeight="medium">{metadata.lab_name || 'Unknown Lab'}</Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AccessTimeIcon sx={{ mr: 1, color: theme.palette.text.secondary }} />
              <Box>
                <Typography variant="caption" color="text.secondary">Report Date</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {metadata.report_date 
                    ? new Date(metadata.report_date).toLocaleDateString('en-US', { 
                        year: 'numeric', 
                        month: 'short', 
                        day: 'numeric' 
                      }) 
                    : 'Unknown Date'}
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <InfoOutlinedIcon sx={{ mr: 1, color: theme.palette.text.secondary }} />
              <Box>
                <Typography variant="caption" color="text.secondary">File Name</Typography>
                <Typography variant="body2" fontWeight="medium" noWrap sx={{ maxWidth: '150px' }}>
                  {metadata.filename || 'No File'}
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <TrendingUpIcon sx={{ mr: 1, color: theme.palette.text.secondary }} />
              <Box>
                <Typography variant="caption" color="text.secondary">Patient</Typography>
                <Typography variant="body2" fontWeight="medium">
                  {metadata.profile_name || 'No Patient'}
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

// New component for category filters with improved visual design
const CategoryFilters: React.FC<{
  categories: string[];
  selectedCategory: string | null;
  onCategorySelect: (category: string | null) => void;
}> = ({ categories, selectedCategory, onCategorySelect }) => {
  const theme = useTheme();
  
  return (
    <Box 
      sx={{ 
        display: 'flex', 
        flexWrap: 'wrap', 
        gap: 1, 
        mb: 3,
        pb: 2,
        borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`
      }}
    >
      <Chip
        label="All Categories"
        onClick={() => onCategorySelect(null)}
        color={selectedCategory === null ? 'primary' : 'default'}
        variant={selectedCategory === null ? 'filled' : 'outlined'}
        sx={{ 
          borderRadius: '8px',
          '&.MuiChip-filled': {
            backgroundColor: alpha(theme.palette.primary.main, 0.15),
            color: theme.palette.primary.main,
            fontWeight: 500
          },
          '&.MuiChip-outlined': {
            borderColor: alpha(theme.palette.divider, 0.3),
            color: theme.palette.text.secondary
          }
        }}
      />
      
      {categories.map((category) => (
        <Chip
          key={category}
          label={category}
          onClick={() => onCategorySelect(category)}
          color={selectedCategory === category ? 'primary' : 'default'}
          variant={selectedCategory === category ? 'filled' : 'outlined'}
          sx={{ 
            borderRadius: '8px',
            '&.MuiChip-filled': {
              backgroundColor: alpha(theme.palette.primary.main, 0.15),
              color: theme.palette.primary.main,
              fontWeight: 500
            },
            '&.MuiChip-outlined': {
              borderColor: alpha(theme.palette.divider, 0.3),
              color: theme.palette.text.secondary
            }
          }}
        />
      ))}
    </Box>
  );
};

// Enhanced action button with improved styling
const ActionButton: React.FC<{
  icon: React.ReactNode;
  label: string;
  onClick: () => void;
  color?: string;
}> = ({ icon, label, onClick, color }) => {
  const theme = useTheme();
  
  return (
    <Button
      startIcon={icon}
      onClick={onClick}
      variant="outlined"
      sx={{
        borderRadius: '10px',
        textTransform: 'none',
        px: 2,
        py: 1,
        borderColor: color ? color : alpha(theme.palette.primary.main, 0.2),
        color: color ? color : theme.palette.primary.main,
        bgcolor: alpha(color || theme.palette.primary.main, 0.05),
        '&:hover': {
          bgcolor: alpha(color || theme.palette.primary.main, 0.1),
          borderColor: color ? color : alpha(theme.palette.primary.main, 0.3),
        }
      }}
    >
      {label}
    </Button>
  );
};

const BiomarkerPage: React.FC = () => {
  const { fileId } = useParams<{ fileId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  
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

  const [profiles, setProfiles] = useState<Profile[]>([]); // Use correct Profile type
  // const [profilesLoading, setProfilesLoading] = useState(false); // Removed unused state

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

            // Correctly use pdfStatus properties that exist on ProcessingStatus type
            if (pdfStatus && pdfStatus.fileId) { // Check for fileId as an indicator of a valid status object
               // Try to extract profileId from biomarkers if not directly in status
               // (This logic remains, but don't access non-existent props on pdfStatus)

               // Set metadata based on available pdfStatus fields or defaults
               setMetadata({
                 lab_name: (pdfStatus as any).lab_name || "Lab Provider", // Use 'any' assertion carefully if structure is known but not typed
                 report_date: (pdfStatus as any).report_date || new Date().toISOString().split('T')[0],
                 filename: pdfStatus.filename || "lab_report.pdf",
                 profile_name: (pdfStatus as any).profile_name || "Patient Profile" // Use 'any' assertion carefully
               });

               // Attempt to get profileId from the status object if it exists (might be added later)
               if ((pdfStatus as any).profileId) {
                 extractedProfileId = (pdfStatus as any).profileId;
                 console.log(`Found profile ID from PDF status: ${extractedProfileId}`);
                 setProfileId(extractedProfileId);
               }

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
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => { // Mark event as unused
    setTabValue(newValue);
  };
  
  // Handle category selection
  const handleCategoryClick = (category: string | null) => {
    setSelectedCategory(category);
  };
  
  // Handle back button
  const handleBack = () => {
    navigate('/dashboard');
  };
  
  // Handle upload new
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
      // Calculate the abnormal status with refined null checks for type safety
      let isAbnormal = biomarker.isAbnormal; // Use existing value if defined
      if (isAbnormal === undefined) {
          if (biomarker.reference_range_low != null && biomarker.reference_range_high != null) {
              // Both bounds exist, perform comparison
              isAbnormal = biomarker.value < biomarker.reference_range_low || biomarker.value > biomarker.reference_range_high;
          } else {
              // If range is incomplete, cannot determine abnormality based on range
              isAbnormal = false; // Or potentially handle as 'unknown' if needed elsewhere
          }
      }

      // Format reference range with null checks
      const referenceRange = biomarker.referenceRange ||
        (biomarker.reference_range_low != null && biomarker.reference_range_high != null
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
        // Assuming getProfiles returns an object like { items: Profile[] } or similar
        const profilesResponse = await getProfiles();
        // Access the array property (e.g., 'items') or default to the response itself if it's the array
        setProfiles((profilesResponse as any).items || profilesResponse || []);
      } catch (err) {
        console.error('Error fetching profiles:', err);
      } // finally { // Removed unused state setter
        // setProfilesLoading(false);
      // }
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
  
  // This returns the redesigned UI
  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header with back button and title */}
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          mb: 3 
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton 
            onClick={handleBack} 
            sx={{ 
              mr: 2, 
              bgcolor: alpha(theme.palette.background.paper, 0.6), 
              '&:hover': { bgcolor: alpha(theme.palette.background.paper, 0.8) }
            }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Typography 
            variant="h4" 
            component="h1" 
            sx={{ 
              fontWeight: 600, 
              color: theme.palette.text.primary,
              fontSize: { xs: '1.5rem', sm: '2rem' } 
            }}
          >
            Health Analysis
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Fade in={!loading}>
            <Box>
              <ViewToggle 
                currentView={currentView} 
                onChange={handleViewChange} 
              />
            </Box>
          </Fade>
          
          {!isMobile && (
            <ActionButton
              icon={<UploadFileIcon />}
              label="Upload New Report"
              onClick={handleUploadNew}
              color={theme.palette.info.main}
            />
          )}
        </Box>
      </Box>
      
      {/* Error alert */}
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3, borderRadius: '12px' }}
        >
          <AlertTitle>Error</AlertTitle>
          {error}
        </Alert>
      )}
      
      {/* Report metadata card */}
      {!loading && Object.keys(metadata).length > 0 && (
        <ReportMetadataCard metadata={metadata} />
      )}
      
      {/* Profile selector */}
      {currentView === 'history' && profiles.length > 0 && (
        <FormControl 
          variant="outlined" 
          sx={{ 
            mb: 3, 
            minWidth: 240,
            '& .MuiOutlinedInput-root': {
              borderRadius: '10px',
              '& fieldset': {
                borderColor: alpha(theme.palette.divider, 0.2),
              },
              '&:hover fieldset': {
                borderColor: alpha(theme.palette.primary.main, 0.5),
              },
            },
          }}
        >
          <InputLabel id="profile-select-label">Select Profile</InputLabel>
          <Select
            labelId="profile-select-label"
            id="profile-select"
            value={profileId || ''}
            onChange={handleProfileSelect}
            label="Select Profile"
          >
            {profiles.map((profile) => (
              <MenuItem key={profile.id} value={profile.id}>
                {profile.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      )}
      
      {/* Loading indicator */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 5 }}>
          <CircularProgress size={40} thickness={4} />
        </Box>
      )}
      
      {/* Categories filter */}
      {!loading && categories.length > 0 && (
        <CategoryFilters
          categories={categories}
          selectedCategory={selectedCategory}
          onCategorySelect={handleCategoryClick}
        />
      )}
      
      {/* Tab Navigation */}
      {!loading && (
        <Box sx={{ borderBottom: 1, borderColor: alpha(theme.palette.divider, 0.1), mb: 2 }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange} 
            aria-label="biomarker display tabs"
            textColor="primary"
            indicatorColor="primary"
            sx={{
              '& .MuiTab-root': {
                textTransform: 'none',
                fontSize: '1rem',
                fontWeight: 500,
                minWidth: 100,
                px: 3
              }
            }}
          >
            <Tab label="Table View" id="biomarker-tab-0" aria-controls="biomarker-tabpanel-0" />
            <Tab label="Visualization" id="biomarker-tab-1" aria-controls="biomarker-tabpanel-1" />
          </Tabs>
        </Box>
      )}
      
      {/* Tab Panels */}
      {!loading && (
        <>
          <TabPanel value={tabValue} index={0}>
            <Paper 
              elevation={0} 
              sx={{ 
                borderRadius: '16px',
                bgcolor: alpha(theme.palette.background.paper, 0.6),
                border: `1px solid ${alpha(theme.palette.divider, 0.05)}`,
                overflow: 'hidden'
              }}
            >
              <BiomarkerTable
                // fileId={fileId} // Remove fileId prop again
                biomarkers={biomarkers}
                isLoading={loading}
                error={error}
                onViewHistory={onViewHistory}
                onExplainWithAI={handleExplainBiomarker}
                showSource={currentView === 'history'}
              />
            </Paper>
          </TabPanel>
          
          <TabPanel value={tabValue} index={1}>
            <Paper 
              elevation={0} 
              sx={{ 
                p: 3, 
                borderRadius: '16px',
                bgcolor: alpha(theme.palette.background.paper, 0.6),
                border: `1px solid ${alpha(theme.palette.divider, 0.05)}`,
              }}
            >
              <BiomarkerVisualization 
                biomarkers={biomarkers}
                // onSelectBiomarker={handleExplainBiomarker} // Removed incorrect prop
              />
            </Paper>
          </TabPanel>
        </>
      )}
      
      {/* AI Explanation Modal */}
      <ExplanationModal
        open={explanationModalOpen}
        onClose={handleCloseExplanationModal}
        biomarker={currentBiomarker}
        explanation={explanation}
        loading={explanationLoading}
        error={explanationError}
      />

      {/* Removed commented out code block causing TS18047 */}

      {/* Mobile Upload Button - Fixed at bottom for mobile */}
      {isMobile && (
        <Box 
          sx={{ 
            position: 'fixed', 
            bottom: 16, 
            right: 16, 
            zIndex: 10 
          }}
        >
          <Button
            variant="contained"
            color="primary"
            startIcon={<UploadFileIcon />}
            onClick={handleUploadNew}
            sx={{ 
              borderRadius: '12px', 
              px: 3, 
              py: 1.5,
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              textTransform: 'none',
              fontWeight: 500
            }}
          >
            Upload
          </Button>
        </Box>
      )}
    </Container>
  );
};

export default BiomarkerPage;
