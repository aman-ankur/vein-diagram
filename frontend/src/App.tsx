import React, { useState, useEffect } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Container, 
  Button, 
  Box, 
  CssBaseline,
  IconButton,
  Menu,
  MenuItem,
  useScrollTrigger,
  Slide,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  useTheme,
  useMediaQuery,
  Avatar,
  Tooltip
} from '@mui/material';
import { alpha } from '@mui/material/styles';

// Import icons
import MenuIcon from '@mui/icons-material/Menu';
import HomeIcon from '@mui/icons-material/Home';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import BarChartIcon from '@mui/icons-material/BarChart';
import InfoIcon from '@mui/icons-material/Info';
import GitHubIcon from '@mui/icons-material/GitHub';
import TwitterIcon from '@mui/icons-material/Twitter';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import BiotechIcon from '@mui/icons-material/Biotech';

// Import pages
import HomePage from './pages/HomePage';
import AboutPage from './pages/AboutPage';
import UploadPage from './pages/UploadPage';
import VisualizePage from './pages/VisualizePage';

// Hide AppBar on scroll down
function HideOnScroll(props: { children: React.ReactElement }) {
  const { children } = props;
  const trigger = useScrollTrigger();

  return (
    <Slide appear={false} direction="down" in={!trigger}>
      {children}
    </Slide>
  );
}

// Page transition component
const PageTransition: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <Box
      sx={{
        animation: 'fadeIn 0.4s ease-in-out',
        '@keyframes fadeIn': {
          '0%': {
            opacity: 0,
            transform: 'translateY(10px)',
          },
          '100%': {
            opacity: 1,
            transform: 'translateY(0)',
          },
        },
      }}
    >
      {children}
    </Box>
  );
};

function App() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const location = useLocation();
  
  // Social media menu
  const [socialAnchorEl, setSocialAnchorEl] = useState<null | HTMLElement>(null);
  const socialMenuOpen = Boolean(socialAnchorEl);
  
  const handleSocialClick = (event: React.MouseEvent<HTMLElement>) => {
    setSocialAnchorEl(event.currentTarget);
  };
  
  const handleSocialClose = () => {
    setSocialAnchorEl(null);
  };

  // Toggle the mobile drawer
  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };
  
  // Close drawer when route changes on mobile
  useEffect(() => {
    if (mobileOpen) {
      setMobileOpen(false);
    }
  }, [location.pathname, mobileOpen]);

  // Navigation items
  const navItems = [
    { title: 'Home', path: '/', icon: <HomeIcon /> },
    { title: 'Upload', path: '/upload', icon: <UploadFileIcon /> },
    { title: 'Visualize', path: '/visualize', icon: <BarChartIcon /> },
    { title: 'About', path: '/about', icon: <InfoIcon /> },
  ];

  // Drawer content
  const drawer = (
    <Box sx={{ width: 250 }} role="presentation">
      <Box sx={{ 
        p: 2, 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center',
        bgcolor: (theme) => alpha(theme.palette.primary.main, 0.03),
        borderBottom: '1px solid',
        borderColor: 'divider'
      }}>
        <BiotechIcon color="primary" sx={{ mr: 1 }} />
        <Typography variant="h6" color="primary" component="div">
          Vein Diagram
        </Typography>
      </Box>
      <List>
        {navItems.map((item) => (
          <ListItem 
            button 
            component={Link} 
            to={item.path} 
            key={item.title}
            selected={location.pathname === item.path}
            sx={{
              '&.Mui-selected': {
                bgcolor: (theme) => alpha(theme.palette.primary.main, 0.1),
                '&:hover': {
                  bgcolor: (theme) => alpha(theme.palette.primary.main, 0.15),
                },
              },
            }}
          >
            <ListItemIcon>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.title} />
          </ListItem>
        ))}
      </List>
      <Divider sx={{ my: 2 }} />
      <Box sx={{ p: 2 }}>
        <Typography variant="caption" color="text.secondary">
          © {new Date().getFullYear()} Vein Diagram
        </Typography>
      </Box>
    </Box>
  );

  return (
    <>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        <HideOnScroll>
          <AppBar position="sticky" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
            <Toolbar>
              {isMobile && (
                <IconButton
                  color="inherit"
                  aria-label="open drawer"
                  edge="start"
                  onClick={handleDrawerToggle}
                  sx={{ mr: 2 }}
                >
                  <MenuIcon />
                </IconButton>
              )}
              
              <Typography 
                variant="h6" 
                component={Link} 
                to="/"
                sx={{ 
                  flexGrow: 1, 
                  color: 'white', 
                  textDecoration: 'none',
                  display: 'flex',
                  alignItems: 'center',
                }}
              >
                <BiotechIcon sx={{ mr: 1 }} />
                Vein Diagram
              </Typography>
              
              {!isMobile && (
                <Box sx={{ display: 'flex' }}>
                  {navItems.map((item) => (
                    <Button
                      key={item.title}
                      component={Link}
                      to={item.path}
                      color="inherit"
                      sx={{ 
                        mx: 1,
                        position: 'relative',
                        '&::after': {
                          content: '""',
                          position: 'absolute',
                          width: location.pathname === item.path ? '100%' : '0%',
                          height: '3px',
                          bottom: '0',
                          left: '0',
                          bgcolor: 'secondary.main',
                          transition: 'width 0.3s ease',
                        },
                        '&:hover::after': {
                          width: '100%',
                        },
                      }}
                    >
                      {item.title}
                    </Button>
                  ))}
                </Box>
              )}
              
              <Box sx={{ ml: 2 }}>
                <Tooltip title="Social Media">
                  <IconButton
                    color="inherit"
                    aria-label="social media"
                    onClick={handleSocialClick}
                    size="small"
                  >
                    <Avatar sx={{ width: 32, height: 32, bgcolor: 'secondary.main' }}>
                      <Typography variant="subtitle2">VD</Typography>
                    </Avatar>
                  </IconButton>
                </Tooltip>
                <Menu
                  anchorEl={socialAnchorEl}
                  open={socialMenuOpen}
                  onClose={handleSocialClose}
                  MenuListProps={{
                    'aria-labelledby': 'social-button',
                  }}
                >
                  <MenuItem onClick={handleSocialClose}>
                    <GitHubIcon fontSize="small" sx={{ mr: 1 }} />
                    GitHub
                  </MenuItem>
                  <MenuItem onClick={handleSocialClose}>
                    <TwitterIcon fontSize="small" sx={{ mr: 1 }} />
                    Twitter
                  </MenuItem>
                  <MenuItem onClick={handleSocialClose}>
                    <LinkedInIcon fontSize="small" sx={{ mr: 1 }} />
                    LinkedIn
                  </MenuItem>
                </Menu>
              </Box>
            </Toolbar>
          </AppBar>
        </HideOnScroll>
        
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true, // Better mobile performance
          }}
          sx={{
            '& .MuiDrawer-paper': { 
              boxSizing: 'border-box', 
              width: 250 
            },
          }}
        >
          {drawer}
        </Drawer>
        
        <Box component="main" sx={{ flexGrow: 1 }}>
          <PageTransition>
            <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/about" element={<AboutPage />} />
              <Route path="/upload" element={<UploadPage />} />
              <Route path="/visualize" element={<VisualizePage />} />
            </Routes>
          </PageTransition>
        </Box>
        
        <Box 
          component="footer" 
          sx={{ 
            py: 3, 
            px: 2, 
            mt: 'auto', 
            backgroundColor: (theme) => theme.palette.grey[100],
            borderTop: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Container maxWidth="lg">
            <Box sx={{ 
              display: 'flex', 
              flexDirection: { xs: 'column', sm: 'row' },
              justifyContent: 'space-between',
              alignItems: { xs: 'center', sm: 'flex-start' },
              textAlign: { xs: 'center', sm: 'left' },
            }}>
              <Box sx={{ mb: { xs: 2, sm: 0 } }}>
                <Typography variant="h6" color="primary" gutterBottom>
                  Vein Diagram
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Visualize and track your blood test results over time.
                </Typography>
              </Box>
              
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Quick Links
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column' }}>
                  {navItems.map((item) => (
                    <Button
                      key={item.title}
                      component={Link}
                      to={item.path}
                      color="inherit"
                      size="small"
                      sx={{ justifyContent: 'flex-start', py: 0.5 }}
                    >
                      {item.icon} 
                      <Typography variant="body2" sx={{ ml: 1 }}>
                        {item.title}
                      </Typography>
                    </Button>
                  ))}
                </Box>
              </Box>
            </Box>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
              <Typography variant="body2" color="text.secondary" align="center">
                © {new Date().getFullYear()} Vein Diagram - Biomarker Visualization
              </Typography>
            </Box>
          </Container>
        </Box>
      </Box>
    </>
  );
}

export default App; 