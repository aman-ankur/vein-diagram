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
  Tooltip,
  IconButton,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  SelectChangeEvent // Import SelectChangeEvent
} from '@mui/material';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import BarChartIcon from '@mui/icons-material/BarChart';
import TableChartIcon from '@mui/icons-material/TableChart';
import HistoryIcon from '@mui/icons-material/History'; // Import HistoryIcon
import TimelineIcon from '@mui/icons-material/Timeline';
import CategoryIcon from '@mui/icons-material/Category';
import SummarizeIcon from '@mui/icons-material/Summarize';
import RefreshIcon from '@mui/icons-material/Refresh';

import { getBiomarkersByFileId, getAllBiomarkers, getBiomarkerExplanation } from '../services/api';
import { getProfiles } from '../services/profileService'; // Import getProfiles
import { Biomarker } from '../types/biomarker';
import { Profile } from '../types/Profile'; // Import Profile type
import BiomarkerTable from '../components/BiomarkerTable';
import ExplanationModal from '../components/ExplanationModal';
import type { BiomarkerExplanation } from '../types/api';
import { useProfile } from '../contexts/ProfileContext';
import FavoriteBiomarkersGrid from '../components/FavoriteBiomarkersGrid'; // Import the grid
import {
  processBiomarkersForFavorites,
  ProcessedFavoriteData,
} from '../utils/biomarkerUtils'; // Import processing function and type
import {
  getFavoritesForProfile,
  addFavorite,
  removeFavorite,
  isFavorite, // Import isFavorite checker
} from '../utils/favoritesUtils'; // Import localStorage utils
import { parseISO, compareDesc } from 'date-fns'; // Import date-fns functions
import AddFavoriteModal from '../components/AddFavoriteModal'; // Import the modal

// --- Constants ---
const MAX_DISPLAY_TILES = 8; // Changed to 8 for a 2x4 grid layout

// Expanded base list for popularity scoring
const BASE_IMPORTANT_BIOMARKERS: string[] = [
  // Lipids
  'Total Cholesterol', 'LDL Cholesterol', 'HDL Cholesterol', 'Triglycerides', 'Non-HDL Cholesterol', 'Apolipoprotein B', 'Lp(a)',
  // Glucose Metabolism
  'Glucose', 'HbA1c', 'Insulin', 'Fasting Insulin',
  // Vitamins & Minerals
  'Vitamin D', // Canonical name
  'Vitamin B12', 'Folate', 'Ferritin', 'Iron', 'Magnesium', 'Zinc',
  // Thyroid
  'TSH', 'Free T3', 'Free T4', 'Reverse T3', 'Thyroglobulin Antibodies', 'Thyroid Peroxidase Antibodies',
  // Inflammation
  'hs-CRP', 'Homocysteine', 'Fibrinogen',
  // Liver Function
  'ALT', 'AST', 'GGT', 'Bilirubin, Total', 'Albumin', 'Alkaline Phosphatase',
  // Kidney Function
  'Creatinine', 'BUN', 'eGFR', 'Uric Acid',
  // Complete Blood Count (CBC)
  'Hemoglobin', 'Hematocrit', 'WBC Count', 'RBC Count', 'Platelet Count', 'MCV', 'MCH', 'MCHC', 'RDW',
  // Hormones
  'Testosterone', 'Free Testosterone', 'Estradiol', 'Progesterone', 'Cortisol', 'DHEA-S', 'SHBG',
  // Other Common
  'Sodium', 'Potassium', 'Chloride', 'CO2', 'Calcium', 'Protein, Total', 'Globulin'
];


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
  const profileIdFromUrl = queryParams.get('profileId');
  
  // Destructure loading state AND setter function from profile context
  const { activeProfile, loading: profileLoading, setActiveProfileById } = useProfile(); 
  
  // Enhanced console logging for debugging
  useEffect(() => {
    console.log("========== VISUALIZATION PAGE DEBUG ==========");
    console.log("Component mounted with:");
    console.log("fileId from query:", fileId);
    console.log("profileId from query:", profileIdFromUrl);
    console.log("full URL search:", location.search);
    console.log("activeProfile:", activeProfile ? {
      id: activeProfile.id,
      name: activeProfile.name,
      type: typeof activeProfile.id
    } : "null");
    console.log("profileLoading:", profileLoading); // Log profile loading state
    console.log("==============================================");

    // If a profileId is provided in the URL and it's different from the active profile,
    // update the active profile
    if (profileIdFromUrl && (!activeProfile || profileIdFromUrl !== activeProfile.id)) {
      console.log(`Setting active profile to ${profileIdFromUrl} from URL parameter`);
      setActiveProfileById(profileIdFromUrl).catch(error => {
        console.error("Failed to set profile from URL:", error);
        setError("Failed to load the specified profile. Using default profile instead.");
      });
    }
  }, [fileId, profileIdFromUrl, activeProfile, location.search, profileLoading, setActiveProfileById]);
  
  // State for biomarkers, loading, and error
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  // Rename local loading state to avoid conflict
  const [biomarkerLoading, setBiomarkerLoading] = useState<boolean>(true); 
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<number>(0);
  const [chartType, setChartType] = useState<'bar' | 'line' | 'scatter'>('line');

  // State for AI explanation modal
  const [explanationModalOpen, setExplanationModalOpen] = useState<boolean>(false);
  const [currentBiomarker, setCurrentBiomarker] = useState<Biomarker | null>(null);
  const [explanationLoading, setExplanationLoading] = useState<boolean>(false);
  const [explanationError, setExplanationError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<BiomarkerExplanation | null>(null);

  // State for favorite biomarkers
  const [favoriteNames, setFavoriteNames] = useState<string[]>([]);
  const [processedFavoritesData, setProcessedFavoritesData] = useState<ProcessedFavoriteData[]>([]);

  // State for profile selection dropdown
  const [availableProfiles, setAvailableProfiles] = useState<Profile[]>([]);
  const [profileListLoading, setProfileListLoading] = useState<boolean>(false);
  const [profileListError, setProfileListError] = useState<string | null>(null);

  // State for Add Favorite Modal
  const [isAddModalOpen, setIsAddModalOpen] = useState<boolean>(false);


  // --- Effects ---

  // 1. Load initial favorite names from localStorage when profile changes
  useEffect(() => {
    if (activeProfile?.id) {
      console.log(`Profile changed to ${activeProfile.id}, loading favorites from localStorage.`);
      const initialFavorites = getFavoritesForProfile(activeProfile.id);
      setFavoriteNames(initialFavorites);
    } else {
      // Clear favorites if profile is removed
      setFavoriteNames([]);
      setProcessedFavoritesData([]);
    }
  }, [activeProfile]);


  // 2. Fetch all biomarkers when profile changes (and is loaded) or fileId changes
  useEffect(() => {
    // Only fetch if profile context is not loading
    if (!profileLoading) { 
      fetchBiomarkers();
    }
  }, [fileId, activeProfile, profileLoading]);

  // 3. Process biomarkers for the favorite grid (Hybrid Logic: Explicit Favorites + Top Scored Fillers)
  useEffect(() => {
    if (biomarkers.length > 0 && activeProfile?.id) {
      console.log('Processing biomarkers for favorite grid (Hybrid Logic)...');

      // Get explicitly favorited names (already in favoriteNames state)
      const explicitFavoriteNames = favoriteNames;
      console.log('Explicit favorites:', explicitFavoriteNames);

      // Process data for explicit favorites
      let processedExplicitFavorites: ProcessedFavoriteData[] = [];
      if (explicitFavoriteNames.length > 0) {
        processedExplicitFavorites = processBiomarkersForFavorites(biomarkers, explicitFavoriteNames);
        console.log(`Processed ${processedExplicitFavorites.length} explicit favorites.`);
      }

      // Determine how many filler slots are needed
      const slotsToFill = MAX_DISPLAY_TILES - processedExplicitFavorites.length;
      let processedFillers: ProcessedFavoriteData[] = [];

      if (slotsToFill > 0) {
        console.log(`Need to fill ${slotsToFill} slots with top-scored biomarkers.`);

        // --- Calculate scores for potential fillers ---
        const biomarkersByName: { [key: string]: { date: Date; reportId: string | number }[] } = {};
        let latestReportDate: Date | null = null;

        biomarkers.forEach(bm => {
          const reportDate = bm.reportDate ? parseISO(bm.reportDate) : null;
          if (reportDate) {
            if (!biomarkersByName[bm.name]) {
              biomarkersByName[bm.name] = [];
            }
            biomarkersByName[bm.name].push({ date: reportDate, reportId: bm.fileId || reportDate.toISOString() });
            if (!latestReportDate || compareDesc(latestReportDate, reportDate) < 0) {
              latestReportDate = reportDate;
            }
          }
        });

        // Calculate scores ONLY for base biomarkers that are NOT already explicit favorites
        const potentialFillerNames = BASE_IMPORTANT_BIOMARKERS.filter(
          name => !explicitFavoriteNames.includes(name) && biomarkersByName[name]
        );

        const scoredFillers = potentialFillerNames.map(name => {
          const history = biomarkersByName[name];
          const uniqueReports = new Set(history.map(h => h.reportId));
          const frequency = uniqueReports.size;
          const measuredInLatest = latestReportDate ? history.some(h => h.date.getTime() === latestReportDate!.getTime()) : false;
          const recencyBoost = measuredInLatest ? 3 : 0;
          const score = recencyBoost + frequency;
          return { name, score };
        });

        // Sort potential fillers by score descending
        scoredFillers.sort((a, b) => b.score - a.score);

        // Select top N fillers needed
        const topFillerNames = scoredFillers.slice(0, slotsToFill).map(bm => bm.name);
        console.log('Top scored fillers selected:', topFillerNames);

        if (topFillerNames.length > 0) {
          // Process data for the selected fillers
          processedFillers = processBiomarkersForFavorites(biomarkers, topFillerNames);
          // Sort fillers based on their score ranking
          processedFillers.sort((a, b) => {
            const scoreA = scoredFillers.find(s => s.name === a.name)?.score ?? 0;
            const scoreB = scoredFillers.find(s => s.name === b.name)?.score ?? 0;
            return scoreB - scoreA;
          });
          console.log(`Processed ${processedFillers.length} filler biomarkers.`);
        }
      } else {
        console.log('No filler slots needed or available.');
      }

      // Combine explicit favorites and fillers
      const finalGridData = [...processedExplicitFavorites, ...processedFillers];
      console.log('Final combined grid data:', finalGridData.map(d => d.name));

      setProcessedFavoritesData(finalGridData);

    } else {
      console.log('Clearing favorite grid data (no biomarkers or profile).');
      setProcessedFavoritesData([]); // Clear if no biomarkers or no profile
    }
  // Rerun when biomarkers, the active profile, OR the list of explicit favorite names changes
  }, [biomarkers, activeProfile, favoriteNames]);

  // 4. Fetch available profiles if none is active
  useEffect(() => {
    const fetchAvailableProfiles = async () => {
      // Only fetch if no profile is active and we aren't already loading them
      if (!activeProfile && !profileLoading && !profileListLoading) {
        console.log("No active profile, fetching available profiles for dropdown...");
        setProfileListLoading(true);
        setProfileListError(null);
        try {
          // Fetch a decent number of profiles, assuming not thousands for now
          const response = await getProfiles(undefined, 1, 100);
          setAvailableProfiles(response.profiles);
          console.log(`Fetched ${response.profiles.length} available profiles.`);
        } catch (err) {
          console.error("Error fetching available profiles:", err);
          setProfileListError("Could not load profile list.");
          setAvailableProfiles([]); // Clear list on error
        } finally {
          setProfileListLoading(false);
        }
      }
    };

    fetchAvailableProfiles();
    // Dependency array: run when activeProfile or its loading state changes
    // REMOVED profileListLoading to prevent infinite loop
  }, [activeProfile, profileLoading]);


  // --- Handlers ---

  // Function to fetch biomarkers
  const fetchBiomarkers = async () => {
    setBiomarkerLoading(true); // Use renamed state setter
    setError(null);
    
    try {
      let data: Biomarker[];
      // Prioritize URL profileId over activeProfile.id for consistency
      const profileId = profileIdFromUrl || activeProfile?.id;
      
      console.log('Fetching biomarkers with:', { 
        fileId, 
        profileIdFromUrl,
        activeProfileId: activeProfile?.id,
        profileIdToUse: profileId,
        activeProfile: activeProfile ? {
          id: activeProfile.id,
          name: activeProfile.name,
          idType: typeof activeProfile.id
        } : null 
      });
      
      // Force profileId to be a string to prevent type issues
      const profileIdStr = profileId?.toString();
      
      // Log the value we're actually going to send
      console.log(`FINAL PROFILE ID TO SEND: "${profileIdStr}" (${typeof profileIdStr})`); 
      
      if (fileId) {
        try {
          // DIRECT FETCH APPROACH: Bypass the API client completely
          console.log(`DIRECT FETCH: Using fetch API directly to ensure parameters are included`); 
          
          // Build URL with profile_id included directly in the URL as a query parameter
          const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || '';
          const url = `${apiBaseUrl}/api/pdf/${fileId}/biomarkers?profile_id=${encodeURIComponent(profileIdStr || '')}`;
          
          console.log(`Making direct fetch to: ${url}`); 
          
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
          console.log(`Direct fetch response received with ${jsonData.length} biomarkers`); 
          
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
          console.error(`Direct fetch failed, falling back to API client:`, fetchError); 
          // Fall back to the regular API client
          console.log(`Calling getBiomarkersByFileId with fileId=${fileId} and profileId=${profileIdStr || 'undefined'}`);
          data = await getBiomarkersByFileId(fileId, profileIdStr);
        }
        
        console.log(`Received ${data.length} biomarkers for file ${fileId}`);
      } else {
        // Fetch all biomarkers only if a profile is active
        if (profileIdStr) {
          console.log(`Calling getAllBiomarkers with profile_id=${profileIdStr}`);
          data = await getAllBiomarkers({
            profile_id: profileIdStr
          });
          console.log(`Received ${data.length} biomarkers in total for profile ${profileIdStr}`);
        } else {
          console.log('No active profile, skipping fetch for all biomarkers.');
          data = []; // Set to empty array if no profile
        }
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
      setBiomarkerLoading(false); // Use renamed state setter
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

  // Handler for toggling a favorite biomarker
  const handleToggleFavorite = (biomarkerName: string) => {
    if (!activeProfile?.id) return;

    const currentIsFavorite = isFavorite(activeProfile.id, biomarkerName);
    let updatedFavorites: string[];

    if (currentIsFavorite) {
      console.log(`Removing ${biomarkerName} from favorites for profile ${activeProfile.id}`);
      updatedFavorites = removeFavorite(activeProfile.id, biomarkerName);
    } else {
      console.log(`Adding ${biomarkerName} to favorites for profile ${activeProfile.id}`);
      updatedFavorites = addFavorite(activeProfile.id, biomarkerName);
    }
    // Update the local state to trigger re-render of grid/tiles
    setFavoriteNames(updatedFavorites);
  };

  // Handler for profile selection change from dropdown
  const handleProfileSelectChange = (event: SelectChangeEvent<string>) => { // Use SelectChangeEvent
    const selectedProfileId = event.target.value as string;
    console.log(`Profile selected from dropdown: ${selectedProfileId}`);
    if (selectedProfileId) {
      // Use the context function to set the active profile
      // This will trigger other useEffects to load data for the new profile
      setActiveProfileById(selectedProfileId);
    }
  };

  // Handlers for Add Favorite Modal
  const handleOpenAddModal = () => {
    console.log("Opening Add Favorite Modal");
    setIsAddModalOpen(true);
  };

  const handleCloseAddModal = () => {
    setIsAddModalOpen(false);
  };

  // Handler to actually add the favorite from the modal
  const handleAddFavoriteFromModal = (biomarkerName: string) => {
    if (!activeProfile?.id) return;
    console.log(`Adding ${biomarkerName} from modal for profile ${activeProfile.id}`);
    const updatedFavorites = addFavorite(activeProfile.id, biomarkerName);
    // Update the local state to trigger re-render of grid/tiles
    // This will cause the popularity useEffect to rerun and potentially include the new favorite
    setFavoriteNames(updatedFavorites);
    // Note: The grid might not update immediately if the new favorite doesn't make the top 10 score.
    // A more robust solution might involve directly manipulating processedFavoritesData state,
    // but let's stick to the score-based approach for now.
  };


  // --- Render Logic ---

  // Render loading state for profile context OR biomarker data
  if (profileLoading || biomarkerLoading) {
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
            {profileLoading ? 'Loading profile...' : 'Loading biomarker data...'}
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

  // Handle the case where overview is shown but no profile is active (and not loading)
  // Show dropdown instead of button
  if (!profileLoading && !activeProfile && !fileId) {
     return (
       <Container maxWidth="lg">
         <Paper sx={{ p: 3, mt: 3, textAlign: 'center' }}>
           <Typography variant="h6" gutterBottom>
             Select a Profile
           </Typography>
           <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
             Choose a profile below to view their biomarker visualizations.
           </Typography>
           {profileListLoading ? (
             <CircularProgress />
           ) : profileListError ? (
             <Alert severity="error">{profileListError}</Alert>
           ) : availableProfiles.length > 0 ? (
             <FormControl sx={{ m: 1, minWidth: 200 }}>
               <InputLabel id="profile-select-label">Profile</InputLabel>
               <Select
                 labelId="profile-select-label"
                 id="profile-select"
                 value="" // No value selected initially
                 label="Profile"
                 onChange={handleProfileSelectChange}
               >
                 {availableProfiles.map((profile) => (
                   <MenuItem key={profile.id} value={profile.id}>
                     {profile.name}
                   </MenuItem>
                 ))}
               </Select>
             </FormControl>
           ) : (
             <Alert severity="warning">No profiles found. Please create one first.</Alert>
           )}
           <Box sx={{ mt: 3 }}>
              <Button component={Link} to="/profiles">
                Manage Profiles
              </Button>
           </Box>
         </Paper>
       </Container>
     );
  }

  // If profile is loaded but no biomarkers found (and not loading/error)
  if (!biomarkerLoading && !error && biomarkers.length === 0 && activeProfile) {
    return (
      <Container maxWidth="lg">
        <Paper sx={{ p: 3, mt: 3 }}>
          <Alert severity="info">
            No biomarker data available for this {fileId ? 'file' : 'profile'}. 
            {fileId ? '' : ' Please upload a lab report to get started.'}
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

  // Add console log here to check activeProfile before rendering the button
  console.log('Rendering History Button - activeProfile:', activeProfile);

  return (
    <Container maxWidth="lg">
      {/* Header Box for Title and Description */}
      <Box sx={{ mt: 3, mb: 2 }}> 
        <Typography variant="h4" component="h1" gutterBottom>
          {fileId ? 'File Analysis' : `Biomarker Overview for ${activeProfile?.name || 'Profile'}`} {/* Show profile name */}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {fileId 
            ? `View and analyze biomarkers extracted from ${biomarkers[0]?.fileName || 'your uploaded file'}` // Show filename if available
            : `View all biomarkers across lab reports for ${activeProfile?.name || 'the selected profile'}`
          }
        </Typography>
      </Box>

      {/* Box specifically for the History Button */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'flex-start' }}> 
        <Tooltip 
          title={
            activeProfile 
              ? `View the complete biomarker history for profile: ${activeProfile.name}` 
              : "Select a profile to view biomarker history"
          }
        >
          {/* Disable button if no active profile AND not viewing a specific file */}
          <Button
            component={Link}
            to={activeProfile ? `/profile/${activeProfile.id}/history` : '/profiles'} // Conditional link
            variant="outlined"
            startIcon={<HistoryIcon />}
            disabled={!activeProfile && !fileId} // Disable if overview mode and no profile
          >
            {activeProfile ? 'View Biomarker History' : 'Select Profile'} {/* Conditional text */}
          </Button>
        </Tooltip>
      </Box>

      {/* --- Favorite Biomarkers Section --- */}
      {activeProfile && ( // Only show favorites if a profile is active
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" component="h2" gutterBottom sx={{ mb: 2 }}>
            Favorite Biomarkers
          </Typography>
          {/* Render the grid unconditionally, let it handle empty data */}
          <FavoriteBiomarkersGrid
            profileId={activeProfile.id}
            favoriteData={processedFavoritesData} // Pass current data (could be empty)
            onToggleFavorite={handleToggleFavorite}
            onAddClick={handleOpenAddModal}
          />
          {/* Optional: Add text below the grid if it's completely empty */}
          {processedFavoritesData.length === 0 && (
             <Typography color="text.secondary" sx={{ mt: 1, textAlign: 'center' }}>
               No popular biomarkers found. Click '+' above to add manually.
             </Typography>
          )}
        </Box>
      )}
      {/* --- End Favorite Biomarkers Section --- */}


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

      {/* AI Explanation Modal - Re-enabled */}
       {currentBiomarker && (
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
      )}

      {/* Add Favorite Modal */}
      {activeProfile && (
        <AddFavoriteModal
          open={isAddModalOpen}
          onClose={handleCloseAddModal}
          availableBiomarkers={biomarkers} // Pass all fetched biomarkers
          currentFavorites={processedFavoritesData.map(fav => fav.name)} // Pass names currently in grid
          onAddFavorite={handleAddFavoriteFromModal}
          isLoading={biomarkerLoading} // Pass loading state
          error={error} // Pass error state
        />
      )}
    </Container>
  );
};

export default VisualizationPage;
