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
  Collapse,
  alpha
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useProfile } from '../contexts/ProfileContext';
// import HealthScoreOverview from '../components/HealthScoreOverview.tsx'; // Keep commented
import { getAllBiomarkers } from '../services/api';
import { Biomarker } from '../types/pdf';

const DashboardPage: React.FC = () => {
  const { activeProfile, loading: profileLoading, error: profileError } = useProfile();
  const [lastReportDate, setLastReportDate] = useState<string | null>(null);
  const [loadingDate, setLoadingDate] = useState<boolean>(false);
  const [summaryExpanded, setSummaryExpanded] = useState(false);
  const [favoriteBiomarkerData, setFavoriteBiomarkerData] = useState<Record<string, { latest: Biomarker | null; previous: Biomarker | null }>>({});
  const [loadingBiomarkers, setLoadingBiomarkers] = useState<boolean>(false);
  const [biomarkerError, setBiomarkerError] = useState<string | null>(null);

  useEffect(() => {
    // Clear data if no active profile
    if (!activeProfile) {
      setLastReportDate(null);
      setFavoriteBiomarkerData({});
      setBiomarkerError(null);
      setLoadingBiomarkers(false);
      setLoadingDate(false);
      return;
    }

    // Fetch data when activeProfile is available
    const fetchDashboardData = async () => {
      if (!activeProfile?.id) return; // Guard against missing ID

      setLoadingBiomarkers(true);
      setLoadingDate(true);
      setBiomarkerError(null);
      setFavoriteBiomarkerData({});
      setLastReportDate(null);

      try {
        const allBiomarkers = await getAllBiomarkers({ profile_id: activeProfile.id });

        // Find the latest report date
        let latestDateFound: Date | null = null;
        allBiomarkers.forEach(b => {
          const dateString = b.reportDate || b.date;
          if (dateString) {
            try {
              const currentDate = new Date(dateString);
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
        // Correctly handle Date | null type using if statement with explicit type check
        let formattedDate: string | null = null;
        if (latestDateFound instanceof Date) { // Explicitly check if it's a Date object
          formattedDate = latestDateFound.toLocaleDateString();
        }
        setLastReportDate(formattedDate);

        // Process favorites
        if (activeProfile.favorite_biomarkers && activeProfile.favorite_biomarkers.length > 0) {
          const latestFavoritesData: Record<string, { latest: Biomarker | null; previous: Biomarker | null }> = {};
          activeProfile.favorite_biomarkers.forEach(favName => {
            const matchingBiomarkers = allBiomarkers
              .filter(b => b.name === favName && typeof b.value === 'number')
              .sort((a, b) => {
                const dateA = a.date ? new Date(a.date).getTime() : 0;
                const dateB = b.date ? new Date(b.date).getTime() : 0;
                return dateB - dateA;
              });

            latestFavoritesData[favName] = {
              latest: matchingBiomarkers.length > 0 ? matchingBiomarkers[0] : null,
              previous: matchingBiomarkers.length > 1 ? matchingBiomarkers[1] : null,
            };
          });
          setFavoriteBiomarkerData(latestFavoritesData);
        } else {
          setFavoriteBiomarkerData({});
        }

      } catch (err) {
        console.error("Error fetching dashboard data:", err);
        setBiomarkerError("Could not load dashboard data.");
        setLastReportDate(null);
        setFavoriteBiomarkerData({});
      } finally {
        setLoadingBiomarkers(false);
        setLoadingDate(false);
      }
    };

    fetchDashboardData();

  }, [activeProfile]);

  // Helper to render trend icon
  const renderTrendIcon = (latestValue: number | null | undefined, previousValue: number | null | undefined) => {
    if (latestValue != null && previousValue != null && typeof latestValue === 'number' && typeof previousValue === 'number') {
      if (latestValue > previousValue) {
        return <ArrowUpwardIcon fontSize="inherit" sx={{ color: 'error.main', verticalAlign: 'middle', ml: 0.5 }} />;
      } else if (latestValue < previousValue) {
        return <ArrowDownwardIcon fontSize="inherit" sx={{ color: 'success.main', verticalAlign: 'middle', ml: 0.5 }} />;
      } else {
        return <ArrowForwardIcon fontSize="inherit" sx={{ color: 'text.secondary', verticalAlign: 'middle', ml: 0.5 }} />;
      }
    }
    return null;
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom sx={{ mb: 4 }}>
        Health Dashboard {activeProfile ? `for ${activeProfile.name}` : ''}
      </Typography>

      {/* Loading and Error States */}
      {profileLoading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Loading profile...</Typography>
        </Box>
      )}
      {profileError && !profileLoading && (
        <Alert severity="error" sx={{ mb: 3 }}>{profileError}</Alert>
      )}

      {/* Guidance when no profile is active */}
      {!activeProfile && !profileLoading && !profileError && (
         <Paper sx={{ p: 3, mb: 3, display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Get Started with Vein Diagram
            </Typography>
            <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
              Create a profile to organize your health data, or upload your first lab report.
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              <Button
                variant="contained"
                component={RouterLink}
                to="/profiles"
              >
                Create Profile
              </Button>
              <Button
                variant="outlined"
                component={RouterLink}
                to="/upload"
              >
                Upload Report
              </Button>
            </Stack>
         </Paper>
      )}

      {/* Main Dashboard Grid - Rendered regardless, but content inside handles activeProfile state */}
      <Grid container spacing={3}>
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
              // <HealthScoreOverview profileId={activeProfile.id} /> // Keep commented
            ) : (
              <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>Select a profile</Typography>
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
                 <CircularProgress size={20} sx={{ mt: 2 }} />
              ) : biomarkerError ? (
                 <Typography variant="body2" color="error" sx={{ mt: 2 }}>{biomarkerError}</Typography>
              ) : activeProfile.favorite_biomarkers && activeProfile.favorite_biomarkers.length > 0 ? (
                 <Box sx={{ overflowY: 'auto', maxHeight: '100px', mt: 1 }}>
                   <ul style={{ paddingLeft: '0px', margin: 0, listStyle: 'none' }}>
                     {activeProfile.favorite_biomarkers.map((favName: string) => {
                       const data = favoriteBiomarkerData[favName];
                       const trendIcon = renderTrendIcon(data?.latest?.value, data?.previous?.value);
                       return (
                         <li key={favName} style={{ marginBottom: '4px' }}>
                           <Typography variant="body2" component="span">
                             {favName}: {data?.latest ? `${data.latest.value} ${data.latest.unit || ''}` : 'No data'}
                           </Typography>
                           {trendIcon}
                         </li>
                       );
                     })}
                   </ul>
                 </Box>
              ) : (
                 <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>No favorite biomarkers set.</Typography>
              )
            ) : (
              <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>Select a profile</Typography>
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
                <CircularProgress size={20} sx={{ mt: 2 }} />
              ) : lastReportDate ? (
                 <Typography variant="h5" sx={{ mt: 2 }}>{lastReportDate}</Typography>
              ) : (
                 <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>No reports found.</Typography>
              )
            ) : (
              <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>Select a profile</Typography>
            )}
          </Paper>
        </Grid>

        {/* Row 2: Category Status & AI Summary */}
        <Grid item xs={12} md={6}>
           <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', minHeight: 150 }}> {/* Added minHeight */}
             <Typography variant="h6" color="primary" gutterBottom>
               Category Status
             </Typography>
             {activeProfile ? (
                <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>Category status coming soon...</Typography>
             ) : (
                <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>Select a profile</Typography>
             )}
           </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
           <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', minHeight: 150 }}> {/* Added minHeight */}
             <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
               <Typography variant="h6" color="primary">
                 AI Health Summary
               </Typography>
               <Button
                 component={RouterLink}
                 to="/visualization?tab=1"
                 size="small"
                 endIcon={<ArrowForwardIcon fontSize="small" />}
                 sx={{ textTransform: 'none' }}
                 disabled={!activeProfile} // Disable if no profile
               >
                 Full View
               </Button>
             </Box>

             {activeProfile ? (
               activeProfile.health_summary ? (
                 <>
                   <Box sx={{ mb: 1, p: 1.5, bgcolor: (theme) => alpha(theme.palette.primary.main, 0.05), borderRadius: 2, border: (theme) => `1px solid ${alpha(theme.palette.primary.main, 0.1)}` }}>
                     <Typography variant="body2" color="text.primary" sx={{ fontWeight: 500, lineHeight: 1.6, display: '-webkit-box', WebkitLineClamp: summaryExpanded ? 'unset' : 3, WebkitBoxOrient: 'vertical', overflow: 'hidden', textOverflow: 'ellipsis', position: 'relative', pr: summaryExpanded ? 0 : 2 }}>
                       {activeProfile.health_summary.split('\n\n')[0]}
                     </Typography>
                   </Box>
                   <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                     <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
                       {activeProfile.summary_last_updated && `Updated: ${new Date(activeProfile.summary_last_updated).toLocaleDateString()}`}
                     </Typography>
                     <Button onClick={() => setSummaryExpanded(!summaryExpanded)} size="small" endIcon={<ExpandMoreIcon sx={{ transform: summaryExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.3s' }} />} sx={{ textTransform: 'none' }}>
                       {summaryExpanded ? 'Show Less' : 'Read More'}
                     </Button>
                   </Box>
                   <Collapse in={summaryExpanded} timeout="auto" unmountOnExit>
                     <Box sx={{ mt: 2 }}>
                       {activeProfile.health_summary.split('\n\n').slice(1).map((paragraph, index) => (
                         <Typography key={index} variant="body2" paragraph sx={{ whiteSpace: 'pre-wrap', mt: 1, color: 'text.primary' }}>
                           {paragraph}
                         </Typography>
                       ))}
                     </Box>
                   </Collapse>
                 </>
               ) : (
                 <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', p: 2, flexGrow: 1, bgcolor: (theme) => alpha(theme.palette.background.default, 0.6), borderRadius: 2, border: '1px dashed', borderColor: 'divider' }}>
                   <Typography variant="body2" align="center" color="text.secondary" sx={{ mb: 1.5 }}>
                     No AI summary available yet
                   </Typography>
                   <Button component={RouterLink} to="/visualization?tab=1" size="small" variant="outlined" sx={{ textTransform: 'none' }}>
                     Generate Summary
                   </Button>
                 </Box>
               )
             ) : (
                <Typography variant="body2" sx={{ mt: 2, color: 'text.secondary' }}>Select a profile</Typography>
             )}
           </Paper>
        </Grid>

        {/* Row 3: Action Buttons */}
        <Grid item xs={12}>
           <Paper sx={{ p: 2 }}>
             <Typography variant="h6" color="primary" gutterBottom>
               Quick Actions
             </Typography>
             <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ mt: 2 }}>
               <Button variant="contained" component={RouterLink} to="/visualization" disabled={!activeProfile}>
                 View Visualizations
               </Button>
               <Button variant="outlined" component={RouterLink} to={activeProfile ? `/profile/${activeProfile.id}/history` : '#'} disabled={!activeProfile}>
                 View Full History
               </Button>
                <Button variant="outlined" component={RouterLink} to="/profiles" disabled={!activeProfile}>
                 Manage Profiles {/* Changed from Manage Favorites to Manage Profiles */}
               </Button>
               <Button variant="contained" color="secondary" component={RouterLink} to="/upload"> {/* Always enabled */}
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
