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
  Stack,
  CircularProgress
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import veinNetworkLogo from '../../assets/vein-network-logo.jpeg';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loginStage, setLoginStage] = useState<'email' | 'password'>('email');
  
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get the redirect path from location state, or default to dashboard
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const handleSubmitEmail = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setErrorMessage('Please enter your email');
      return;
    }
    
    // In a real implementation, you might validate if the email exists first
    setLoginStage('password');
    setErrorMessage('');
  };

  const handleSubmitPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!password) {
      setErrorMessage('Please enter your password');
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
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(to bottom, #0f172a, #1e293b)',
        backgroundSize: 'cover',
        position: 'relative',
        // Add subtle dot pattern overlay
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'radial-gradient(#ffffff11 1px, transparent 1px)',
          backgroundSize: '30px 30px',
          zIndex: 1,
        },
        // Add a subtle glow in the background
        '&::after': {
          content: '""',
          position: 'absolute',
          top: '30%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '500px',
          height: '500px',
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, rgba(99, 102, 241, 0.05) 40%, transparent 70%)',
          filter: 'blur(60px)',
          zIndex: 0,
        }
      }}
    >
      <Paper
        elevation={5}
        sx={{
          width: '100%',
          maxWidth: 450,
          p: 4,
          position: 'relative',
          zIndex: 2,
          borderRadius: 4,
          background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.98))',
          backdropFilter: 'blur(10px)',
          border: '1px solid rgba(99, 102, 241, 0.1)',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3), 0 0 40px rgba(99, 102, 241, 0.15)'
        }}
      >
        {/* Logo container with improved visibility */}
        <Box 
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            mb: 6,
            mt: 2,
            position: 'relative',
          }}
        >
          {/* Outer glow effect */}
          <Box
            sx={{
              position: 'absolute',
              width: 120,
              height: 120,
              borderRadius: '50%',
              background: 'radial-gradient(circle, rgba(104, 112, 255, 0.15) 0%, rgba(104, 112, 255, 0.05) 70%, transparent 100%)',
              filter: 'blur(15px)',
              zIndex: 0,
            }}
          />
          
          {/* Logo container */}
          <Box
            sx={{
              width: 80,
              height: 80,
              borderRadius: '50%',
              position: 'relative',
              background: 'rgba(15, 23, 42, 0.7)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '1px solid rgba(104, 112, 255, 0.2)',
              backdropFilter: 'blur(4px)',
              zIndex: 1,
              boxShadow: '0 0 20px rgba(104, 112, 255, 0.2)',
            }}
          >
            {/* Inner glow effect */}
            <Box
              sx={{
                position: 'absolute',
                inset: 0,
                borderRadius: '50%',
                background: 'radial-gradient(circle, rgba(104, 112, 255, 0.15) 0%, transparent 70%)',
                opacity: 0.8,
              }}
            />
            
            {/* The logo image */}
            <img
              src={veinNetworkLogo}
              alt="Vein Diagram Network"
              style={{
                width: '70%',
                height: '70%',
                objectFit: 'contain',
                position: 'relative',
                zIndex: 2,
                filter: 'brightness(1.2)',
              }}
            />
            
            {/* Subtle pulsing animation */}
            <Box
              sx={{
                position: 'absolute',
                inset: -5,
                borderRadius: '50%',
                border: '1px solid rgba(104, 112, 255, 0.3)',
                animation: 'pulse 3s infinite ease-in-out',
                '@keyframes pulse': {
                  '0%': { opacity: 0.3, transform: 'scale(0.95)' },
                  '50%': { opacity: 0.6, transform: 'scale(1.05)' },
                  '100%': { opacity: 0.3, transform: 'scale(0.95)' },
                },
              }}
            />
          </Box>
        </Box>

        <Box sx={{ textAlign: 'center', mb: 5 }}>
          <Typography variant="h4" fontWeight="700" color="white" gutterBottom>
            Welcome to Vein Diagram
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ opacity: 0.8 }}>
            AI-Powered Health Analytics Platform
          </Typography>
        </Box>

        {errorMessage && (
          <Box 
            sx={{
              p: 2,
              mb: 3,
              bgcolor: 'rgba(220, 38, 38, 0.1)',
              color: '#fca5a5',
              borderRadius: 2,
              border: '1px solid rgba(220, 38, 38, 0.3)',
              animation: 'fadeIn 0.3s ease-in',
              '@keyframes fadeIn': {
                from: { opacity: 0, transform: 'translateY(-10px)' },
                to: { opacity: 1, transform: 'translateY(0)' }
              }
            }}
          >
            <Typography variant="body2">{errorMessage}</Typography>
          </Box>
        )}

        {loginStage === 'email' ? (
          <Box component="form" onSubmit={handleSubmitEmail} sx={{ width: '100%' }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
              Email
            </Typography>
            <TextField
              fullWidth
              id="email"
              placeholder="Enter your email address..."
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              sx={{
                mb: 3,
                '.MuiOutlinedInput-root': {
                  bgcolor: 'rgba(15, 23, 42, 0.7)',
                  borderRadius: 2,
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'primary.main',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'primary.main',
                    borderWidth: 2,
                  }
                }
              }}
              InputProps={{
                endAdornment: email && (
                  <InputAdornment position="end">
                    <Box 
                      sx={{ 
                        width: 16, 
                        height: 16, 
                        bgcolor: 'success.main', 
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      <Typography variant="caption" color="white" sx={{ lineHeight: 1, fontWeight: 'bold' }}>✓</Typography>
                    </Box>
                  </InputAdornment>
                )
              }}
            />

            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{
                py: 1.5,
                mb: 3,
                bgcolor: 'primary.main',
                borderRadius: 2,
                fontWeight: 600,
                '&:hover': {
                  bgcolor: 'primary.dark',
                  transform: 'translateY(-2px)',
                  boxShadow: '0 6px 20px rgba(99, 102, 241, 0.4)'
                },
                transition: 'all 0.2s ease-in-out'
              }}
            >
              Continue with email
            </Button>

            <Stack direction="row" spacing={2} sx={{ width: '100%', mb: 3 }}>
              <Button 
                fullWidth
                variant="outlined"
                startIcon={
                  <img src="https://developers.google.com/identity/images/g-logo.png" alt="Google logo" height="18" width="18" />
                }
                sx={{
                  py: 1.2,
                  borderColor: 'rgba(99, 102, 241, 0.3)',
                  color: 'white',
                  borderRadius: 2,
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'rgba(99, 102, 241, 0.1)',
                  },
                }}
              >
                Google
              </Button>
              <Button 
                fullWidth
                variant="outlined"
                startIcon={
                  <img src="https://upload.wikimedia.org/wikipedia/commons/f/fa/Apple_logo_black.svg" alt="Apple logo" height="18" width="18" style={{ filter: 'invert(1)' }} />
                }
                sx={{
                  py: 1.2,
                  borderColor: 'rgba(99, 102, 241, 0.3)',
                  color: 'white',
                  borderRadius: 2,
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'rgba(99, 102, 241, 0.1)',
                  },
                }}
              >
                Apple
              </Button>
            </Stack>

            <Divider sx={{ my: 2 }}>
              <Typography variant="caption" color="text.secondary">
                or continue with SSO
              </Typography>
            </Divider>

            <Button
              fullWidth
              variant="text"
              color="inherit"
              sx={{
                py: 1.2,
                color: 'text.secondary',
                borderRadius: 2,
                '&:hover': {
                  bgcolor: 'rgba(255, 255, 255, 0.05)',
                },
              }}
            >
              Enterprise Single Sign-On
            </Button>
          </Box>
        ) : (
          <Box component="form" onSubmit={handleSubmitPassword} sx={{ width: '100%' }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Password for {email}
            </Typography>
            <TextField
              fullWidth
              id="password"
              type={showPassword ? "text" : "password"}
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              sx={{
                mb: 3,
                '.MuiOutlinedInput-root': {
                  bgcolor: 'rgba(15, 23, 42, 0.7)',
                  borderRadius: 2,
                  '&:hover .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'primary.main',
                  },
                  '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                    borderColor: 'primary.main',
                    borderWidth: 2,
                  }
                }
              }}
              InputProps={{
                endAdornment: (
                  <InputAdornment position="end">
                    <IconButton
                      aria-label={showPassword ? "Hide password" : "Show password"}
                      onClick={() => setShowPassword(!showPassword)}
                      edge="end"
                      sx={{ color: 'text.secondary' }}
                    >
                      {showPassword ? <VisibilityOff /> : <Visibility />}
                    </IconButton>
                  </InputAdornment>
                )
              }}
            />

            <Stack direction="row" spacing={2} sx={{ width: '100%', mb: 2 }}>
              <Button
                type="submit"
                fullWidth
                variant="contained"
                disabled={isLoading}
                sx={{
                  py: 1.5,
                  bgcolor: 'primary.main',
                  borderRadius: 2,
                  fontWeight: 600,
                  '&:hover': {
                    bgcolor: 'primary.dark',
                    transform: 'translateY(-2px)',
                    boxShadow: '0 6px 20px rgba(99, 102, 241, 0.4)'
                  },
                  transition: 'all 0.2s ease-in-out'
                }}
              >
                {isLoading ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  'Sign in'
                )}
              </Button>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => setLoginStage('email')}
                sx={{
                  py: 1.5,
                  borderColor: 'rgba(99, 102, 241, 0.3)',
                  color: 'white',
                  borderRadius: 2,
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'rgba(99, 102, 241, 0.1)',
                  },
                }}
              >
                Back
              </Button>
            </Stack>

            <Typography variant="body2" color="text.secondary" textAlign="center" sx={{ mt: 2 }}>
              <Link to="/reset-password" style={{ color: '#6366f1', textDecoration: 'none' }}>
                Forgot password?
              </Link>
            </Typography>
          </Box>
        )}

        <Box sx={{ mt: 4, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            Don't have an account?{' '}
            <Link to="/signup" style={{ color: '#6366f1', textDecoration: 'none' }}>
              Sign up
            </Link>
          </Typography>
        </Box>
      </Paper>
    </Box>
  );
};

export default LoginForm; 