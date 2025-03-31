import React, { useState, useEffect, useMemo } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  CircularProgress,
  Alert,
  Grid,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Button,
  SelectChangeEvent,
  TextFieldProps // Import TextFieldProps
} from '@mui/material';
import { useParams } from 'react-router-dom';
// Remove DatePicker and related imports
import { format, parseISO, isValid, startOfDay, endOfDay } from 'date-fns';

// Adjust BiomarkerTable import if Biomarker type is defined elsewhere
import BiomarkerTable from '../components/BiomarkerTable';
import { getAllBiomarkers, getBiomarkerCategories, getBiomarkerExplanation } from '../services/api'; // Added getBiomarkerExplanation
import { ApiError, BiomarkerExplanation } from '../types/api'; // Added BiomarkerExplanation type
import { Biomarker } from '../types/pdf'; // Ensure Biomarker type is imported
import ExplanationModal from '../components/ExplanationModal'; // Added ExplanationModal import

const BiomarkerHistoryPage: React.FC = () => {
  const { profileId } = useParams<{ profileId: string }>();
  const [biomarkers, setBiomarkers] = useState<Biomarker[]>([]);
  const [filteredBiomarkers, setFilteredBiomarkers] = useState<Biomarker[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<string[]>(['All']);
  const [reportNames, setReportNames] = useState<string[]>(['All']);

  // Filter states - Remove start and end dates
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedStatus, setSelectedStatus] = useState<string>('All'); // 'All', 'Normal', 'Abnormal'
  const [selectedReport, setSelectedReport] = useState<string>('All');

  // State for AI explanation modal (copied from VisualizationPage)
  const [explanationModalOpen, setExplanationModalOpen] = useState<boolean>(false);
  const [currentBiomarker, setCurrentBiomarker] = useState<Biomarker | null>(null);
  const [explanationLoading, setExplanationLoading] = useState<boolean>(false);
  const [explanationError, setExplanationError] = useState<string | null>(null);
  const [explanation, setExplanation] = useState<BiomarkerExplanation | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!profileId) {
        setError('Profile ID is missing from the URL.');
        setIsLoading(false);
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        // Fetch all biomarkers for the profile
        const fetchedBiomarkers = await getAllBiomarkers({ profile_id: profileId, limit: 1000 }); // Fetch a large limit initially
        setBiomarkers(fetchedBiomarkers);

        // Extract unique categories and report names for filters
        const uniqueCategories = ['All', ...new Set(fetchedBiomarkers.map(b => b.category || 'Uncategorized').filter(Boolean))];
        setCategories(uniqueCategories);

        const uniqueReportNames = ['All', ...new Set(fetchedBiomarkers.map(b => b.fileName || 'Unknown Report').filter(Boolean))];
        setReportNames(uniqueReportNames);

        // Fetch all categories from API to ensure complete list
        try {
          const allApiCategories = await getBiomarkerCategories();
          setCategories(prev => ['All', ...new Set([...prev.slice(1), ...allApiCategories])].sort((a, b) => a === 'All' ? -1 : b === 'All' ? 1 : a.localeCompare(b)));
        } catch (catError) {
          console.warn('Could not fetch all categories from API:', catError);
        }

      } catch (err) {
        console.error('Error fetching biomarker history:', err);
        const apiError = err as ApiError;
        setError(apiError.message || 'Failed to load biomarker history.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [profileId]);

  // Apply filters whenever biomarkers or filter states change
  useEffect(() => {
    let tempFiltered = [...biomarkers];

    // Remove Date Range filtering logic

    // Filter by Category
    if (selectedCategory !== 'All') {
      tempFiltered = tempFiltered.filter(b => (b.category || 'Uncategorized') === selectedCategory);
    }

    // Filter by Status
    if (selectedStatus !== 'All') {
      const isAbnormalFilter = selectedStatus === 'Abnormal';
      tempFiltered = tempFiltered.filter(b => b.isAbnormal === isAbnormalFilter);
    }

    // Filter by Report Name
    if (selectedReport !== 'All') {
      tempFiltered = tempFiltered.filter(b => (b.fileName || 'Unknown Report') === selectedReport);
    }

    setFilteredBiomarkers(tempFiltered);
  }, [biomarkers, selectedCategory, selectedStatus, selectedReport]); // Update dependencies

  const handleRetry = () => {
     // Re-fetch data
     if (profileId) {
        const fetchData = async () => {
            setIsLoading(true);
            setError(null);
            try {
                const fetchedBiomarkers = await getAllBiomarkers({ profile_id: profileId, limit: 1000 });
                setBiomarkers(fetchedBiomarkers);
                 // Re-populate filters
                const uniqueCategories = ['All', ...new Set(fetchedBiomarkers.map(b => b.category || 'Uncategorized').filter(Boolean))];
                setCategories(uniqueCategories);
                const uniqueReportNames = ['All', ...new Set(fetchedBiomarkers.map(b => b.fileName || 'Unknown Report').filter(Boolean))];
                setReportNames(uniqueReportNames);
            } catch (err) {
                 console.error('Error fetching biomarker history:', err);
                 const apiError = err as ApiError;
                 setError(apiError.message || 'Failed to load biomarker history.');
            } finally {
                setIsLoading(false);
            }
        };
        fetchData();
     }
  };

  // Function to handle opening the explanation modal (copied from VisualizationPage)
  const handleExplainBiomarker = async (biomarker: Biomarker) => {
    console.log('=== EXPLAIN BIOMARKER FUNCTION CALLED (History Page) ===');
    console.log('Biomarker data received:', biomarker);

    if (!biomarker || !biomarker.name) {
      console.error('Invalid biomarker data received:', biomarker);
      setExplanationError('Cannot explain this biomarker: invalid data');
      return;
    }

    setCurrentBiomarker(biomarker);
    setExplanationModalOpen(true);
    setExplanationLoading(true);
    setExplanationError(null);
    setExplanation(null);

    try {
      const isAbnormal = biomarker.isAbnormal !== undefined
        ? biomarker.isAbnormal
        : (typeof biomarker.value === 'number' && typeof biomarker.reference_range_low === 'number' && typeof biomarker.reference_range_high === 'number')
          ? (biomarker.value < biomarker.reference_range_low || biomarker.value > biomarker.reference_range_high)
          : false;

      const referenceRange = biomarker.referenceRange ??
        (typeof biomarker.reference_range_low === 'number' && typeof biomarker.reference_range_high === 'number'
          ? `${biomarker.reference_range_low}-${biomarker.reference_range_high}`
          : "Not available");

      console.log('Calculated parameters (History Page):');
      console.log('- isAbnormal:', isAbnormal);
      console.log('- referenceRange:', referenceRange);

      const result = await getBiomarkerExplanation(
        biomarker.id,
        biomarker.name,
        biomarker.value,
        biomarker.unit,
        referenceRange,
        isAbnormal
      );

      console.log('Received explanation result (History Page):', result);

      if (!result || !result.general_explanation || !result.specific_explanation) {
        console.error('Invalid explanation data received:', result);
        setExplanationError('Invalid explanation data received. Please try again.');
        return;
      }

      setExplanation(result);
    } catch (error) {
      console.error('=== ERROR IN EXPLAIN BIOMARKER HANDLER (History Page) ===');
      console.error('Error details:', error);
      let errorMessage = 'An unexpected error occurred. Please try again later.';
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'object' && error !== null && 'message' in error) {
        errorMessage = String(error.message);
      }
      setExplanationError(errorMessage);
    } finally {
      setExplanationLoading(false);
    }
  };

  // Handle closing the explanation modal (copied from VisualizationPage)
  const handleCloseExplanationModal = () => {
    setExplanationModalOpen(false);
  };


  return (
    // Remove LocalizationProvider if no longer needed
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Biomarker History {profileId ? `for Profile ${profileId.substring(0, 8)}...` : ''}
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} action={
             <Button color="inherit" size="small" onClick={handleRetry}>Retry</Button>
          }>
            {error}
          </Alert>
        )}

        <Paper sx={{ p: 2, mb: 3 }}>
          <Grid container spacing={2} alignItems="center">
            {/* Remove DatePicker Grid items */}
            {/* Adjust grid sizing for remaining items */}
            <Grid item xs={6} sm={4} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Category</InputLabel>
                <Select
                  value={selectedCategory}
                  label="Category"
                  onChange={(e: SelectChangeEvent<string>) => setSelectedCategory(e.target.value)}
                >
                  {categories.map(cat => <MenuItem key={cat} value={cat}>{cat}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6} sm={4} md={3}>
              <FormControl fullWidth size="small">
                <InputLabel>Status</InputLabel>
                <Select
                  value={selectedStatus}
                  label="Status"
                  onChange={(e: SelectChangeEvent<string>) => setSelectedStatus(e.target.value)}
                >
                  <MenuItem value="All">All</MenuItem>
                  <MenuItem value="Normal">Normal</MenuItem>
                  <MenuItem value="Abnormal">Abnormal</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} sm={4} md={6}>
              <FormControl fullWidth size="small">
                <InputLabel>Report</InputLabel>
                <Select
                  value={selectedReport}
                  label="Report"
                  onChange={(e: SelectChangeEvent<string>) => setSelectedReport(e.target.value)}
                  MenuProps={{ PaperProps: { style: { maxHeight: 300 } } }} // Limit dropdown height
                >
                  {reportNames.map(name => <MenuItem key={name} value={name}>{name}</MenuItem>)}
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </Paper>

        {isLoading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
            <CircularProgress />
          </Box>
        ) : (
          <BiomarkerTable
            biomarkers={filteredBiomarkers}
            isLoading={isLoading} // Pass loading state
            error={error} // Pass error state
            onRefresh={handleRetry} // Pass retry handler
            showSource={true} // Correct prop name: Indicate this is the history view
            onExplainWithAI={handleExplainBiomarker} // Pass the handler
          />
        )}

        {/* AI Explanation Modal */}
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
      </Container>
    // Remove LocalizationProvider if no longer needed
  );
};

export default BiomarkerHistoryPage;
