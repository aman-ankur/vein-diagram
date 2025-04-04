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
  ListItemButton,
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
  Science as ScienceIcon,
  Person as PersonIcon,
  Login as LoginIcon,
  AccountCircle as AccountIcon,
  ErrorOutline as ErrorOutlineIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { theme } from './main';
import HomePage from './pages/HomePage';
import UploadPage from './pages/UploadPage';
import VisualizationPage from './pages/VisualizationPage';
import ProfileManagement from './pages/ProfileManagement';
import BiomarkerHistoryPage from './pages/BiomarkerHistoryPage';
const DashboardPage = React.lazy(() => import('./pages/DashboardPage.tsx'));
import APIStatusIndicator from './components/APIStatusIndicator';
import { checkApiAvailability } from './services/api';

// Auth imports
import { AuthProvider } from './contexts/AuthContext';
import { ProfileProvider } from './contexts/ProfileContext';
import ProtectedRoute from './components/ProtectedRoute';
import LoginPage from './pages/LoginPage';
// import SignupPage from './pages/SignupPage'; // Keep old one for now, maybe rename later
import NewSignupPage from './pages/NewSignupPage'; // Import the new page
import ResetPasswordPage from './pages/ResetPasswordPage';
import AccountPage from './pages/AccountPage';
import AuthCallbackPage from './pages/AuthCallbackPage';
import { useAuth } from './contexts/AuthContext';
import { logger } from './utils/logger';

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
    logger.error('Application error caught by boundary', error, {
      componentStack: errorInfo.componentStack
    });

    // Check for network or API errors
    if (error.message.includes('network') || error.message.includes('api') || error.message.includes('fetch')) {
      logger.warn('Network or API error detected', {
        message: error.message,
        type: 'network_error'
      });
      
      // Log API configuration in development
      import('./config/environment').then(config => {
        logger.debug('Current API configuration', {
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
          <ErrorOutlineIcon sx={{ fontSize: 64, color: 'error.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            Something went wrong
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph>
            {this.state.errorMessage || 'An unexpected error occurred.'}
          </Typography>
          <Button
            variant="contained"
            onClick={() => {
              logger.info('User initiated app reload after error');
              window.location.reload();
            }}
            startIcon={<RefreshIcon />}
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

// NavBar component to access auth context
const NavBar: React.FC<{ 
  handleDrawerToggle: () => void;
}> = ({ handleDrawerToggle }) => {
  const { user, signOut } = useAuth();
  
  return (
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
          {user ? (
            <>
              <Button color="inherit" component={Link} to="/upload">
                Upload
              </Button>
              <Button color="inherit" component={Link} to="/visualization">
                Visualization
              </Button>
              <Button color="inherit" component={Link} to="/profiles">
                Profiles
              </Button>
              <Button color="inherit" component={Link} to="/dashboard">
                Dashboard
              </Button>
              <Button color="inherit" component={Link} to="/account">
                Account
              </Button>
              <Button color="inherit" onClick={() => signOut()}>
                Sign Out
              </Button>
            </>
          ) : (
            <>
              <Button color="inherit" component={Link} to="/login">
                Sign In
              </Button>
              <Button color="inherit" component={Link} to="/signup">
                Sign Up
              </Button>
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

function AppContent() {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [apiAvailable, setApiAvailable] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [showErrorSnackbar, setShowErrorSnackbar] = useState(false);
  const { user } = useAuth();

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

  // Adjust drawer items based on authentication state
  const drawerItems = [
    { text: 'Home', icon: <HomeIcon />, path: '/' },
    ...(user 
      ? [
          { text: 'Upload', icon: <UploadIcon />, path: '/upload' },
          { text: 'Visualization', icon: <AnalyticsIcon />, path: '/visualization' },
          { text: 'Biomarkers', icon: <ScienceIcon />, path: '/biomarkers' },
          { text: 'Profiles', icon: <PersonIcon />, path: '/profiles' },
          { text: 'Dashboard', icon: <DashboardIcon />, path: '/dashboard' },
          { text: 'Account', icon: <AccountIcon />, path: '/account' },
        ]
      : [
          { text: 'Sign In', icon: <LoginIcon />, path: '/login' },
          { text: 'Sign Up', icon: <PersonIcon />, path: '/signup' },
        ]),
  ];

  const drawer = (
    <Box sx={{ width: 250 }} role="presentation" onClick={handleDrawerToggle}>
      <List>
        {drawerItems.map((item) => (
          <ListItemButton 
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
          </ListItemButton> 
        ))}
      </List>
    </Box>
  );

  return (
    <AppErrorBoundary>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <NavBar handleDrawerToggle={handleDrawerToggle} />
        
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
              <Route path="/login" element={<LoginPage />} />
              {/* Use the new signup page */}
              <Route path="/signup" element={<NewSignupPage />} /> 
              <Route path="/reset-password" element={<ResetPasswordPage />} />
              <Route path="/auth/callback" element={<AuthCallbackPage />} />
              
              {/* Protected routes */}
              <Route path="/upload" element={<ProtectedRoute><UploadPage /></ProtectedRoute>} />
              <Route path="/visualization" element={<ProtectedRoute><VisualizationPage /></ProtectedRoute>} />
              <Route path="/visualization/:fileId" element={<ProtectedRoute><VisualizationPage /></ProtectedRoute>} />
              <Route path="/profiles" element={<ProtectedRoute><ProfileManagement /></ProtectedRoute>} />
              <Route path="/profile/:profileId/history" element={<ProtectedRoute><BiomarkerHistoryPage /></ProtectedRoute>} />
              <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
              <Route path="/account" element={<ProtectedRoute><AccountPage /></ProtectedRoute>} />
              
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
  );
}

function App() {
  return (
    <ThemeProvider theme={theme}>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <AuthProvider>
          <ProfileProvider>
            <AppContent />
          </ProfileProvider>
        </AuthProvider>
      </LocalizationProvider>
    </ThemeProvider>
  );
}

export default App;
