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
  SelectChangeEvent, // Import SelectChangeEvent
  Dialog, // Added for confirmation
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Snackbar // Added for feedback
} from '@mui/material';
import { useParams, useNavigate, useLocation, Link } from 'react-router-dom';
import BarChartIcon from '@mui/icons-material/BarChart';
import TableChartIcon from '@mui/icons-material/TableChart';
import HistoryIcon from '@mui/icons-material/History'; // Import HistoryIcon
import TimelineIcon from '@mui/icons-material/Timeline';
import CategoryIcon from '@mui/icons-material/Category';
import SummarizeIcon from '@mui/icons-material/Summarize'; // Re-added SummarizeIcon
import RefreshIcon from '@mui/icons-material/Refresh'; // Keep RefreshIcon if used in error handling
import UpdateIcon from '@mui/icons-material/Update'; // Add UpdateIcon for the generate button
import PsychologyIcon from '@mui/icons-material/Psychology'; // AI brain icon
import SmartToyIcon from '@mui/icons-material/SmartToy'; // Another AI icon option
import PersonIcon from '@mui/icons-material/Person';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import PersonAddIcon from '@mui/icons-material/PersonAdd';

import { getBiomarkersByFileId, getAllBiomarkers, getBiomarkerExplanation, deleteBiomarkerEntry } from '../services/api'; // Added deleteBiomarkerEntry
import { getProfiles, generateHealthSummary } from '../services/profileService'; // Import generateHealthSummary
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
// Removed unused import for getFavoritesForProfile
import { parseISO, compareDesc } from 'date-fns'; // Import date-fns functions
import AddFavoriteModal from '../components/AddFavoriteModal'; // Import the modal
import ReplaceFavoriteModal from '../components/ReplaceFavoriteModal'; // Import the new modal
import { 
  updateFavoriteOrder, 
  addFavoriteBiomarker, // Import backend service functions
  removeFavoriteBiomarker 
} from '../services/profileService'; 

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
  
  // State for Replace Favorite Modal
  const [replaceModalOpen, setReplaceModalOpen] = useState<boolean>(false);
  const [biomarkerToReplaceWith, setBiomarkerToReplaceWith] = useState<string | null>(null);

  // State for Delete Confirmation Dialog
  const [deleteDialogOpen, setDeleteDialogOpen] = useState<boolean>(false);
  const [biomarkerIdToDelete, setBiomarkerIdToDelete] = useState<number | null>(null);
  const [deleteLoading, setDeleteLoading] = useState<boolean>(false);

  // State for Snackbar feedback
  const [snackbarOpen, setSnackbarOpen] = useState<boolean>(false);
  const [snackbarMessage, setSnackbarMessage] = useState<string>('');
  // Allow 'info' and 'warning' severities for the Snackbar Alert
  const [snackbarSeverity, setSnackbarSeverity] = useState<'success' | 'error' | 'info' | 'warning'>('success'); 

  // State for health summary generation
  const [isSummaryGenerating, setIsSummaryGenerating] = useState<boolean>(false);

  // --- Helper Function ---

  // Function to calculate and set the processed data for the favorite grid
  const calculateAndSetGridData = (currentFavoriteNames: string[]) => {
    if (biomarkers.length > 0 && activeProfile?.id) {
      console.log('Calculating grid data with explicit favorites:', currentFavoriteNames);

      // Process data for explicit favorites
      let processedExplicitFavorites: ProcessedFavoriteData[] = [];
      if (currentFavoriteNames.length > 0) {
        processedExplicitFavorites = processBiomarkersForFavorites(biomarkers, currentFavoriteNames);
      }

      // Determine how many filler slots are needed
      const slotsToFill = MAX_DISPLAY_TILES - processedExplicitFavorites.length;
      let processedFillers: ProcessedFavoriteData[] = [];

      if (slotsToFill > 0) {
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
          name => !currentFavoriteNames.includes(name) && biomarkersByName[name]
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

        if (topFillerNames.length > 0) {
          processedFillers = processBiomarkersForFavorites(biomarkers, topFillerNames);
          // Sort fillers based on their score ranking
          processedFillers.sort((a, b) => {
            const scoreA = scoredFillers.find(s => s.name === a.name)?.score ?? 0;
            const scoreB = scoredFillers.find(s => s.name === b.name)?.score ?? 0;
            return scoreB - scoreA;
          });
        }
      }

      // Combine explicit favorites and fillers
      const finalGridData = [...processedExplicitFavorites, ...processedFillers];
      console.log('Setting final grid data:', finalGridData.map(d => d.name));
      setProcessedFavoritesData(finalGridData);

    } else {
      console.log('Clearing favorite grid data (no biomarkers or profile).');
      setProcessedFavoritesData([]); // Clear if no biomarkers or no profile
    }
  };


  // --- Effects ---

  // 1. Load initial favorite names when profile changes
  useEffect(() => {
    if (activeProfile?.favorite_biomarkers) { // Check the field added to the Profile type
      console.log(`Profile changed to ${activeProfile.id}, loading favorites from profile data.`);
      console.log(`Profile changed to ${activeProfile.id}, loading favorites from profile data.`);
      setFavoriteNames(activeProfile.favorite_biomarkers);
    } else {
      // Clear favorites if profile is removed or has no favorites
      console.log('No active profile or no favorites in profile, clearing favoriteNames.');
      setFavoriteNames([]);
      // setProcessedFavoritesData([]); // Removed - calculation happens later
    }
    // Note: Grid calculation is now handled in the biomarker loading effect
  }, [activeProfile]);


  // 2. Fetch all biomarkers when profile changes (and is loaded) or fileId changes
  useEffect(() => {
    // Only fetch if profile context is not loading
    if (!profileLoading) { 
      fetchBiomarkers();
    }
  }, [fileId, activeProfile, profileLoading]);

  // 3. Calculate grid data when biomarkers load or profile changes (using current favoriteNames state)
  useEffect(() => {
    // Only calculate if biomarkers are loaded and profile is active
    if (!biomarkerLoading && biomarkers.length > 0 && activeProfile?.id) {
      console.log('Biomarkers loaded or profile changed, recalculating grid data...');
      calculateAndSetGridData(favoriteNames); // Use the current favoriteNames state
    } else if (!biomarkerLoading && activeProfile?.id) {
      // Handle case where profile is active but no biomarkers exist yet
      console.log('Profile active but no biomarkers, clearing grid data.');
      calculateAndSetGridData(favoriteNames); // Will likely result in empty grid
    }
  }, [biomarkers, biomarkerLoading, activeProfile]); // Rerun if biomarkers, loading state, or profile changes


  // 4. Fetch available profiles if the list is empty
  useEffect(() => {
    const fetchAvailableProfiles = async () => {
      // Fetch if the list is empty and we aren't already loading them
      if (availableProfiles.length === 0 && !profileListLoading) {
        console.log("Available profiles list is empty, fetching...");
        setProfileListLoading(true);
        setProfileListError(null);
        try {
          // Fetch a decent number of profiles, assuming not thousands for now
          const response = await getProfiles(undefined, 1, 100); // Fetch up to 100 profiles
          setAvailableProfiles(response.profiles);
          console.log(`Fetched ${response.profiles.length} available profiles.`);
        } catch (err) {
          console.error("Error fetching available profiles:", err);
          setProfileListError("Could not load profile list.");
          setAvailableProfiles([]); // Clear list on error
        } finally {
          setProfileListLoading(false);
        }
      } else {
         console.log("Available profiles already loaded or currently loading.");
      }
    };

    fetchAvailableProfiles();
    // Rerun if the profile list loading state changes (e.g., after an error and retry)
    // or if availableProfiles becomes empty for some reason.
  }, [profileListLoading, availableProfiles.length]); // Depend on length to refetch if cleared


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
          console.log(`Calling getAllBiomarkers with profile_id=${profileIdStr} and max limit`);
          // Request the maximum allowed number of biomarkers
          data = await getAllBiomarkers({ 
            profile_id: profileIdStr,
            limit: 1000 // Use the maximum allowed limit (1000)
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

  // Handler for toggling a favorite biomarker (now uses backend)
  const handleToggleFavorite = async (biomarkerName: string) => {
    if (!activeProfile?.id) return;

    const currentIsFavorite = favoriteNames.includes(biomarkerName); // Check against state

    try {
      let updatedProfile: Profile;
      if (currentIsFavorite) {
        console.log(`[handleToggleFavorite] Removing ${biomarkerName} for profile ${activeProfile.id}`); // Log removal attempt
        updatedProfile = await removeFavoriteBiomarker(activeProfile.id, biomarkerName);
        console.log(`[handleToggleFavorite] Backend removal successful. New favorites:`, updatedProfile.favorite_biomarkers); // Log result
      } else {
        // Check limit before calling backend add
        if (isFavoriteLimitReached) {
           handleReplaceFavoriteRequest(biomarkerName); // Trigger replacement flow
           return; // Don't proceed with direct add
        }
        console.log(`[handleToggleFavorite] Adding ${biomarkerName} for profile ${activeProfile.id}`); // Log add attempt
        updatedProfile = await addFavoriteBiomarker(activeProfile.id, biomarkerName);
        console.log(`[handleToggleFavorite] Backend add successful. New favorites:`, updatedProfile.favorite_biomarkers); // Log result
      }
      // Update the local state with the list returned from the backend
      const newFavorites = updatedProfile.favorite_biomarkers || [];
      console.log(`[handleToggleFavorite] Updating state with:`, newFavorites); // Log state update
      setFavoriteNames(newFavorites);
      // --- Trigger grid recalculation ---
      calculateAndSetGridData(newFavorites); 
      // --- End trigger ---
      setSnackbarMessage(`Favorite ${currentIsFavorite ? 'removed' : 'added'}.`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (err) {
       console.error(`Error toggling favorite ${biomarkerName}:`, err);
       setSnackbarMessage(`Failed to ${currentIsFavorite ? 'remove' : 'add'} favorite.`);
       setSnackbarSeverity('error');
       setSnackbarOpen(true);
    }
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

  // Handler to actually add the favorite from the modal (now uses backend)
  const handleAddFavoriteFromModal = async (biomarkerName: string) => {
    if (!activeProfile?.id) return;
    console.log(`Adding ${biomarkerName} from modal (backend) for profile ${activeProfile.id}`);
    
    // Check limit first
    if (isFavoriteLimitReached) {
      handleReplaceFavoriteRequest(biomarkerName); // Trigger replacement flow
      handleCloseAddModal(); // Close the add modal as replace modal will open
      return; 
    }
    
    try {
      // Call backend service
      const updatedProfile = await addFavoriteBiomarker(activeProfile.id, biomarkerName);
      // Update state with the list returned from backend
      const newFavorites = updatedProfile.favorite_biomarkers || [];
      setFavoriteNames(newFavorites);
      // --- Trigger grid recalculation ---
      calculateAndSetGridData(newFavorites);
      // --- End trigger ---
      setSnackbarMessage(`${biomarkerName} added to favorites.`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      handleCloseAddModal(); // Close the modal on success
    } catch (err) {
      console.error(`Error adding favorite ${biomarkerName} from modal:`, err);
      setSnackbarMessage(`Failed to add ${biomarkerName} to favorites.`);
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      // Optionally keep modal open on error? Closing for now.
      handleCloseAddModal();
    }
    // Note: The grid might not update immediately if the new favorite doesn't make the top 10 score.
    // A more robust solution might involve directly manipulating processedFavoritesData state,
    // but let's stick to the score-based approach for now.
  };

  // --- Delete Biomarker Handlers ---
  const handleDeleteBiomarkerRequest = (biomarkerId: number) => {
    console.log(`Request to delete biomarker entry ID: ${biomarkerId}`);
    setBiomarkerIdToDelete(biomarkerId);
    setDeleteDialogOpen(true);
  };

  const handleCloseDeleteDialog = () => {
    setDeleteDialogOpen(false);
    setBiomarkerIdToDelete(null);
  };

  const handleConfirmDelete = async () => {
    if (biomarkerIdToDelete === null) return;

    console.log(`Confirming deletion for biomarker entry ID: ${biomarkerIdToDelete}`);
    setDeleteLoading(true);
    try {
      await deleteBiomarkerEntry(biomarkerIdToDelete);
      console.log(`Successfully deleted biomarker entry ID: ${biomarkerIdToDelete}`);
      
      // Update local state
      setBiomarkers(prevBiomarkers => 
        prevBiomarkers.filter(bm => bm.id !== biomarkerIdToDelete)
      );
      
      // Show success feedback
      setSnackbarMessage('Biomarker entry deleted successfully.');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      
      // Close dialog and reset state
      handleCloseDeleteDialog();
      
      // Optional: Refresh favorite data if the deleted item could affect it
      // (This might already be handled by the useEffect dependency on `biomarkers`)
      
    } catch (err) {
      console.error(`Error deleting biomarker entry ID ${biomarkerIdToDelete}:`, err);
      // Show error feedback
      setSnackbarMessage('Failed to delete biomarker entry. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setDeleteLoading(false);
    }
  };
  // --- End Delete Biomarker Handlers ---

  // --- Snackbar Handler ---
  const handleCloseSnackbar = (event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbarOpen(false);
  };
  // --- End Snackbar Handler ---

  // --- Favorite Checkers/Handlers for Table ---
  // Check against component state which is sourced from backend profile data
  const isBiomarkerFavorite = (name: string): boolean => {
    return favoriteNames.includes(name);
  };

  const isFavoriteLimitReached = favoriteNames.length >= MAX_DISPLAY_TILES;

  const handleReplaceFavoriteRequest = (biomarkerName: string) => {
    console.log(`Request to replace a favorite to add: ${biomarkerName}`);
    setBiomarkerToReplaceWith(biomarkerName);
    // TODO: Open the actual replacement modal here
    setReplaceModalOpen(true); // Open the actual modal now
  };

  const handleCloseReplaceModal = () => {
    setReplaceModalOpen(false);
    setBiomarkerToReplaceWith(null); // Clear the biomarker name
  };

  // Make this async to allow await
  const handleConfirmReplace = async (favoriteToRemove: string, favoriteToAdd: string) => { 
    if (!activeProfile?.id) return;
    
    console.log(`Replacing favorite: Removing ${favoriteToRemove}, Adding ${favoriteToAdd}`);
    // Perform the actions: remove old, add new via backend calls
    try {
      // Set loading state if you add one to the modal
      // setIsLoading(true); 
      console.log(`Backend remove: ${favoriteToRemove}`);
      await removeFavoriteBiomarker(activeProfile.id, favoriteToRemove);
      console.log(`Backend add: ${favoriteToAdd}`);
      const updatedProfile = await addFavoriteBiomarker(activeProfile.id, favoriteToAdd);
      
      // Update state with the final list from the backend
      const newFavorites = updatedProfile.favorite_biomarkers || [];
      setFavoriteNames(newFavorites);
      // --- Trigger grid recalculation ---
      calculateAndSetGridData(newFavorites);
      // --- End trigger ---
      
      // Close the modal
      handleCloseReplaceModal();
      
      // Show success feedback
      setSnackbarMessage(`Replaced ${favoriteToRemove} with ${favoriteToAdd} in favorites.`);
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
      
    } catch (err) {
       console.error(`Error replacing favorite ${favoriteToRemove} with ${favoriteToAdd}:`, err);
       setSnackbarMessage('Failed to replace favorite.');
       setSnackbarSeverity('error');
       setSnackbarOpen(true);
       // Close modal even on error? Or keep it open? Closing for now.
       handleCloseReplaceModal();
    } finally {
       // setIsLoading(false);
    }
    // NOTE: The closing brace below was incorrectly placed here in the previous step. 
    // It belongs after the handleFavoriteOrderChange function.
  }; 
  
  // Handler for when the favorite order changes via drag-and-drop
  const handleFavoriteOrderChange = async (orderedNames: string[]) => {
    if (!activeProfile?.id) return;
    
    console.log(`Favorite order changed, attempting to save new order for profile ${activeProfile.id}:`, orderedNames);
    
    // --- REMOVED OPTIMISTIC UPDATE ---
    // setFavoriteNames(orderedNames); 
    
    try {
      // Call the backend API to persist the new order
      const updatedProfile = await updateFavoriteOrder(activeProfile.id, orderedNames);
      console.log(`Successfully saved new favorite order for profile ${activeProfile.id}`);
      
      // Update state with the confirmed order from the backend
      const newFavorites = updatedProfile.favorite_biomarkers || [];
      setFavoriteNames(newFavorites);
      // --- Trigger grid recalculation ---
      calculateAndSetGridData(newFavorites);
      // --- End trigger ---

      // Show success feedback (optional, could be too noisy)
      // setSnackbarMessage('Favorite order saved.');
      // setSnackbarSeverity('success');
      // setSnackbarOpen(true);
      
    } catch (err) {
      console.error(`Error saving favorite order for profile ${activeProfile.id}:`, err);
      // Show error feedback
      setSnackbarMessage('Failed to save favorite order. Please try again.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
      
      // Revert optimistic update if save fails? 
      // No optimistic update to revert, but maybe refetch profile to be safe?
      // For now, just show error. The state might be inconsistent until next refresh.
    }
  }; // Correct closing brace for handleFavoriteOrderChange

  // --- End Favorite Checkers/Handlers ---

  // Handle generate health summary
  const handleGenerateHealthSummary = async () => {
    if (!activeProfile?.id) return;
    
    // Show snackbar
    setSnackbarMessage('Generating AI health summary...');
    setSnackbarSeverity('info');
    setSnackbarOpen(true);
    
    setIsSummaryGenerating(true);
    
    try {
      // Call the generate summary API
      const updatedProfile = await generateHealthSummary(activeProfile.id);
      
      // Update the active profile with the new summary
      setActiveProfileById(activeProfile.id); // This will fetch the updated profile
      
      // Show success message
      setSnackbarMessage('AI health summary generation started! Check back in a minute to see your personalized summary.');
      setSnackbarSeverity('success');
      setSnackbarOpen(true);
    } catch (error) {
      console.error('Error generating health summary:', error);
      
      // Show error message
      setSnackbarMessage('Failed to generate AI health summary. Please try again later.');
      setSnackbarSeverity('error');
      setSnackbarOpen(true);
    } finally {
      setIsSummaryGenerating(false);
    }
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
  if (!profileLoading && !activeProfile && !fileId) {
    return (
      <Container maxWidth="lg">
        <Paper sx={{ p: 4, mt: 3, textAlign: 'center' }}>
          <Typography variant="h5" gutterBottom>
            Select a Profile to View Visualizations
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Choose a profile below to explore your biomarker data and health insights.
          </Typography>
          {profileListLoading ? (
            <CircularProgress />
          ) : profileListError ? (
            <Alert severity="error">{profileListError}</Alert>
          ) : availableProfiles.length > 0 ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
              <FormControl sx={{ m: 1, minWidth: 300 }}>
                <InputLabel id="profile-select-label">Select Profile</InputLabel>
                <Select
                  labelId="profile-select-label"
                  id="profile-select"
                  value=""
                  label="Select Profile"
                  onChange={handleProfileSelectChange}
                  sx={{ textAlign: 'left' }}
                >
                  {availableProfiles.map((profile) => (
                    <MenuItem key={profile.id} value={profile.id}>
                      {profile.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Typography variant="caption" color="text.secondary">
                You can manage your profiles and create new ones from the Profiles page
              </Typography>
              <Box sx={{ mt: 2 }}>
                <Button
                  component={Link}
                  to="/profiles"
                  variant="outlined"
                  startIcon={<PersonIcon />}
                  sx={{ mr: 2 }}
                >
                  Manage Profiles
                </Button>
                <Button
                  component={Link}
                  to="/upload"
                  variant="contained"
                  startIcon={<CloudUploadIcon />}
                >
                  Upload New Data
                </Button>
              </Box>
            </Box>
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
              <Alert severity="info" sx={{ maxWidth: 400 }}>
                No profiles found. Create a profile to get started with visualizations.
              </Alert>
              <Button
                component={Link}
                to="/profiles"
                variant="contained"
                startIcon={<PersonAddIcon />}
              >
                Create Your First Profile
              </Button>
            </Box>
          )}
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

      {/* Box for Profile Selector and History Button */}
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        {/* Profile Selector Dropdown - Render if profile is active */}
        {activeProfile && ( 
          <FormControl sx={{ minWidth: 200 }} size="small"> {/* Removed disabled prop for now */}
            <InputLabel id="profile-select-label">
              {profileListLoading ? "Loading..." : profileListError ? "Error" : "Viewing Profile"}
            </InputLabel>
            <Select
              labelId="profile-select-label"
              id="profile-select"
              value={activeProfile?.id || ''} // Use optional chaining and default to empty string
              label={profileListLoading ? "Loading..." : profileListError ? "Error" : "Viewing Profile"} // Match InputLabel
              onChange={handleProfileSelectChange}
              // Disabled state removed from FormControl, let Select handle internally if needed
            >
              {/* Handle loading state */}
              {profileListLoading && (
                <MenuItem disabled value="">
                  <CircularProgress size={20} sx={{ mr: 1 }} /> Loading...
                </MenuItem>
              )}
              {/* Handle error state */}
              {profileListError && !profileListLoading && (
                 <MenuItem disabled value="" sx={{ color: 'error.main' }}>Error loading profiles</MenuItem>
              )}
              {/* Handle success state (only map if not loading and no error) */}
              {!profileListLoading && !profileListError && availableProfiles.length > 0 && (
                availableProfiles.map((profile) => (
                  <MenuItem key={profile.id} value={profile.id}>
                    {profile.name}
                  </MenuItem>
                ))
              )}
              {/* Handle case where profiles loaded but list is empty */}
              {!profileListLoading && !profileListError && availableProfiles.length === 0 && (
                 <MenuItem disabled value="">No profiles found</MenuItem>
              )}
            </Select>
          </FormControl>
        )}
        {/* Placeholder if no active profile */}
        {!activeProfile && ( // Show placeholder only if no active profile
           <Box sx={{ minWidth: 200 }} /> 
        )}

        {/* History Button */}
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
            onToggleFavorite={handleToggleFavorite} // Used by star icon
            onDeleteFavorite={async (biomarkerName) => { // Make async for await
              // When we delete a favorite from the grid tile's 'x' button
              if (!activeProfile?.id) return;
            
              console.log(`Deleting favorite ${biomarkerName} via delete button`);
            
              // --- REMOVED OPTIMISTIC UPDATE ---
              // const originalFavoriteNames = [...favoriteNames]; 
              // const updatedFavoritesOptimistic = favoriteNames.filter(name => name !== biomarkerName);
              // setFavoriteNames(updatedFavoritesOptimistic);
            
              // Perform the backend update
              try {
                const updatedProfile = await removeFavoriteBiomarker(activeProfile.id, biomarkerName);
                console.log('Delete successful, updated favorites from backend:', updatedProfile.favorite_biomarkers);
                
                // Update favorites state from backend to ensure sync
                const newFavorites = updatedProfile.favorite_biomarkers || [];
                setFavoriteNames(newFavorites); 
                // --- Trigger grid recalculation ---
                calculateAndSetGridData(newFavorites);
                // --- End trigger ---
                
                setSnackbarMessage(`${biomarkerName} removed from favorites.`);
                setSnackbarSeverity('success');
                setSnackbarOpen(true);
              } catch (err) {
                console.error(`Error deleting favorite ${biomarkerName}:`, err);
                
                // Revert the optimistic update for favoriteNames (this triggers the useEffect)
                // No optimistic update to revert, just show error
                // setFavoriteNames(originalFavoriteNames); 
                
                // Snackbar message
                setSnackbarMessage('Failed to remove from favorites.');
                setSnackbarSeverity('error');
                setSnackbarOpen(true);
              }
            }}
            onAddClick={handleOpenAddModal}
            onOrderChange={handleFavoriteOrderChange} // Pass the order change handler
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
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={handleTabChange} 
          aria-label="biomarker visualization tabs"
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': { 
              minHeight: '72px',
              fontWeight: 500,
              transition: 'all 0.2s ease-in-out',
              opacity: 0.7,
            },
            '& .Mui-selected': {
              fontWeight: 700,
              opacity: 1,
              background: 'linear-gradient(to bottom, rgba(25, 118, 210, 0.1), transparent)',
              borderBottom: '3px solid',
              borderColor: 'primary.main',
            },
            '& .MuiTabs-indicator': {
              height: 3,
              borderRadius: '3px 3px 0 0',
            }
          }}
        >
          <Tab icon={<TableChartIcon />} label="Table View" />
          <Tab icon={<SmartToyIcon />} label="Smart Summary" />
          <Tab icon={<TimelineIcon />} label="Chart View" />
          <Tab icon={<CategoryIcon />} label="Categories" />
        </Tabs>
      </Box>

      {/* Table View */}
      <TabPanel value={activeTab} index={0}>
        <BiomarkerTable 
          biomarkers={biomarkers} 
          isLoading={biomarkerLoading} // Pass loading state
          error={error} // Pass error state
          onRefresh={handleRetry} // Pass refresh handler
          onExplainWithAI={handleExplainBiomarker}
          onDeleteBiomarker={handleDeleteBiomarkerRequest} // Pass delete handler
          onToggleFavorite={handleToggleFavorite} // Pass favorite toggle handler
          isFavoriteChecker={isBiomarkerFavorite} // Pass favorite checker function
          isFavoriteLimitReached={isFavoriteLimitReached} // Pass limit flag
          onReplaceFavoriteRequest={handleReplaceFavoriteRequest} // Pass replace request handler
          showSource={!fileId} // Show source if viewing overview (not specific file)
        />
      </TabPanel>

      {/* Smart Summary View - Redesigned */}
      <TabPanel value={activeTab} index={1}>
        <Box sx={{ p: 0 }}> {/* Removed outer Paper, using Box for padding control */}
          <Box sx={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            mb: 3,
            px: 1 // Add slight horizontal padding
          }}>
            <Typography variant="h5" fontWeight="500" sx={{ display: 'flex', alignItems: 'center' }}>
              <SmartToyIcon sx={{ mr: 1.5, color: theme.palette.primary.main }} />
              AI-Powered Health Analysis
            </Typography>
            {activeProfile && (
              <Button
                variant="contained" // Keep contained for primary action
                color="primary"
                startIcon={<UpdateIcon />}
                onClick={handleGenerateHealthSummary}
                disabled={isSummaryGenerating}
                size="medium" // Slightly larger button
                sx={{ 
                  borderRadius: '12px', // More rounded
                  boxShadow: 'none', // Remove default shadow for cleaner look
                  textTransform: 'none', // Keep text normal case
                  fontWeight: 600,
                  px: 2.5, // More padding
                  py: 1,
                  '&:hover': {
                    boxShadow: 'none', // Keep shadow off on hover
                  }
                }}
              >
                {isSummaryGenerating ? 'Generating...' : 'Generate Smart Summary'}
              </Button>
            )}
          </Box>
          
          {/* Redesigned Top Cards */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={6}>
              <Paper 
                variant="outlined" // Use outlined variant for subtle look
                sx={{ 
                  p: 3, // Increased padding
                  // Use theme background paper color
                  bgcolor: theme.palette.background.paper, 
                  borderRadius: 3, // More rounded corners
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  textAlign: 'center',
                  border: `1px solid ${theme.palette.divider}` // Subtle border
                }}
              >
                <Typography 
                  variant="h3" 
                  fontWeight="bold" 
                  gutterBottom 
                  // Use subtle warning color for abnormal count
                  color={theme.palette.warning.main} 
                >
                  {biomarkers.filter(b => b.isAbnormal).length}
                </Typography>
                <Typography variant="subtitle1" sx={{ mb: 1, color: 'text.secondary' }}>
                  Abnormal Values
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  out of {biomarkers.length} total biomarkers
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper 
                variant="outlined" // Use outlined variant
                sx={{ 
                  p: 3, // Increased padding
                  bgcolor: theme.palette.background.paper,
                  borderRadius: 3, // More rounded corners
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  alignItems: 'center',
                  textAlign: 'center',
                  border: `1px solid ${theme.palette.divider}` // Subtle border
                }}
              >
                <Typography variant="h3" fontWeight="bold" gutterBottom color="text.primary">
                  {new Set(biomarkers.map(b => b.category)).size}
                </Typography>
                <Typography variant="subtitle1" sx={{ mb: 1, color: 'text.secondary' }}>
                  Categories
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  different types of biomarkers analyzed
                </Typography>
              </Paper>
            </Grid>
          </Grid>

          {/* AI Health Summary Section - Redesigned */}
          {activeProfile && (
            <Paper
              variant="outlined" // Use outlined variant
              sx={{
                p: { xs: 2, md: 3 }, // Responsive padding
                borderRadius: 3, // Match card rounding
                bgcolor: theme.palette.background.default, // Slightly different background
                border: `1px solid ${theme.palette.divider}`,
                mb: 3 // Increased bottom margin
              }}
            >
              <Box sx={{ 
                display: 'flex', 
                flexDirection: 'column',
                gap: 2.5 // Increased gap
              }}>
                {/* Header */}
                <Box sx={{
                  display: 'flex',
                  alignItems: 'center',
                  pb: 2,
                  borderBottom: `1px solid ${theme.palette.divider}`
                }}>
                  <PsychologyIcon fontSize="medium" sx={{ mr: 1.5, color: theme.palette.primary.main }} />
                  <Box>
                    <Typography variant="h6" fontWeight="500" color="text.primary">
                      Smart Health Summary
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {activeProfile.summary_last_updated 
                        ? `Last updated: ${new Date(activeProfile.summary_last_updated).toLocaleString()}` 
                        : 'Not generated yet'}
                    </Typography>
                  </Box>
                </Box>
                
                {/* Summary Content or Placeholder */}
                {activeProfile.health_summary ? (
                  <Box sx={{ 
                    p: 0, // Remove extra padding/border from inner box
                    borderRadius: 0, 
                    bgcolor: 'transparent', // Make inner box transparent
                    border: 'none',
                    boxShadow: 'none'
                  }}>
                    <Typography 
                      variant="body1" 
                      color="text.primary" // Use primary text color
                      sx={{ 
                        whiteSpace: 'pre-wrap',
                        lineHeight: 1.7, // Slightly adjusted line height
                        fontWeight: 400,
                        fontSize: '0.95rem', // Slightly smaller font for reading
                        letterSpacing: '0.01em',
                      }}
                    >
                      {activeProfile.health_summary} 
                    </Typography>
                  </Box>
                ) : (
                  // Placeholder styling
                  <Box sx={{ 
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    p: { xs: 3, md: 4 }, // Responsive padding
                    borderRadius: 2, // Slightly rounded placeholder
                    bgcolor: theme.palette.background.paper, // Use paper background
                    border: `1px dashed ${theme.palette.divider}`, // Dashed border
                    textAlign: 'center'
                  }}>
                    <SmartToyIcon sx={{ fontSize: 40, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="body1" color="text.primary" paragraph fontWeight="medium">
                      No AI health summary available yet.
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Click the "Generate Smart Summary" button above to create one.
                    </Typography>
                  </Box>
                )}
              </Box>
              
              {/* Regenerate Button (only if summary exists) */}
              {activeProfile.health_summary && (
                <Box sx={{ mt: 2.5, display: 'flex', justifyContent: 'flex-end' }}>
                  <Button
                    size="small"
                    startIcon={<UpdateIcon />}
                    onClick={handleGenerateHealthSummary}
                    disabled={isSummaryGenerating}
                    variant="text" // Use text variant for less emphasis
                    sx={{ textTransform: 'none', color: 'text.secondary' }}
                  >
                    {isSummaryGenerating ? 'Regenerating...' : 'Regenerate Summary'}
                  </Button>
                </Box>
              )}
            </Paper>
          )}
          
          {/* Additional Information / Disclaimer Box - Redesigned */}
          <Paper 
            variant="outlined" // Use outlined variant
            sx={{ 
              p: 2.5, // Consistent padding
              bgcolor: theme.palette.background.paper, // Use paper background
              borderRadius: 3, // Match card rounding
              border: `1px solid ${theme.palette.divider}` // Subtle border
            }}
          >
            <Typography variant="subtitle2" fontWeight="500" color="text.secondary">
              About Smart Health Summary
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }} color="text.secondary">
              This AI-powered analysis examines your biomarker data to identify patterns, trends, and notable values.
              The summary is generated based solely on your uploaded lab results and is not medical advice.
              Always consult with healthcare professionals for proper interpretation of your test results.
            </Typography>
          </Paper>
        </Box>
      </TabPanel>

      {/* Chart View */}
      <TabPanel value={activeTab} index={2}>
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
      <TabPanel value={activeTab} index={3}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Biomarkers by Category
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Category view will be implemented here
          </Typography>
        </Paper>
      </TabPanel>

      {/* AI Explanation Modal - Re-enabled */}
       {/* AI Explanation Modal - Pass the whole biomarker object */}
       {currentBiomarker && (
        <ExplanationModal
          open={explanationModalOpen}
          onClose={handleCloseExplanationModal}
          biomarker={currentBiomarker} // Pass the entire object
          loading={explanationLoading}
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

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleCloseDeleteDialog}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">Confirm Deletion</DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            Are you sure you want to permanently delete this biomarker entry? This action cannot be undone.
          </DialogContentText>
          {deleteLoading && <CircularProgress size={24} sx={{ mt: 2 }} />}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDeleteDialog} disabled={deleteLoading}>
            Cancel
          </Button>
          <Button 
            onClick={handleConfirmDelete} 
            color="error" 
            autoFocus 
            disabled={deleteLoading}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>

      {/* Feedback Snackbar */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbarSeverity} sx={{ width: '100%' }}>
          {snackbarMessage}
        </Alert>
      </Snackbar>
      
      {/* Replace Favorite Modal */}
      {activeProfile && (
        <ReplaceFavoriteModal
          open={replaceModalOpen}
          onClose={handleCloseReplaceModal}
          biomarkerToAdd={biomarkerToReplaceWith}
          currentFavorites={favoriteNames} // Pass the current list of favorite names
          onConfirmReplace={handleConfirmReplace}
          // Pass isLoading if you add loading state to the replace action
        />
      )}

    </Container>
  );
};

export default VisualizationPage;
