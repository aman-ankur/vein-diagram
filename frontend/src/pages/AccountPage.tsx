import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate, useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Container,
  Paper,
  Grid,
  Button,
  Divider,
  Avatar,
  Chip,
  IconButton,
  styled,
  useTheme,
  Card,
  CardHeader,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  alpha,
  Tooltip
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Email as EmailIcon,
  Key as KeyIcon,
  LockOpen as LockOpenIcon,
  AccountCircle as AccountCircleIcon,
  CalendarToday as CalendarTodayIcon,
  Login as LoginIcon,
  Security as SecurityIcon,
  Shield as ShieldIcon,
  Logout as LogoutIcon,
  OpenInNew as OpenInNewIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';

// Styled components for custom elements
const GradientTypography = styled(Typography)(({ theme }) => ({
  backgroundImage: `linear-gradient(to right, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
  WebkitBackgroundClip: 'text',
  WebkitTextFillColor: 'transparent',
  fontWeight: 'bold'
}));

const StyledCard = styled(Card)(({ theme }) => ({
  background: `linear-gradient(145deg, ${alpha(theme.palette.background.paper, 0.8)}, ${alpha(theme.palette.background.paper, 0.9)})`,
  backdropFilter: 'blur(10px)',
  borderRadius: theme.shape.borderRadius * 2,
  boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
  border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
  marginBottom: theme.spacing(5),
  overflow: 'hidden',
  transition: 'transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out',
  '&:hover': {
    transform: 'translateY(-5px)',
    boxShadow: `0 12px 40px ${alpha(theme.palette.primary.main, 0.25)}`
  }
}));

const StyledCardHeader = styled(CardHeader)(({ theme }) => ({
  borderBottom: `1px solid ${alpha(theme.palette.divider, 0.1)}`,
  '& .MuiCardHeader-title': {
    display: 'flex',
    alignItems: 'center',
    fontSize: '1.2rem',
    fontWeight: 600,
    color: theme.palette.text.primary
  },
  '& .MuiCardHeader-avatar': {
    marginRight: theme.spacing(1.5),
    backgroundColor: alpha(theme.palette.primary.main, 0.1),
    color: theme.palette.primary.main
  }
}));

const InfoListItem = styled(ListItem)(({ theme }) => ({
  padding: theme.spacing(2.5),
  '&:hover': {
    backgroundColor: alpha(theme.palette.action.hover, 0.1)
  },
  borderBottom: `1px solid ${alpha(theme.palette.divider, 0.05)}`
}));

const FeatureItem = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'flex-start',
  padding: theme.spacing(2.5),
  '&:hover': {
    backgroundColor: alpha(theme.palette.action.hover, 0.1)
  },
  borderBottom: `1px solid ${alpha(theme.palette.divider, 0.05)}`
}));

const ActionButton = styled(Button)(({ theme }) => ({
  borderRadius: theme.shape.borderRadius * 1.5,
  padding: '10px 24px',
  textTransform: 'none',
  fontWeight: 600,
  boxShadow: `0 4px 14px ${alpha(theme.palette.primary.main, 0.25)}`,
  transition: 'all 0.3s ease',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: `0 6px 20px ${alpha(theme.palette.primary.main, 0.35)}`
  }
}));

const ProfileAvatar = styled(Avatar)(({ theme }) => ({
  width: 80,
  height: 80,
  backgroundColor: alpha(theme.palette.primary.main, 0.2),
  color: theme.palette.primary.main,
  fontSize: '2rem',
  fontWeight: 'bold',
  boxShadow: `0 4px 14px ${alpha(theme.palette.common.black, 0.15)}`
}));

const AccountPage: React.FC = () => {
  const theme = useTheme();
  const { user, loading, signOut } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const navigate = useNavigate();
  
  // Redirect to login if not authenticated
  if (!user && !loading) {
    return <Navigate to="/login" replace />;
  }
  
  // Show loading state while auth state is initializing
  if (loading) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '100vh', 
          bgcolor: 'background.default'
        }}
      >
        <Box 
          sx={{ 
            width: 40, 
            height: 40, 
            borderRadius: '50%', 
            border: 2,
            borderColor: 'primary.main', 
            borderTopColor: 'transparent',
            animation: 'spin 1s linear infinite',
            '@keyframes spin': {
              '0%': { transform: 'rotate(0deg)' },
              '100%': { transform: 'rotate(360deg)' }
            }
          }} 
        />
      </Box>
    );
  }

  const handleSignOut = async () => {
    try {
      setIsSigningOut(true);
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Error signing out:', error);
      setIsSigningOut(false);
    }
  };

  // Create initials for avatar from email
  const getInitials = (email: string) => {
    return email
      .split('@')[0]
      .substring(0, 2)
      .toUpperCase();
  };

  return (
    <Box 
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        pt: 4,
        pb: 8
      }}
    >
      <Container maxWidth="md" sx={{ animation: 'fadeIn 0.5s ease-out', '@keyframes fadeIn': { from: { opacity: 0 }, to: { opacity: 1 } } }}>
        {/* Back Button */}
        <Box sx={{ mb: 4 }}>
          <Button
            onClick={() => navigate('/dashboard')}
            startIcon={<ArrowBackIcon />}
            sx={{
              color: 'text.secondary',
              '&:hover': {
                color: 'primary.main',
                bgcolor: alpha(theme.palette.primary.main, 0.1),
                transform: 'translateX(-4px)'
              },
              transition: 'all 0.3s',
              pl: 2,
              pr: 3,
              py: 1,
              borderRadius: 2
            }}
          >
            Back to Dashboard
          </Button>
        </Box>
        
        {/* Header */}
        <Box sx={{ mb: 5, display: 'flex', alignItems: 'center', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
          <ProfileAvatar>
            {user?.email ? getInitials(user.email) : 'U'}
          </ProfileAvatar>
          
          <Box sx={{ flexGrow: 1 }}>
            <GradientTypography variant="h4" sx={{ mb: 1 }}>
              Account Settings
            </GradientTypography>
            <Typography variant="subtitle1" color="text.secondary">
              Manage your account preferences and security
            </Typography>
          </Box>
          
          <Tooltip title="Sign Out">
            <ActionButton
              onClick={handleSignOut}
              disabled={isSigningOut}
              color="error"
              variant="contained"
              endIcon={<LogoutIcon />}
              sx={{ 
                minWidth: { xs: '100%', md: 'auto' },
                alignSelf: { xs: 'stretch', md: 'flex-start' }
              }}
            >
              {isSigningOut ? 'Signing Out...' : 'Sign Out'}
            </ActionButton>
          </Tooltip>
        </Box>
        
        {/* User Information Card */}
        <StyledCard elevation={0} sx={{ mb: 5 }}>
          <StyledCardHeader
            avatar={<AccountCircleIcon fontSize="large" />}
            title="User Information"
          />
          
          <CardContent sx={{ p: 0 }}>
            <List disablePadding>
              <InfoListItem>
                <ListItemIcon>
                  <EmailIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Email Address
                    </Typography>
                  }
                  secondary={
                    <Typography variant="body1" sx={{ fontWeight: 500 }}>
                      {user?.email}
                    </Typography>
                  }
                />
              </InfoListItem>
              
              <InfoListItem>
                <ListItemIcon>
                  <KeyIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      User ID
                    </Typography>
                  }
                  secondary={
                    <Typography 
                      variant="body2" 
                      component="div" 
                      sx={{ 
                        fontFamily: 'monospace',
                        opacity: 0.7,
                        wordBreak: 'break-all',
                        fontSize: '0.8rem'
                      }}
                    >
                      {user?.id}
                    </Typography>
                  }
                />
              </InfoListItem>
              
              <InfoListItem>
                <ListItemIcon>
                  <LoginIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Authentication Method
                    </Typography>
                  }
                  secondary={
                    <Chip 
                      label={user?.app_metadata?.provider === 'google' ? 'Google' : 'Email/Password'} 
                      size="small"
                      sx={{ 
                        bgcolor: alpha(theme.palette.primary.main, 0.1),
                        color: theme.palette.primary.main,
                        fontWeight: 500,
                        borderRadius: 1
                      }}
                    />
                  }
                />
              </InfoListItem>
              
              <InfoListItem>
                <ListItemIcon>
                  <CalendarTodayIcon color="primary" />
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                      Account Created
                    </Typography>
                  }
                  secondary={
                    <Typography variant="body1">
                      {new Date(user?.created_at ?? '').toLocaleString()}
                    </Typography>
                  }
                />
              </InfoListItem>
            </List>
          </CardContent>
        </StyledCard>
        
        {/* Security & Privacy Card */}
        <StyledCard elevation={0}>
          <StyledCardHeader
            avatar={<ShieldIcon fontSize="large" />}
            title="Security & Privacy"
          />
          
          <CardContent sx={{ p: 0 }}>
            <Box
              sx={{
                p: 3,
                display: 'flex',
                flexDirection: { xs: 'column', sm: 'row' },
                justifyContent: 'space-between',
                alignItems: { xs: 'stretch', sm: 'center' },
                gap: 2
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <LockOpenIcon color="primary" />
                <Box>
                  <Typography variant="subtitle2">Password</Typography>
                  <Typography variant="body2" color="text.secondary">
                    Change your password or reset it if forgotten
                  </Typography>
                </Box>
              </Box>
              
              <Button
                variant="outlined"
                color="primary"
                onClick={() => navigate('/reset-password')}
                endIcon={<OpenInNewIcon />}
                sx={{
                  borderRadius: 2,
                  textTransform: 'none',
                  px: 3,
                  alignSelf: { xs: 'stretch', sm: 'center' }
                }}
              >
                Change Password
              </Button>
            </Box>
            
            <Divider />
            
            <FeatureItem>
              <CheckCircleIcon 
                sx={{ 
                  mr: 2, 
                  color: 'success.main',
                  bgcolor: alpha(theme.palette.success.main, 0.1),
                  borderRadius: '50%',
                  p: 0.5,
                  width: 30,
                  height: 30
                }} 
              />
              <Box>
                <Typography variant="subtitle2">Data Protection</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  Your data is encrypted and securely stored
                </Typography>
              </Box>
            </FeatureItem>
            
            <Divider />
            
            <FeatureItem>
              <CheckCircleIcon 
                sx={{ 
                  mr: 2, 
                  color: 'success.main',
                  bgcolor: alpha(theme.palette.success.main, 0.1),
                  borderRadius: '50%',
                  p: 0.5,
                  width: 30,
                  height: 30
                }} 
              />
              <Box>
                <Typography variant="subtitle2">Privacy Controls</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                  Your health data is private and only accessible to you
                </Typography>
              </Box>
            </FeatureItem>
          </CardContent>
        </StyledCard>
        
        <Box sx={{ mt: 5, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            © {new Date().getFullYear()} Vein Diagram • All rights reserved
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default AccountPage; 