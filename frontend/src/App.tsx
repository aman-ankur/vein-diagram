import React, { useState, useEffect, Suspense } from 'react';
import { Routes, Route, Link } from 'react-router-dom';
import { 
  Box, 
  Container, 
  CssBaseline, 
  AppBar, 
  Toolbar,
  Typography, 
  Button, 
  ThemeProvider, 
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Alert,
  Snackbar,
  ClickAwayListener
} from '@mui/material';
import {
  Home as HomeIcon,
  UploadFile as UploadIcon,
  Analytics as AnalyticsIcon,
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Science as ScienceIcon
} from '@mui/icons-material';
import { theme } from './main';
import HomePage from './pages/HomePage';
import UploadPage from './pages/UploadPage';
import VisualizationPage from './pages/VisualizationPage';
import APIStatusIndicator from './components/APIStatusIndicator';
import { checkApiAvailability } from './services/api';

// Error Boundary Component
class AppErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; errorMessage: string }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, errorMessage: '' };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, errorMessage: error.message };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Application error:', error);
    console.error('Component stack:', errorInfo.componentStack);
    
    // Additional debugging for network or API errors
    if (error.message.includes('network') || error.message.includes('api') || error.message.includes('fetch')) {
      console.error('Potential network or API error detected');
      
      // Check API configuration
      import('./config').then(config => {
        console.log('Current API configuration:', {
          apiBaseUrl: config.API_BASE_URL,
          environmentInfo: {
            isDev: import.meta.env.DEV,
            mode: import.meta.env.MODE,
            baseUrl: import.meta.env.BASE_URL,
          }
        });
      });
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            p: 3,
            textAlign: 'center'
          }}
        >
          <Typography variant="h4" color="error" gutterBottom>
            Something went wrong
          </Typography>
          <Typography variant="body1" gutterBottom>
            {this.state.errorMessage || 'An unexpected error occurred'}
          </Typography>
          <Button 
            variant="contained" 
            color="primary" 
            onClick={() => window.location.reload()}
            sx={{ mt: 2 }}
          >
            Reload Application
          </Button>
        </Box>
      );
    }

    return this.props.children;
  }
}

// Fallback loading component
const LoadingFallback = () => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh'
    }}
  >
    <CircularProgress size={60} />
    <Typography variant="h6" sx={{ mt: 2 }}>
      Loading...
    </Typography>
  </Box>
);

function App() {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [apiAvailable, setApiAvailable] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showErrorSnackbar, setShowErrorSnackbar] = useState(false);

  // Check API availability on mount
  useEffect(() => {
    const checkApi = async () => {
      try {
        const isAvailable = await checkApiAvailability();
        setApiAvailable(isAvailable);
        
        if (!isAvailable) {
          setErrorMessage('Unable to connect to the backend server. Some features may be limited.');
          setShowErrorSnackbar(true);
        }
      } catch (error) {
        console.error('Error checking API:', error);
        setApiAvailable(false);
        setErrorMessage('Network error. Please check your connection.');
        setShowErrorSnackbar(true);
      }
    };
    
    checkApi();
  }, []);

  const handleDrawerToggle = () => {
    setIsDrawerOpen(!isDrawerOpen);
  };

  const handleCloseSnackbar = () => {
    setShowErrorSnackbar(false);
  };

  const drawerItems = [
    { text: 'Home', icon: <HomeIcon />, path: '/' },
    { text: 'Upload', icon: <UploadIcon />, path: '/upload' },
    { text: 'Visualization', icon: <AnalyticsIcon />, path: '/visualization' },
    { text: 'Biomarkers', icon: <ScienceIcon />, path: '/biomarkers' },
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
  ];

  const drawer = (
    <Box sx={{ width: 250 }} role="presentation" onClick={handleDrawerToggle}>
      <List>
        {drawerItems.map((item) => (
          <ListItem 
            button 
            key={item.text} 
            component={Link} 
            to={item.path} 
            sx={{
              '&:hover': {
                backgroundColor: 'rgba(0, 0, 0, 0.04)',
              },
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <ThemeProvider theme={theme}>
      <AppErrorBoundary>
        <CssBaseline />
          <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
            <AppBar position="static">
              <Toolbar>
                <IconButton
                  color="inherit"
                  aria-label="open drawer"
                  edge="start"
                  onClick={handleDrawerToggle}
                  sx={{ mr: 2 }}
                >
                  <MenuIcon />
                </IconButton>
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                  Vein Diagram
                </Typography>
                <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
                  <Button color="inherit" component={Link} to="/">
                    Home
                  </Button>
                  <Button color="inherit" component={Link} to="/upload">
                    Upload
                  </Button>
                  <Button color="inherit" component={Link} to="/visualization">
                    Visualization
                  </Button>
                </Box>
              </Toolbar>
            </AppBar>
            
            <Drawer
              anchor="left"
              open={isDrawerOpen}
              onClose={handleDrawerToggle}
            >
              {drawer}
            </Drawer>
            
            <Container component="main" sx={{ flexGrow: 1, py: 3 }}>
              <Suspense fallback={<LoadingFallback />}>
                <Routes>
                  <Route path="/" element={<HomePage />} />
                  <Route path="/upload" element={<UploadPage />} />
                  <Route path="/visualization" element={<VisualizationPage />} />
                  <Route path="*" element={
                    <Box sx={{ textAlign: 'center', mt: 4 }}>
                      <Typography variant="h4">Page Not Found</Typography>
                      <Button 
                        component={Link} 
                        to="/" 
                        variant="contained" 
                        sx={{ mt: 2 }}
                      >
                        Go Home
                      </Button>
                    </Box>
                  } />
                </Routes>
              </Suspense>
            </Container>
            
            <Box component="footer" sx={{ py: 3, px: 2, mt: 'auto', backgroundColor: (theme) => theme.palette.mode === 'light' ? theme.palette.grey[200] : theme.palette.grey[800] }}>
              <Container maxWidth="sm">
                <Typography variant="body2" color="text.secondary" align="center">
                  © {new Date().getFullYear()} Vein Diagram
                </Typography>
              </Container>
            </Box>
            
            {/* API Status Indicator */}
            <APIStatusIndicator position="bottom-right" showOnlyOnError={false} />
            
            {/* Error Snackbar */}
            <Snackbar 
              open={showErrorSnackbar} 
              autoHideDuration={6000} 
              onClose={handleCloseSnackbar}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
              ClickAwayListenerProps={{
                mouseEvent: 'onMouseUp'
              }}
            >
              <Alert 
                onClose={handleCloseSnackbar} 
                severity="error" 
                sx={{ width: '100%' }}
              >
                {errorMessage}
              </Alert>
            </Snackbar>
          </Box>
      </AppErrorBoundary>
    </ThemeProvider>
  );
}

export default App; 