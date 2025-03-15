import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Container, 
  Grid, 
  Button, 
  Card, 
  CardContent, 
  CardMedia, 
  Stack,
  Paper,
  useTheme,
  alpha,
  Divider,
  Tab,
  Tabs
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ScheduleIcon from '@mui/icons-material/Schedule';
import SecurityIcon from '@mui/icons-material/Security';
import TimelineIcon from '@mui/icons-material/Timeline';
import BiotechIcon from '@mui/icons-material/Biotech';
import Dashboard from '../components/Dashboard';
import storageService, { STORAGE_KEYS } from '../services/localStorage';

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
    path: '/visualize'
  },
  {
    title: 'Track Over Time',
    description: 'Monitor changes in your biomarkers over time to see trends and patterns in your health data.',
    icon: <TimelineIcon fontSize="large" color="primary" />,
    path: '/visualize'
  },
  {
    title: 'Privacy Focused',
    description: 'Your health data stays private. We employ advanced security measures to protect your information.',
    icon: <SecurityIcon fontSize="large" color="primary" />,
    path: '/about'
  }
];

// Mock biomarker categories
const biomarkerCategories = [
  { name: 'Cholesterol Panel', count: 5 },
  { name: 'Complete Blood Count', count: 12 },
  { name: 'Liver Function', count: 8 },
  { name: 'Kidney Function', count: 6 },
  { name: 'Hormones', count: 7 },
  { name: 'Vitamins & Minerals', count: 10 },
  { name: 'Metabolic Markers', count: 9 },
  { name: 'Inflammatory Markers', count: 4 }
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

const HomePage: React.FC = () => {
  const theme = useTheme();
  const [hasUploads, setHasUploads] = useState(false);
  const [tabValue, setTabValue] = useState(0);

  // Check if user has uploads for conditional rendering
  useEffect(() => {
    const uploads = storageService.getItem(STORAGE_KEYS.UPLOADED_FILES, []);
    setHasUploads(uploads.length > 0);
    
    // If user has uploads, default to dashboard tab
    if (uploads.length > 0) {
      setTabValue(0);
    }
  }, []);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box>
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
                      component={RouterLink} 
                      to="/upload"
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
                      component={RouterLink} 
                      to="/visualize"
                      endIcon={<AssessmentIcon />}
                      sx={{ 
                        py: 1.5, 
                        px: 4,
                        fontWeight: 600 
                      }}
                    >
                      Explore Visualizations
                    </Button>
                  </Stack>
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
        // Dashboard header section for returning users
        <Box 
          className="gradient-primary"
          sx={{ 
            pt: { xs: 6, md: 8 },
            pb: { xs: 6, md: 8 }
          }}
        >
          <Container maxWidth="lg">
            <Box
              className="fade-in"
              sx={{
                textAlign: 'center'
              }}
            >
              <Typography 
                component="h1" 
                variant="h2" 
                color="white"
                gutterBottom
                sx={{ 
                  fontWeight: 700,
                  fontSize: { xs: '2rem', md: '2.75rem' },
                }}
              >
                Welcome Back to Your Health Dashboard
              </Typography>
              <Typography 
                variant="h6" 
                sx={{ 
                  color: 'rgba(255, 255, 255, 0.9)',
                  maxWidth: '800px',
                  mx: 'auto',
                  mb: 4
                }}
              >
                Track your biomarkers, analyze your health trends, and gain valuable insights
              </Typography>
              <Box sx={{ 
                borderRadius: '40px', 
                backgroundColor: 'rgba(255, 255, 255, 0.15)',
                display: 'inline-flex',
                p: 0.5,
                backdropFilter: 'blur(8px)'
              }}>
                <Tabs 
                  value={tabValue} 
                  onChange={handleTabChange}
                  sx={{
                    '& .MuiTabs-indicator': {
                      display: 'none',
                    },
                    '& .MuiTab-root': {
                      color: 'rgba(255, 255, 255, 0.7)',
                      fontWeight: 500,
                      mx: 0.5,
                      minHeight: 'auto',
                      borderRadius: '30px',
                      py: 1,
                      px: 2,
                      '&.Mui-selected': {
                        color: theme.palette.text.primary,
                        backgroundColor: 'white',
                      },
                    }
                  }}
                >
                  <Tab label="Dashboard" />
                  <Tab label="Features" />
                </Tabs>
              </Box>
            </Box>
          </Container>
        </Box>
      )}

      {/* Content Section */}
      <Container maxWidth="lg" sx={{ py: { xs: 6, md: 8 } }}>
        {hasUploads ? (
          // Tabs content for users with data
          <>
            <TabPanel value={tabValue} index={0}>
              <Dashboard />
            </TabPanel>
            <TabPanel value={tabValue} index={1}>
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
          </>
        ) : (
          // Content for new users
          <>
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
            <Box sx={{ py: 8, bgcolor: alpha(theme.palette.primary.main, 0.03), borderRadius: 4, px: 3 }}>
              <Typography 
                component="h2" 
                variant="h3" 
                align="center"
                gutterBottom
                sx={{ 
                  fontWeight: 700,
                  position: 'relative',
                  mb: 5,
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
                Supported Biomarkers
              </Typography>
              
              <Grid container spacing={3}>
                {biomarkerCategories.map((category, index) => (
                  <Grid item xs={6} sm={4} md={3} key={index}>
                    <Paper 
                      className="hover-card"
                      sx={{ 
                        p: 3, 
                        textAlign: 'center',
                        height: '100%',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'center',
                        borderLeft: '4px solid',
                        borderColor: theme.palette.primary.main
                      }}
                    >
                      <Typography variant="h6" component="h3" gutterBottom>
                        {category.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {category.count} biomarkers
                      </Typography>
                    </Paper>
                  </Grid>
                ))}
              </Grid>
              
              <Box sx={{ textAlign: 'center', mt: 5 }}>
                <Button
                  variant="contained"
                  size="large"
                  component={RouterLink}
                  to="/upload"
                  endIcon={<CloudUploadIcon />}
                  sx={{ py: 1.5, px: 4 }}
                >
                  Upload Your First Test
                </Button>
              </Box>
            </Box>
            
            {/* How It Works */}
            <Box sx={{ py: 8 }}>
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
                How It Works
              </Typography>
              
              <Grid container spacing={4} sx={{ mt: 3 }}>
                <Grid item xs={12} md={4}>
                  <Box 
                    className="hover-card"
                    sx={{ 
                      p: 3, 
                      textAlign: 'center',
                      borderRadius: 4,
                      bgcolor: alpha(theme.palette.primary.main, 0.03),
                      height: '100%'
                    }}
                  >
                    <Box sx={{ 
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 60,
                      height: 60,
                      borderRadius: '50%',
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      color: theme.palette.primary.main,
                      mb: 2
                    }}>
                      <Typography variant="h4" component="span">1</Typography>
                    </Box>
                    <Typography variant="h5" component="h3" gutterBottom>
                      Upload Your Lab Results
                    </Typography>
                    <Typography color="text.secondary">
                      Simply upload your PDF, CSV, or Excel files containing lab results. 
                      Our intelligent system will extract all the biomarkers.
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Box 
                    className="hover-card"
                    sx={{ 
                      p: 3, 
                      textAlign: 'center',
                      borderRadius: 4,
                      bgcolor: alpha(theme.palette.primary.main, 0.03),
                      height: '100%'
                    }}
                  >
                    <Box sx={{ 
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 60,
                      height: 60,
                      borderRadius: '50%',
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      color: theme.palette.primary.main,
                      mb: 2
                    }}>
                      <Typography variant="h4" component="span">2</Typography>
                    </Box>
                    <Typography variant="h5" component="h3" gutterBottom>
                      Visualize Your Data
                    </Typography>
                    <Typography color="text.secondary">
                      See your biomarkers displayed in easy-to-understand charts and graphs. 
                      Identify trends and patterns at a glance.
                    </Typography>
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <Box 
                    className="hover-card"
                    sx={{ 
                      p: 3, 
                      textAlign: 'center',
                      borderRadius: 4,
                      bgcolor: alpha(theme.palette.primary.main, 0.03),
                      height: '100%'
                    }}
                  >
                    <Box sx={{ 
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 60,
                      height: 60,
                      borderRadius: '50%',
                      bgcolor: alpha(theme.palette.primary.main, 0.1),
                      color: theme.palette.primary.main,
                      mb: 2
                    }}>
                      <Typography variant="h4" component="span">3</Typography>
                    </Box>
                    <Typography variant="h5" component="h3" gutterBottom>
                      Track Over Time
                    </Typography>
                    <Typography color="text.secondary">
                      Monitor your health progress as you upload more results. 
                      See how your biomarkers change and improve over time.
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </>
        )}
      </Container>

      {/* CTA Section */}
      <Box 
        className="gradient-primary"
        sx={{ 
          py: { xs: 6, md: 10 }, 
          textAlign: 'center',
          color: 'white'
        }}
      >
        <Container maxWidth="md">
          <Typography variant="h3" component="h2" gutterBottom sx={{ fontWeight: 700 }}>
            Ready to take control of your health?
          </Typography>
          <Typography variant="h6" paragraph sx={{ mb: 4, opacity: 0.9 }}>
            Upload your lab results now and start understanding your biomarkers better than ever before.
          </Typography>
          <Button 
            variant="contained" 
            size="large" 
            component={RouterLink}
            to="/upload"
            color="secondary"
            sx={{ 
              py: 1.5, 
              px: 4,
              backgroundColor: 'white',
              color: theme.palette.primary.main,
              '&:hover': {
                backgroundColor: alpha('#ffffff', 0.9),
              }
            }}
          >
            Get Started Now
          </Button>
        </Container>
      </Box>
    </Box>
  );
};

export default HomePage; 