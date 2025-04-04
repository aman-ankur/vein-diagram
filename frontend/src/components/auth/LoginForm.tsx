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
  
  const { signIn, signInWithGoogle } = useAuth();
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

  const handleGoogleSignIn = async () => {
    try {
      setIsLoading(true);
      setErrorMessage('');
      
      const { error } = await signInWithGoogle();
      
      if (error) {
        throw error;
      }
      
      // The redirect will be handled by Supabase automatically, no need to navigate
    } catch (error: any) {
      console.error('Google sign in error:', error);
      setErrorMessage(error.message || 'Failed to sign in with Google');
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

            <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontWeight: 500, textAlign: 'center' }}>
              Or continue with
            </Typography>
            
            <Stack direction="row" spacing={2} sx={{ width: '100%', mb: 3 }}>
              <Button 
                fullWidth
                variant="outlined"
                startIcon={
                  isLoading ? (
                    <CircularProgress size={20} color="inherit" />
                  ) : (
                    <svg width="18" height="18" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
                      <path fill="#FFC107" d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,20-8.955,20-20C44,22.659,43.862,21.35,43.611,20.083z"></path>
                      <path fill="#FF3D00" d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.154,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.656,8.337,6.306,14.691z"></path>
                      <path fill="#4CAF50" d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.715,36,24,36c-5.202,0-9.619-3.317-11.283-7.946l-6.522,5.025C9.505,39.556,16.227,44,24,44z"></path>
                      <path fill="#1976D2" d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"></path>
                    </svg>
                  )
                }
                onClick={handleGoogleSignIn}
                disabled={isLoading}
                sx={{
                  py: 1.2,
                  borderColor: 'rgba(99, 102, 241, 0.3)',
                  color: 'white',
                  borderRadius: 2,
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  backdropFilter: 'blur(4px)',
                  fontWeight: 500,
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'rgba(99, 102, 241, 0.1)',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.2)'
                  },
                  '&:active': {
                    transform: 'translateY(0)',
                    boxShadow: 'none',
                  },
                  transition: 'all 0.2s ease-in-out',
                  position: 'relative',
                  overflow: 'hidden',
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    background: 'linear-gradient(rgba(255,255,255,0.1), rgba(255,255,255,0))',
                    opacity: 0,
                    transition: 'opacity 0.2s ease-in-out',
                  },
                  '&:hover::after': {
                    opacity: 1,
                  }
                }}
              >
                Google
              </Button>
              <Button 
                fullWidth
                variant="outlined"
                startIcon={
                  <svg width="18" height="22" viewBox="0 0 170 170" fill="white" xmlns="http://www.w3.org/2000/svg">
                    <path d="M150.37 130.25c-2.45 5.66-5.35 10.87-8.71 15.66-4.58 6.53-8.33 11.05-11.22 13.56-4.48 4.12-9.28 6.23-14.42 6.35-3.69 0-8.14-1.05-13.32-3.18-5.197-2.12-9.973-3.17-14.34-3.17-4.58 0-9.492 1.05-14.746 3.17-5.262 2.13-9.501 3.24-12.742 3.35-4.929 0.21-9.842-1.96-14.746-6.52-3.13-2.73-7.045-7.41-11.735-14.04-5.032-7.08-9.169-15.29-12.41-24.65-3.471-10.11-5.211-19.9-5.211-29.378 0-10.857 2.346-20.221 7.045-28.068 3.693-6.303 8.606-11.275 14.755-14.925s12.793-5.51 19.948-5.629c3.915 0 9.049 1.211 15.429 3.591 6.362 2.388 10.447 3.599 12.238 3.599 1.339 0 5.877-1.416 13.57-4.239 7.275-2.618 13.415-3.702 18.445-3.275 13.63 1.1 23.87 6.473 30.68 16.153-12.19 7.386-18.22 17.731-18.1 31.002 0.11 10.337 3.86 18.939 11.23 25.769 3.34 3.17 7.07 5.62 11.22 7.36-0.9 2.61-1.85 5.11-2.86 7.51zM119.11 7.24c0 8.102-2.96 15.667-8.86 22.669-7.12 8.324-15.732 13.134-25.071 12.375-0.119-0.972-0.188-1.995-0.188-3.07 0-7.778 3.386-16.102 9.399-22.908 3.002-3.446 6.82-6.311 11.45-8.597 4.62-2.253 8.99-3.498 13.1-3.71 0.12 1.083 0.17 2.166 0.17 3.241z"/>
                  </svg>
                }
                sx={{
                  py: 1.2,
                  borderColor: 'rgba(99, 102, 241, 0.3)',
                  color: 'white',
                  borderRadius: 2,
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  backdropFilter: 'blur(4px)',
                  fontWeight: 500,
                  '&:hover': {
                    borderColor: 'primary.main',
                    bgcolor: 'rgba(99, 102, 241, 0.1)',
                    transform: 'translateY(-1px)',
                    boxShadow: '0 4px 12px rgba(99, 102, 241, 0.2)'
                  },
                  '&:active': {
                    transform: 'translateY(0)',
                    boxShadow: 'none',
                  },
                  transition: 'all 0.2s ease-in-out',
                  position: 'relative',
                  overflow: 'hidden',
                  '&::after': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '100%',
                    height: '100%',
                    background: 'linear-gradient(rgba(255,255,255,0.1), rgba(255,255,255,0))',
                    opacity: 0,
                    transition: 'opacity 0.2s ease-in-out',
                  },
                  '&:hover::after': {
                    opacity: 1,
                  }
                }}
              >
                Apple
              </Button>
            </Stack>

            <Button
              fullWidth
              variant="text"
              color="inherit"
              sx={{
                py: 1.2,
                color: 'text.secondary',
                borderRadius: 2,
                backgroundColor: 'rgba(15, 23, 42, 0.4)',
                backdropFilter: 'blur(4px)',
                border: '1px solid rgba(99, 102, 241, 0.1)',
                fontWeight: 500,
                '&:hover': {
                  backgroundColor: 'rgba(15, 23, 42, 0.6)',
                  borderColor: 'rgba(99, 102, 241, 0.2)',
                  transform: 'translateY(-1px)',
                },
                '&:active': {
                  transform: 'translateY(0)',
                },
                transition: 'all 0.2s ease-in-out'
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