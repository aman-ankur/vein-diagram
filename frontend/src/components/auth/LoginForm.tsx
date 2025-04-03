import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Container, 
  InputAdornment, 
  IconButton,
  Paper,
  Divider,
  Grid,
  Alert,
  CircularProgress
} from '@mui/material';
import { Visibility, VisibilityOff, ArrowBack, CheckCircle } from '@mui/icons-material';
import GoogleAuthButton from './GoogleAuthButton';

// Use a professional medical image for the login page
const medicalImageUrl = 'https://images.unsplash.com/photo-1581093196277-9f608bb3d4b7?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get the redirect path from location state, or default to dashboard
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      setErrorMessage('Please enter both email and password');
      return;
    }
    
    try {
      setIsLoading(true);
      setErrorMessage('');
      
      const { error } = await signIn(email, password);
      
      if (error) {
        throw error;
      }
      
      // Redirect to the page they were trying to access, or default to dashboard
      navigate(from, { replace: true });
    } catch (error: any) {
      console.error('Login error:', error);
      setErrorMessage(error.message || 'Failed to sign in');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: { xs: 'column', md: 'row' },
        overflow: 'hidden',
      }}
    >
      {/* Left panel with medical image */}
      <Box
        sx={{
          display: { xs: 'none', md: 'flex' },
          width: '50%',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <img 
          src={medicalImageUrl} 
          alt="Medical illustration" 
          style={{
            position: 'absolute',
            inset: 0,
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(135deg, rgba(15, 40, 71, 0.95), rgba(10, 21, 37, 0.9), rgba(6, 18, 36, 0.95))',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            padding: 5,
          }}
        >
          <Box sx={{ maxWidth: 500, color: 'white' }}>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Box 
                sx={{ 
                  background: 'linear-gradient(to right, #0369a1, #0ea5e9)',
                  padding: 1,
                  borderRadius: 2,
                  mr: 2,
                  boxShadow: '0 4px 12px rgba(14, 165, 233, 0.3)',
                }}
              >
                <Typography variant="h4" fontWeight="600">VD</Typography>
              </Box>
              <Typography variant="h4" fontWeight="bold">Vein Diagram</Typography>
            </Box>
            <Typography 
              variant="h5" 
              fontWeight="600"
              mb={3}
              sx={{ 
                background: 'linear-gradient(to right, #ffffff, #d1d5db)',
                backgroundClip: 'text',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              Advanced Vascular Diagnostics
            </Typography>
            <Typography variant="body1" mb={4} fontSize="1.125rem" lineHeight={1.6} color="rgba(229, 231, 235, 0.9)">
              Welcome back to Vein Diagram. Sign in to view your latest health insights
              and biomarker visualizations.
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, '&:hover': { '& svg': { color: '#0ea5e9' }, color: 'white' }, transition: 'all 0.2s ease-in-out', color: 'rgba(229, 231, 235, 0.9)' }}>
                <CheckCircle sx={{ color: '#0ea5e9' }} />
                <Typography>View your personalized health dashboard</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, '&:hover': { '& svg': { color: '#0ea5e9' }, color: 'white' }, transition: 'all 0.2s ease-in-out', color: 'rgba(229, 231, 235, 0.9)' }}>
                <CheckCircle sx={{ color: '#0ea5e9' }} />
                <Typography>Track biomarker changes over time</Typography>
              </Box>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, '&:hover': { '& svg': { color: '#0ea5e9' }, color: 'white' }, transition: 'all 0.2s ease-in-out', color: 'rgba(229, 231, 235, 0.9)' }}>
                <CheckCircle sx={{ color: '#0ea5e9' }} />
                <Typography>Access your securely stored test results</Typography>
              </Box>
            </Box>
          </Box>
        </Box>
      </Box>
      
      {/* Right panel with form */}
      <Box
        sx={{
          width: { xs: '100%', md: '50%' },
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
          background: 'linear-gradient(to bottom, #0A1525, #132238)',
          boxShadow: '0 0 20px rgba(0, 0, 0, 0.5)',
        }}
      >
        <Container maxWidth="sm" sx={{ py: 4, display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
          <Button 
            component={Link} 
            to="/" 
            startIcon={<ArrowBack />}
            sx={{ 
              alignSelf: 'flex-start', 
              mb: 5,
              color: 'text.secondary',
              '&:hover': { color: 'white' },
              transition: 'color 0.2s ease-in-out',
            }}
          >
            Back to website
          </Button>
          
          <Box sx={{ mb: 5, textAlign: { xs: 'center', sm: 'left' } }}>
            <Typography variant="h4" fontWeight="bold" color="white" mb={1}>
              Welcome back
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Sign in to your account to continue
            </Typography>
          </Box>
          
          {errorMessage && (
            <Alert 
              severity="error" 
              sx={{ 
                mb: 3, 
                bgcolor: 'rgba(127, 29, 29, 0.2)', 
                color: '#fecaca',
                border: '1px solid rgba(220, 38, 38, 0.3)',
                borderRadius: 2,
                animation: 'fadeIn 0.3s ease-in-out',
                '@keyframes fadeIn': {
                  '0%': { opacity: 0, transform: 'translateY(-10px)' },
                  '100%': { opacity: 1, transform: 'translateY(0)' },
                },
              }}
            >
              {errorMessage}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            <TextField
              fullWidth
              id="email"
              label="Email address"
              name="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              variant="outlined"
              InputLabelProps={{ 
                sx: { color: 'text.secondary' } 
              }}
              InputProps={{
                sx: {
                  bgcolor: 'rgba(15, 32, 54, 0.8)',
                  borderRadius: 2,
                  '&:hover': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(42, 58, 84, 0.8)',
                    }
                  },
                  '&.Mui-focused': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'primary.main',
                      borderWidth: 2,
                    }
                  },
                }
              }}
            />
            
            <TextField
              fullWidth
              id="password"
              label="Password"
              name="password"
              type={showPassword ? 'text' : 'password'}
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              variant="outlined"
              InputLabelProps={{ 
                sx: { color: 'text.secondary' } 
              }}
              InputProps={{
                sx: {
                  bgcolor: 'rgba(15, 32, 54, 0.8)',
                  borderRadius: 2,
                  '&:hover': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'rgba(42, 58, 84, 0.8)',
                    }
                  },
                  '&.Mui-focused': {
                    '& .MuiOutlinedInput-notchedOutline': {
                      borderColor: 'primary.main',
                      borderWidth: 2,
                    }
                  },
                },
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      sx={{ color: 'text.secondary', '&:hover': { color: 'white' } }}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                ),
              }}
              helperText={
                <Typography variant="caption" component={Link} to="/reset-password" sx={{ color: 'primary.main', '&:hover': { color: 'primary.light' }, display: 'block', textAlign: 'right', mt: 0.5 }}>
                  Forgot password?
                </Typography>
              }
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              disabled={isLoading}
              sx={{
                mt: 2,
                py: 1.5,
                background: 'linear-gradient(to right, #0284c7, #0ea5e9)',
                borderRadius: 2,
                fontWeight: 600,
                '&:hover': {
                  background: 'linear-gradient(to right, #0369a1, #0ea5e9)',
                  transform: 'translateY(-1px)',
                  boxShadow: '0 4px 12px rgba(14, 165, 233, 0.3)',
                },
                transition: 'all 0.2s ease-in-out',
              }}
            >
              {isLoading ? (
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
                  Signing in...
                </Box>
              ) : 'Sign in'}
            </Button>
          </Box>
          
          <Box sx={{ my: 4, position: 'relative' }}>
            <Divider sx={{ '&::before, &::after': { borderColor: 'rgba(42, 58, 84, 0.5)' } }}>
              <Typography variant="body2" color="text.secondary" sx={{ px: 2 }}>
                Or continue with
              </Typography>
            </Divider>
          </Box>
          
          <Button
            fullWidth
            variant="outlined"
            startIcon={
              <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google logo" height="18" width="18" />
            }
            sx={{
              py: 1.5,
              borderColor: 'rgba(42, 58, 84, 0.5)',
              color: 'white',
              borderRadius: 2,
              '&:hover': {
                borderColor: 'rgba(42, 58, 84, 0.8)',
                bgcolor: 'rgba(42, 58, 84, 0.2)',
              },
            }}
          >
            Sign in with Google
          </Button>
          
          <Box sx={{ mt: 4, textAlign: 'center', flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'flex-end' }}>
            <Typography variant="body2" color="text.secondary">
              Don't have an account?{' '}
              <Link to="/signup" style={{ color: '#0ea5e9', fontWeight: 500, textDecoration: 'none' }}>
                Sign up
              </Link>
            </Typography>
          </Box>
          
          <Box component="footer" sx={{ mt: 'auto', pt: 4, pb: 2, textAlign: 'center', borderTop: '1px solid rgba(42, 58, 84, 0.5)' }}>
            <Typography variant="caption" color="text.secondary">
              © {new Date().getFullYear()} Vein Diagram. All rights reserved.
            </Typography>
            <Box sx={{ mt: 1, display: 'flex', justifyContent: 'center', gap: 3 }}>
              <Link to="/terms" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.75rem' }}>Terms</Link>
              <Link to="/privacy" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.75rem' }}>Privacy</Link>
              <Link to="/support" style={{ color: '#94a3b8', textDecoration: 'none', fontSize: '0.75rem' }}>Support</Link>
            </Box>
          </Box>
        </Container>
      </Box>
    </Box>
  );
};

export default LoginForm; 