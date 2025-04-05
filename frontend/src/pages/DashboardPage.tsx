import React, { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import { 
  Box, 
  Container, 
  Typography, 
  Grid, 
  Paper, 
  CircularProgress, 
  Alert, 
  Button, 
  Stack,
  Collapse, // Import Collapse
  // IconButton removed - unused
  // styled removed - unused
  alpha // Import alpha for opacity
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'; // Import ExpandMore icon
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useProfile } from '../contexts/ProfileContext'; // Import the profile context hook
// Removing problematic Health Score component import for now - Re-add if path/component is confirmed
// import HealthScoreOverview from '../components/HealthScoreOverview.tsx';
// import Dashboard from '../components/Dashboard.tsx'; 
import { getAllBiomarkers } from '../services/api'; // Import biomarker service
import { Biomarker } from '../types/pdf'; // Import Biomarker type
// import TrendIndicator from '../components/TrendIndicator'; // Could use this later if available and suitable
// TODO: Import service to fetch last report date when available

// Removed unused ExpandMore styled component definition


const DashboardPage: React.FC = () => {
  const { activeProfile, loading: profileLoading, error: profileError } = useProfile();
  const [lastReportDate, setLastReportDate] = useState<string | null>(null);
  const [loadingDate, setLoadingDate] = useState<boolean>(false);
  const [summaryExpanded, setSummaryExpanded] = useState(false); // State for summary collapse
  // Store the latest two values for trend calculation
  const [favoriteBiomarkerData, setFavoriteBiomarkerData] = useState<Record<string, { latest: Biomarker | null; previous: Biomarker | null }>>({});
  const [loadingBiomarkers, setLoadingBiomarkers] = useState<boolean>(false);
  const [biomarkerError, setBiomarkerError] = useState<string | null>(null);

  useEffect(() => {
    // Clear data when profile changes or becomes null
    if (!activeProfile) {
      setLastReportDate(null);
      setFavoriteBiomarkerData({});
      setBiomarkerError(null);
      setLoadingBiomarkers(false);
      setLoadingDate(false); // Ensure loading state is reset
      return; 
    }

    // Fetch all biomarkers for the profile to find favorites' latest values AND last report date
    const fetchDashboardData = async () => {
      // Only proceed if we have profile ID and favorites list
      if (!activeProfile?.id || !activeProfile.favorite_biomarkers) {
         setFavoriteBiomarkerData({}); // Clear data if no favorites
         setLastReportDate(null); // Clear date
         return;
      }

      setLoadingBiomarkers(true);
      setLoadingDate(true); // Also loading date now
      setBiomarkerError(null);
      setFavoriteBiomarkerData({}); // Clear previous data
      setLastReportDate(null); // Clear previous date

      try {
        const allBiomarkers = await getAllBiomarkers({ profile_id: activeProfile.id });

        // Find the latest report date from all fetched biomarkers
        let latestDateFound: Date | null = null;
        allBiomarkers.forEach(b => {
          // Use reportDate first, fallback to date, ensure it's valid before creating Date object
          const dateString = b.reportDate || b.date; 
          if (dateString) {
             try {
                const currentDate = new Date(dateString);
                // Check if date is valid before comparing
                if (!isNaN(currentDate.getTime())) { 
                   if (!latestDateFound || currentDate > latestDateFound) {
                     latestDateFound = currentDate;
                   }
                }
             } catch (e) {
                console.warn(`Invalid date string encountered: ${dateString}`);
             }
          }
        });
        // Fix: Explicitly cast to Date after truthy check
        setLastReportDate(latestDateFound ? (latestDateFound as Date).toLocaleDateString() : null);


        // Process favorites only if there are any
        if (activeProfile.favorite_biomarkers.length > 0) {
           const latestFavoritesData: Record<string, { latest: Biomarker | null; previous: Biomarker | null }> = {};
           activeProfile.favorite_biomarkers.forEach(favName => {
             const matchingBiomarkers = allBiomarkers
               .filter(b => b.name === favName && typeof b.value === 'number') // Only consider numeric values for trend
              // Fix: Handle potentially undefined dates in sort
              .sort((a, b) => {
                const dateA = a.date ? new Date(a.date).getTime() : 0;
                const dateB = b.date ? new Date(b.date).getTime() : 0;
                 return dateB - dateA; // Sort descending by date
               });
               
             latestFavoritesData[favName] = {
               latest: matchingBiomarkers.length > 0 ? matchingBiomarkers[0] : null,
               previous: matchingBiomarkers.length > 1 ? matchingBiomarkers[1] : null,
             };
           });
           setFavoriteBiomarkerData(latestFavoritesData);
        } else {
             setFavoriteBiomarkerData({}); // Ensure it's empty if no favorites
        } // End of processing favorites block

       } catch (err) { // Catch block for the try fetching biomarkers
         console.error("Error fetching dashboard data:", err);
         setBiomarkerError("Could not load dashboard data.");
         setLastReportDate(null); // Clear date on error
         setFavoriteBiomarkerData({}); // Clear favorites on error
       } finally { // Finally block for the try fetching biomarkers
         setLoadingBiomarkers(false);
         setLoadingDate(false); // Finish loading date
       }
    }; // End of fetchDashboardData function

    fetchDashboardData(); // Call the async function

  }, [activeProfile]);


  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Health Dashboard {activeProfile ? `for ${activeProfile.name}` : ''}
      </Typography>

      {profileLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Loading profile...</Typography>
        </Box>
      )}
      {profileError && (
        <Alert severity="error" sx={{ mb: 3 }}>{profileError}</Alert>
      )}
      {!activeProfile && !profileLoading && (
         <Alert severity="info" sx={{ mb: 3 }}>Please select a profile to view the dashboard.</Alert>
      )}

      {/* Disable grid content if no profile is active */}
      <Grid container spacing={3} sx={{ filter: !activeProfile ? 'blur(2px)' : 'none', pointerEvents: !activeProfile ? 'none' : 'auto' }}>
        {/* Row 1: Key Metric Cards */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 180 }}>
            <Typography variant="h6" color="primary" gutterBottom>
              Health Score
            </Typography>
            {activeProfile ? (
              // Placeholder for Health Score
              <Typography variant="h3" component="div" sx={{ mt: 2 }}>
                {/* Display a static or random number for now */}
                {Math.floor(Math.random() * 31) + 60} 
                <Typography variant="caption" display="block">/ 100</Typography>
              </Typography>
              // <HealthScoreOverview profileId={activeProfile.id} /> // Keep commented until component path/type is fixed
            ) : (
              <Typography variant="body2">Select a profile</Typography>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 180 }}>
            <Typography variant="h6" color="primary" gutterBottom>
              Key Biomarkers
            </Typography>
            {activeProfile ? (
              loadingBiomarkers ? (
                 <CircularProgress size={20} />
              ) : biomarkerError ? (
                 <Typography variant="body2" color="error">{biomarkerError}</Typography>
              ) : activeProfile.favorite_biomarkers && activeProfile.favorite_biomarkers.length > 0 ? (
                 <Box sx={{ overflowY: 'auto', maxHeight: '100px' }}> {/* Basic scroll */}
                   <ul style={{ paddingLeft: '20px', margin: 0, listStyle: 'none' }}>
                     {activeProfile.favorite_biomarkers.map((favName: string) => { // Add type annotation
                       const data = favoriteBiomarkerData[favName];
                       let trendIcon = null;
                       
                       // Check if data and both latest/previous values exist and are numbers
                       if (data?.latest?.value != null && data?.previous?.value != null && 
                           typeof data.latest.value === 'number' && typeof data.previous.value === 'number') {
                           
                         if (data.latest.value > data.previous.value) {
                           trendIcon = <ArrowUpwardIcon fontSize="inherit" sx={{ color: 'error.main', verticalAlign: 'middle', ml: 0.5 }} />;
                         } else if (data.latest.value < data.previous.value) {
                           trendIcon = <ArrowDownwardIcon fontSize="inherit" sx={{ color: 'success.main', verticalAlign: 'middle', ml: 0.5 }} />;
                         } else {
                           trendIcon = <ArrowForwardIcon fontSize="inherit" sx={{ color: 'text.secondary', verticalAlign: 'middle', ml: 0.5 }} />;
                         }
                       } else if (data?.latest && !data?.previous) {
                         // Optional: Indicate if it's the first data point (e.g., with a different icon or no icon)
                         // trendIcon = <FiberNewIcon fontSize="inherit" sx={{ color: 'info.main', verticalAlign: 'middle', ml: 0.5 }} />; 
                       }

                       return (
                         <li key={favName}>
                           <Typography variant="body2" component="span">
                             {favName}: {data?.latest ? `${data.latest.value} ${data.latest.unit || ''}` : 'No data'}
                           </Typography>
                           {trendIcon}
                         </li>
                       ); // End of return statement for map
                     })}
                   </ul>
                 </Box>
              ) : (
                 <Typography variant="body2">No favorite biomarkers set.</Typography>
              )
            ) : (
              <Typography variant="body2">Select a profile</Typography>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', height: 180 }}>
            <Typography variant="h6" color="primary" gutterBottom>
              Last Report
            </Typography>
            {activeProfile ? (
              loadingDate ? (
                <CircularProgress size={20} />
              ) : lastReportDate ? (
                 <Typography variant="h5">{lastReportDate}</Typography>
              ) : (
                 <Typography variant="body2">No reports found.</Typography>
              )
            ) : (
              <Typography variant="body2">Select a profile</Typography>
            )}
          </Paper>
        </Grid>
        
        {/* Row 2: Category Status & AI Summary */}
        <Grid item xs={12} md={6}>
           <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
             <Typography variant="h6" color="primary" gutterBottom>
               Category Status
             </Typography>
             {/* TODO: Implement category status overview */}
             <Typography variant="body2">Category status coming soon...</Typography>
           </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
           <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column' }}>
             <Box sx={{ 
               display: 'flex', 
               alignItems: 'center',
               justifyContent: 'space-between',
               mb: 2
             }}>
               <Typography variant="h6" color="primary">
                 AI Health Summary
               </Typography>
               <Button 
                 component={RouterLink}
                 to="/visualization?tab=1"
                 size="small"
                 endIcon={<ArrowForwardIcon fontSize="small" />}
                 sx={{ textTransform: 'none' }}
               >
                 Full View
               </Button>
             </Box>
             
             {activeProfile?.health_summary ? (
               <>
                 {/* Summary preview - always visible */}
                 <Box sx={{ 
                   mb: 1,
                   p: 1.5,
                   bgcolor: (theme) => alpha(theme.palette.primary.main, 0.05),
                   borderRadius: 2,
                   border: (theme) => `1px solid ${alpha(theme.palette.primary.main, 0.1)}`
                 }}>
                   {/* Extract and display the first paragraph or sentence as a preview */}
                   <Typography 
                     variant="body2" 
                     color="text.primary"
                     sx={{ 
                       fontWeight: 500,
                       lineHeight: 1.6,
                       display: '-webkit-box',
                       WebkitLineClamp: summaryExpanded ? 'unset' : 3,
                       WebkitBoxOrient: 'vertical',
                       overflow: 'hidden',
                       textOverflow: 'ellipsis',
                       position: 'relative',
                       pr: summaryExpanded ? 0 : 2
                     }}
                   >
                     {activeProfile.health_summary.split('\n\n')[0]}
                   </Typography>
                 </Box>
                 
                 {/* Expandable content for more details */}
                 <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                   <Typography 
                     variant="body2" 
                     color="text.secondary" 
                     sx={{ fontSize: '0.8rem' }}
                   >
                     {activeProfile.summary_last_updated && 
                       `Updated: ${new Date(activeProfile.summary_last_updated).toLocaleDateString()}`}
                   </Typography>
                   <Button
                     onClick={() => setSummaryExpanded(!summaryExpanded)}
                     size="small"
                     endIcon={
                       <ExpandMoreIcon 
                         sx={{ 
                           transform: summaryExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                           transition: 'transform 0.3s'
                         }} 
                       />
                     }
                     sx={{ textTransform: 'none' }}
                   >
                     {summaryExpanded ? 'Show Less' : 'Read More'}
                   </Button>
                 </Box>
                 
                 <Collapse in={summaryExpanded} timeout="auto" unmountOnExit>
                   <Box sx={{ mt: 2 }}>
                     {/* Display the rest of the paragraphs */}
                     {activeProfile.health_summary.split('\n\n')
                       .slice(1) // Skip the first paragraph which is already shown
                       .map((paragraph, index) => (
                         <Typography 
                           key={index} 
                           variant="body2" 
                           paragraph 
                           sx={{ 
                             whiteSpace: 'pre-wrap',
                             mt: 1,
                             color: 'text.primary'
                           }}
                         >
                           {paragraph}
                         </Typography>
                       ))}
                   </Box>
                 </Collapse>
               </>
             ) : (
               <Box sx={{ 
                 display: 'flex', 
                 flexDirection: 'column', 
                 alignItems: 'center',
                 justifyContent: 'center',
                 p: 2,
                 minHeight: 100,
                 bgcolor: (theme) => alpha(theme.palette.background.default, 0.6),
                 borderRadius: 2,
                 border: '1px dashed',
                 borderColor: 'divider'
               }}>
                 <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 1.5 }}>
                   No AI summary available yet
                 </Typography>
                 <Button
                   component={RouterLink}
                   to="/visualization?tab=1"
                   size="small"
                   variant="outlined"
                   sx={{ textTransform: 'none' }}
                 >
                   Generate Summary
                 </Button>
               </Box>
             )}
           </Paper>
        </Grid>
        
        {/* Row 3: Action Buttons */}
        <Grid item xs={12}>
           <Paper sx={{ p: 2 }}>
             <Typography variant="h6" color="primary" gutterBottom>
               Quick Actions
             </Typography>
             <Stack direction="row" spacing={2} sx={{ mt: 2, flexWrap: 'wrap' }}>
               <Button 
                 variant="contained" 
                 component={RouterLink} 
                 to="/visualization" 
                 disabled={!activeProfile}
               >
                 View Visualizations
               </Button>
               <Button 
                 variant="outlined" 
                 component={RouterLink} 
                 to={activeProfile ? `/profile/${activeProfile.id}/history` : '#'} 
                 disabled={!activeProfile}
               >
                 View Full History
               </Button>
                <Button 
                 variant="outlined" 
                 component={RouterLink} 
                 to="/profiles" // Assuming favorites are managed within profile or visualization page
                 disabled={!activeProfile} 
               >
                 Manage Favorites
               </Button>
               <Button 
                 variant="contained" 
                 color="secondary" 
                 component={RouterLink} 
                 to="/upload"
                 disabled={!activeProfile} // Might allow upload even without profile? TBD
               >
                 Upload New Report
               </Button>
             </Stack>
           </Paper>
        </Grid>

      </Grid>
    </Container>
  );
};

export default DashboardPage;
