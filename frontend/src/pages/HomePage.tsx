import React, { useState, useEffect } from 'react';
import {
  Typography,
  Box,
  Container,
  Grid,
  Button,
  Card,
  CardContent,
  // CardMedia removed - unused
  Stack,
  Paper,
  useTheme,
  alpha,
  // Divider removed - unused
  Tab,
  Tabs,
  Alert
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import AssessmentIcon from '@mui/icons-material/Assessment';
// ScheduleIcon removed - unused
import SecurityIcon from '@mui/icons-material/Security';
import TimelineIcon from '@mui/icons-material/Timeline';
import BiotechIcon from '@mui/icons-material/Biotech';
import ScienceIcon from '@mui/icons-material/Science';
// Remove import for the old Dashboard component as it's no longer rendered here
// import Dashboard from '../components/Dashboard';
import storageService, { STORAGE_KEYS } from '../services/localStorage';
// Fix: Import ApiError from the correct location (assuming it's in types/api.ts)
import { getAllBiomarkers } from '../services/api';
// ApiError removed - unused
import LoadingIndicator from '../components/LoadingIndicator';
import ErrorHandler from '../components/ErrorHandler';

// Mock data for feature cards
const features = [
  {
    title: 'Easy Data Upload',
    description: 'Upload your lab results quickly and securely. We support various formats including PDF and CSV.',
    icon: <CloudUploadIcon fontSize="large" color="primary" />,
    path: '/upload'
  },
  {
    title: 'Visual Analysis',
    description: 'See your biomarkers visualized with intuitive charts and graphs for better understanding of your health.',
    icon: <AssessmentIcon fontSize="large" color="primary" />,
    path: '/visualize' // Corrected path
  },
  {
    title: 'Track Over Time',
    description: 'Monitor changes in your biomarkers over time to see trends and patterns in your health data.',
    icon: <TimelineIcon fontSize="large" color="primary" />,
    path: '/visualize' // Corrected path
  },
  {
    title: 'Privacy Focused',
    description: 'Your health data stays private. We employ advanced security measures to protect your information.',
    icon: <SecurityIcon fontSize="large" color="primary" />,
    path: '/about' // Assuming an about page exists or will be created
  }
];

// Biomarker categories with icons
const biomarkerCategories = [
  { name: 'Cholesterol Panel', count: 5, icon: <TimelineIcon color="primary" /> },
  { name: 'Complete Blood Count', count: 12, icon: <BiotechIcon color="primary" /> },
  { name: 'Liver Function', count: 8, icon: <AssessmentIcon color="primary" /> },
  { name: 'Kidney Function', count: 6, icon: <ScienceIcon color="primary" /> },
  { name: 'Hormones', count: 7, icon: <BiotechIcon color="primary" /> },
  { name: 'Vitamins & Minerals', count: 10, icon: <ScienceIcon color="primary" /> },
  { name: 'Metabolic Markers', count: 9, icon: <TimelineIcon color="primary" /> },
  { name: 'Inflammatory Markers', count: 4, icon: <BiotechIcon color="primary" /> }
];

// Interface for tabs
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// Tab panel component
function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`home-tabpanel-${index}`}
      aria-labelledby={`home-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const HomePage: React.FC = () => { // Corrected type error: FC requires return type ReactNode
  const theme = useTheme();
  const navigate = useNavigate();
  const [hasUploads, setHasUploads] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiAvailable, setApiAvailable] = useState<boolean | null>(null);
  // const [activeProfile, setActiveProfile] = useState<string | null>(null); // Removed unused state

  // Check API availability and if user has uploads
  useEffect(() => {
    const checkAPIAndUploads = async () => {
      setIsLoading(true);
      setError(null); // Reset error state

      // Check if user has uploads
      try {
        // getItem returns the value property of the stored item
        const uploads = storageService.getItem(STORAGE_KEYS.UPLOADED_FILES, []);

        // Make sure uploads is an array
        if (!Array.isArray(uploads)) {
          console.warn('Expected uploads to be an array but got:', typeof uploads);
          setHasUploads(false);
        } else {
          setHasUploads(uploads.length > 0);

          // If user has uploads, default to dashboard tab
          if (uploads.length > 0) {
            setTabValue(0);
          }
        }
      } catch (error) {
        console.error('Error checking uploads:', error);
        setHasUploads(false);
      }

      // Check if user is offline first
      if (typeof navigator !== 'undefined' && !navigator.onLine) {
        setApiAvailable(false);
        setError('You are currently offline. Limited functionality is available while offline.');
        setIsLoading(false);
        return;
      }

      // Check API availability
      try {
        // Make a simple API call to check if the backend is available
        await getAllBiomarkers({ limit: 1 });
        setApiAvailable(true);
      } catch (err: any) {
        console.error('API connection error:', err);
        setApiAvailable(false);

        // Provide more specific error messages based on error type
        if (err.isOffline) {
          setError('You are offline. Limited functionality is available while offline.');
        } else if (err.isNetworkError) {
          setError('Unable to reach the backend server. Please check your network connection or try again later.');
        } else if (err.status === 404) {
          setError('Backend service endpoint not found. Please verify the API configuration.');
        } else if (err.status >= 500) {
          setError('Backend server encountered an error. Our team has been notified and is working on a fix.');
        } else {
          setError('Unable to connect to the backend server. Some features may be limited.');
        }
      } finally {
        setIsLoading(false);
      }
    };

    checkAPIAndUploads();

    // Add event listeners for online/offline status
    const handleOnline = () => {
      setError(null);
      checkAPIAndUploads();
    };

    const handleOffline = () => {
      setApiAvailable(false);
      setError('You are currently offline. Limited functionality is available while offline.');
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => { // Keep event marked as unused again
    setTabValue(newValue);
  };

  const handleUploadClick = () => {
    navigate('/upload');
  };

  const handleExploreClick = () => {
    // Navigate directly to visualization, profile selection happens there if needed
    navigate('/visualization');
  }; // Added missing closing brace

  return (
    <Box>
      {/* API status alert */}
      {apiAvailable === false && (
        <Box sx={{ position: 'sticky', top: 0, zIndex: 1000 }}>
          <ErrorHandler
            error={error}
            retry={() => window.location.reload()}
          />
        </Box>
      )}

      {isLoading ? (
        <LoadingIndicator message="Connecting to server..." variant="linear" />
      ) : (
        <>
          {/* Hero Section with conditional rendering */}
          {!hasUploads ? (
            <Box
              className="bg-pattern"
              sx={{
                position: 'relative',
                overflow: 'hidden',
                pt: { xs: 6, md: 10 },
                pb: { xs: 8, md: 14 }
              }}
            >
              <Container maxWidth="lg">
                <Grid container spacing={4} alignItems="center">
                  <Grid item xs={12} md={6}>
                    <Box
                      className="slide-up"
                      sx={{
                        mb: 5,
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: { xs: 'center', md: 'flex-start' },
                        textAlign: { xs: 'center', md: 'left' }
                      }}
                    >
                      <Typography
                        component="h1"
                        variant="h2"
                        color="primary"
                        gutterBottom
                        sx={{
                          fontWeight: 700,
                          letterSpacing: -1,
                          fontSize: { xs: '2.5rem', md: '3.5rem' },
                          position: 'relative',
                          '&::after': {
                            content: '""',
                            position: 'absolute',
                            width: '50px',
                            height: '4px',
                            bottom: '-12px',
                            left: { xs: 'calc(50% - 25px)', md: '0' },
                            backgroundColor: theme.palette.secondary.main,
                          }
                        }}
                      >
                        Visualize Your Health
                      </Typography>
                      <Typography
                        variant="h5"
                        color="text.secondary"
                        paragraph
                        sx={{
                          maxWidth: '600px',
                          mt: 3,
                          mb: 4,
                          lineHeight: 1.8
                        }}
                      >
                        Understand your blood test results with intuitive visualizations and track changes over time.
                        Take control of your health with data-driven insights.
                      </Typography>
                      <Stack
                        direction={{ xs: 'column', sm: 'row' }}
                        spacing={2}
                        width={{ xs: '100%', sm: 'auto' }}
                        justifyContent={{ xs: 'center', md: 'flex-start' }}
                      >
                        <Button
                          variant="contained"
                          size="large"
                          onClick={handleUploadClick}
                          endIcon={<CloudUploadIcon />}
                          sx={{
                            py: 1.5,
                            px: 4,
                            fontWeight: 600
                          }}
                        >
                          Upload Data
                        </Button>
                        <Button
                          variant="outlined"
                          size="large"
                          onClick={handleExploreClick}
                          endIcon={<AssessmentIcon />}
                          sx={{
                            py: 1.5,
                            px: 4,
                            fontWeight: 600
                          }}
                          disabled={!apiAvailable}
                        >
                          Explore Visualizations
                        </Button>
                      </Stack>

                      {!apiAvailable && (
                        <Alert
                          severity="warning"
                          sx={{ mt: 2, maxWidth: { xs: '100%', sm: '400px' } }}
                        >
                          Backend connection is not available. Upload functionality is limited.
                        </Alert>
                      )}
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Box
                      className="scale-in"
                      sx={{
                        position: 'relative',
                        width: '100%',
                        height: { xs: '300px', md: '400px' },
                        display: 'flex',
                        justifyContent: 'center',
                        '&::before': {
                          content: '""',
                          position: 'absolute',
                          top: '10%',
                          left: '10%',
                          width: '80%',
                          height: '80%',
                          borderRadius: '50%',
                          background: alpha(theme.palette.primary.main, 0.1),
                          zIndex: 0
                        }
                      }}
                    >
                      <Box
                        sx={{
                          position: 'relative',
                          zIndex: 1,
                          width: '100%',
                          height: '100%',
                          backgroundImage: 'url("https://images.unsplash.com/photo-1576086213369-97a306d36557?q=80&w=800&auto=format&fit=crop")',
                          backgroundSize: 'cover',
                          backgroundPosition: 'center',
                          borderRadius: 4,
                          boxShadow: theme.shadows[10],
                          transform: 'translateY(-4%) rotate(2deg)',
                          transition: 'transform 0.3s ease-in-out',
                          '&:hover': {
                            transform: 'translateY(-6%) rotate(1deg)',
                          }
                        }}
                      />
                    </Box>
                  </Grid>
                </Grid>
              </Container>
            </Box>
          ) : (
            // User has uploads, show dashboard with tabs
            <Container maxWidth="lg" sx={{ pt: 4 }}>
              <Paper elevation={0} sx={{ mb: 4 }}>
                <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                  <Tabs
                    value={tabValue}
                    onChange={handleTabChange}
                    aria-label="homepage tabs"
                    variant="fullWidth"
                  >
                    <Tab label="Dashboard" id="tab-0" />
                    <Tab label="Upload More Data" id="tab-1" />
                    <Tab label="Explore Features" id="tab-2" />
                  </Tabs>
                </Box>
                <TabPanel value={tabValue} index={0}>
                  {/* Remove rendering of the old Dashboard component here */}
                  {/* <Dashboard /> */}
                  <Typography variant="h5" gutterBottom align="center">Welcome Back!</Typography>
                  <Typography variant="body1" color="text.secondary" align="center" paragraph>
                    Use the sidebar navigation to view your dashboard, visualizations, or upload new reports.
                  </Typography>

                  <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center', gap: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleUploadClick}
                      startIcon={<CloudUploadIcon />}
                    >
                      Upload More Data
                    </Button>
                    <Button
                      variant="outlined"
                      onClick={handleExploreClick}
                      startIcon={<AssessmentIcon />}
                      disabled={!apiAvailable}
                    >
                      Explore Visualizations
                    </Button>
                  </Box>

                  {!apiAvailable && (
                    <Alert
                      severity="warning"
                      sx={{ mt: 3 }}
                    >
                      Backend connection is not available. Some dashboard data may be outdated.
                    </Alert>
                  )}
                </TabPanel>

                <TabPanel value={tabValue} index={1}>
                  <Box sx={{ textAlign: 'center', p: 4 }}>
                    <Typography variant="h5" gutterBottom>
                      Add More Health Data
                    </Typography>
                    <Typography variant="body1" color="text.secondary" paragraph>
                      Upload additional lab results to enrich your health data and get more comprehensive insights.
                    </Typography>
                    <Button
                      variant="contained"
                      size="large"
                      onClick={handleUploadClick}
                      endIcon={<CloudUploadIcon />}
                      sx={{ mt: 2 }}
                    >
                      Go to Upload Page
                    </Button>

                    {!apiAvailable && (
                      <Alert
                        severity="warning"
                        sx={{ mt: 3 }}
                      >
                        Backend connection is not available. Upload functionality is limited.
                      </Alert>
                    )}
                  </Box>
                </TabPanel>

                <TabPanel value={tabValue} index={2}>
                  {/* Features Section */}
                  <Box
                    sx={{
                      mb: 8,
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center'
                    }}
                  >
                    <Typography
                      component="h2"
                      variant="h3"
                      align="center"
                      gutterBottom
                      sx={{
                        fontWeight: 700,
                        position: 'relative',
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          width: '60px',
                          height: '4px',
                          bottom: '-12px',
                          left: 'calc(50% - 30px)',
                          backgroundColor: theme.palette.secondary.main,
                        }
                      }}
                    >
                      Key Features
                    </Typography>
                    <Typography
                      variant="h6"
                      align="center"
                      color="text.secondary"
                      sx={{
                        maxWidth: '800px',
                        mx: 'auto',
                        mt: 3,
                        mb: 6
                      }}
                    >
                      Our platform offers everything you need to understand and track your health data
                    </Typography>

                    <Grid container spacing={4}>
                      {features.map((feature, index) => (
                        <Grid item xs={12} sm={6} md={3} key={index}>
                          <Card
                            className="hover-card"
                            sx={{
                              height: '100%',
                              display: 'flex',
                              flexDirection: 'column',
                              transition: 'all 0.3s ease',
                            }}
                          >
                            <CardContent sx={{ flexGrow: 1, textAlign: 'center', p: 3 }}>
                              <Box sx={{ mb: 2 }}>
                                {feature.icon}
                              </Box>
                              <Typography gutterBottom variant="h5" component="h3" sx={{ fontWeight: 600 }}>
                                {feature.title}
                              </Typography>
                              <Typography variant="body2" color="text.secondary" paragraph>
                                {feature.description}
                              </Typography>
                              <Button
                                component={RouterLink}
                                to={feature.path}
                                color="primary"
                                sx={{ mt: 'auto' }}
                              >
                                Learn more
                              </Button>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                </TabPanel>
              </Paper>
            </Container>
          )}

          {/* Feature section for new users */}
          {!hasUploads && (
            <Container maxWidth="lg" sx={{ py: 8 }}>
              {/* Features Section */}
              <Box
                sx={{
                  mb: 8,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center'
                }}
              >
                <Typography
                  component="h2"
                  variant="h3"
                  align="center"
                  color="text.primary"
                  gutterBottom
                  sx={{
                    fontWeight: 700,
                    position: 'relative',
                    '&::after': {
                      content: '""',
                      position: 'absolute',
                      width: '60px',
                      height: '4px',
                      bottom: '-12px',
                      left: 'calc(50% - 30px)',
                      backgroundColor: theme.palette.secondary.main,
                    }
                  }}
                >
                  Key Features
                </Typography>
                <Typography
                  variant="h6"
                  align="center"
                  color="text.secondary"
                  sx={{
                    maxWidth: '800px',
                    mx: 'auto',
                    mt: 3,
                    mb: 6
                  }}
                >
                  Our platform offers everything you need to understand and track your health data
                </Typography>

                <Grid container spacing={4}>
                  {features.map((feature, index) => (
                    <Grid item xs={12} sm={6} md={3} key={index}>
                      <Card
                        className="hover-card"
                        sx={{
                          height: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                          transition: 'all 0.3s ease',
                        }}
                      >
                        <CardContent sx={{ flexGrow: 1, textAlign: 'center', p: 3 }}>
                          <Box sx={{ mb: 2 }}>
                            {feature.icon}
                          </Box>
                          <Typography gutterBottom variant="h5" component="h3" sx={{ fontWeight: 600 }}>
                            {feature.title}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" paragraph>
                            {feature.description}
                          </Typography>
                          <Button
                            component={RouterLink}
                            to={feature.path}
                            color="primary"
                            sx={{ mt: 'auto' }}
                          >
                            Learn more
                          </Button>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </Box>

              {/* Biomarker Categories */}
              <Box sx={{ py: 8, bgcolor: alpha(theme.palette.primary.main, 0.05) }}>
                <Container maxWidth="lg">
                  <Box sx={{ mb: 6, textAlign: 'center' }}>
                    <Typography variant="h3" component="h2" gutterBottom>
                      Analyze Your Biomarkers
                    </Typography>
                    <Typography
                      variant="h6"
                      color="text.secondary"
                      sx={{ maxWidth: '700px', mx: 'auto' }}
                    >
                      Our platform supports a wide range of biomarker categories for comprehensive health monitoring.
                    </Typography>
                  </Box>

                  <Grid container spacing={3}>
                    {biomarkerCategories.map((category, index) => (
                      <Grid item xs={12} sm={6} md={3} key={index}>
                        <Card
                          className="hover-card"
                          sx={{
                            height: '100%',
                            display: 'flex',
                            flexDirection: 'column',
                            transition: 'transform 0.3s, box-shadow 0.3s',
                            '&:hover': {
                              transform: 'translateY(-5px)',
                              boxShadow: theme.shadows[10],
                            }
                          }}
                        >
                          <CardContent sx={{ flexGrow: 1, textAlign: 'center' }}>
                            <Box sx={{ mb: 2 }}>
                              {category.icon}
                            </Box>
                            <Typography variant="h6" component="h3" gutterBottom>
                              {category.name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {category.count} biomarkers available
                            </Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>

                  <Box sx={{ mt: 6, textAlign: 'center' }}>
                    <Button
                      variant="contained"
                      size="large"
                      onClick={handleUploadClick}
                      endIcon={<CloudUploadIcon />}
                      sx={{ mr: 2 }}
                    >
                      Upload Your Data
                    </Button>
                    <Button
                      variant="outlined"
                      size="large"
                      onClick={handleExploreClick}
                      endIcon={<AssessmentIcon />}
                      disabled={!apiAvailable}
                    >
                      Explore Visualizations
                    </Button>
                  </Box>
                </Container>
              </Box>
            </Container>
          )}

          {/* Call to action section */}
          <Box
            sx={{
              py: 10,
              background: `linear-gradient(to right, ${theme.palette.primary.main}, ${theme.palette.primary.dark})`,
              color: theme.palette.common.white
            }}
          >
            <Container maxWidth="md">
              <Box sx={{ textAlign: 'center' }}>
                <Typography variant="h3" component="h2" gutterBottom>
                  Start Tracking Your Health Today
                </Typography>
                <Typography variant="h6" paragraph sx={{ mb: 4, opacity: 0.9 }}>
                  Upload your lab results now and unlock valuable insights into your health metrics.
                </Typography>
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleUploadClick}
                  sx={{
                    bgcolor: theme.palette.common.white,
                    color: theme.palette.primary.main,
                    '&:hover': {
                      bgcolor: alpha(theme.palette.common.white, 0.9),
                    },
                    px: 4,
                    py: 1.5,
                    fontSize: '1rem',
                    fontWeight: 600
                  }}
                >
                  Get Started
                </Button>
              </Box>
            </Container>
          </Box>
        </>
      )}
    </Box>
  );
};

export default HomePage;
