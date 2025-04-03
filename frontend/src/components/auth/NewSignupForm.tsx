import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { 
  Box, 
  TextField, 
  Button, 
  Typography, 
  Checkbox,
  FormControlLabel,
  InputAdornment, 
  IconButton,
  Grid,
  Divider,
  CircularProgress
} from '@mui/material';
import { Visibility, VisibilityOff } from '@mui/icons-material';
import GoogleIcon from '@mui/icons-material/Google';

const NewSignupForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { signUp, signInWithGoogle } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (!agreedToTerms) {
      setError('You must agree to the Terms of Service and Privacy Policy');
      return;
    }
    
    try {
      setLoading(true);
      await signUp(email, password);
      // Redirect to login after successful signup
      navigate('/login'); 
    } catch (err: any) {
      setError(err.message || 'Failed to create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleGoogleSignIn = async () => {
    setError('');
    setLoading(true);
    try {
      await signInWithGoogle();
      // Google sign-in handles redirection via callback
    } catch (err: any) {
      setError(err.message || 'Failed to sign in with Google. Please try again.');
      setLoading(false);
    }
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
      {error && (
        <Box 
          sx={{
            p: 2,
            mb: 3,
            bgcolor: 'rgba(220, 38, 38, 0.1)',
            color: '#fca5a5',
            borderRadius: 1,
            border: '1px solid rgba(220, 38, 38, 0.3)',
          }}
        >
          <Typography variant="body2">{error}</Typography>
        </Box>
      )}

      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
            First name
          </Typography>
          <TextField
            fullWidth
            id="firstName"
            placeholder="Enter your first name"
            value={firstName}
            onChange={(e) => setFirstName(e.target.value)}
            sx={{
              '.MuiOutlinedInput-root': {
                bgcolor: 'rgba(15, 23, 42, 0.6)',
                borderRadius: 1,
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'primary.main',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'primary.main',
                  borderWidth: 2,
                }
              }
            }}
          />
        </Grid>
        <Grid item xs={12} sm={6}>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
            Last name
          </Typography>
          <TextField
            fullWidth
            id="lastName"
            placeholder="Enter your last name"
            value={lastName}
            onChange={(e) => setLastName(e.target.value)}
            sx={{
              '.MuiOutlinedInput-root': {
                bgcolor: 'rgba(15, 23, 42, 0.6)',
                borderRadius: 1,
                '&:hover .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'primary.main',
                },
                '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                  borderColor: 'primary.main',
                  borderWidth: 2,
                }
              }
            }}
          />
        </Grid>
      </Grid>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
        Email
      </Typography>
      <TextField
        fullWidth
        id="email"
        type="email"
        placeholder="Enter your email address"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        required
        sx={{
          mb: 3,
          '.MuiOutlinedInput-root': {
            bgcolor: 'rgba(15, 23, 42, 0.6)',
            borderRadius: 1,
            '&:hover .MuiOutlinedInput-notchedOutline': {
              borderColor: 'primary.main',
            },
            '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
              borderColor: 'primary.main',
              borderWidth: 2,
            }
          }
        }}
      />

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
        Password
      </Typography>
      <TextField
        fullWidth
        id="password"
        type={showPassword ? 'text' : 'password'}
        placeholder="Create a password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        sx={{
          mb: 3,
          '.MuiOutlinedInput-root': {
            bgcolor: 'rgba(15, 23, 42, 0.6)',
            borderRadius: 1,
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

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1, fontWeight: 500 }}>
        Confirm password
      </Typography>
      <TextField
        fullWidth
        id="confirmPassword"
        type={showConfirmPassword ? 'text' : 'password'}
        placeholder="Confirm your password"
        value={confirmPassword}
        onChange={(e) => setConfirmPassword(e.target.value)}
        required
        sx={{
          mb: 3,
          '.MuiOutlinedInput-root': {
            bgcolor: 'rgba(15, 23, 42, 0.6)',
            borderRadius: 1,
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
                aria-label={showConfirmPassword ? "Hide confirm password" : "Show confirm password"}
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                edge="end"
                sx={{ color: 'text.secondary' }}
              >
                {showConfirmPassword ? <VisibilityOff /> : <Visibility />}
              </IconButton>
            </InputAdornment>
          )
        }}
      />
      
      <FormControlLabel
        control={
          <Checkbox 
            checked={agreedToTerms}
            onChange={(e) => setAgreedToTerms(e.target.checked)}
            sx={{ 
              color: 'text.secondary',
              '&.Mui-checked': {
                color: 'primary.main',
              }
            }}
          />
        }
        label={
          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.875rem' }}>
            I agree to the{' '}
            <Link to="/terms" style={{ color: '#6366f1', textDecoration: 'none' }}>
              Terms of Service
            </Link>{' '}
            and{' '}
            <Link to="/privacy" style={{ color: '#6366f1', textDecoration: 'none' }}>
              Privacy Policy
            </Link>
          </Typography>
        }
        sx={{ mb: 3 }}
      />

      <Button
        type="submit"
        fullWidth
        variant="contained"
        disabled={loading}
        sx={{
          py: 1.4,
          mb: 3,
          bgcolor: 'primary.main',
          borderRadius: 1,
          fontWeight: 600,
          '&:hover': {
            bgcolor: 'primary.dark',
            transform: 'translateY(-1px)',
            boxShadow: '0 4px 12px rgba(99, 102, 241, 0.3)'
          },
          transition: 'all 0.2s ease-in-out'
        }}
      >
        {loading ? (
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <CircularProgress size={20} color="inherit" sx={{ mr: 1 }} />
            Creating Account...
          </Box>
        ) : 'Create Account'}
      </Button>

      <Divider sx={{ mb: 3 }}>
        <Typography variant="caption" color="text.secondary">
          Or continue with
        </Typography>
      </Divider>
      
      <Button
        fullWidth
        variant="outlined"
        startIcon={<GoogleIcon sx={{ height: 18 }} />}
        onClick={handleGoogleSignIn}
        disabled={loading}
        sx={{
          py: 1.2,
          borderColor: 'rgba(99, 102, 241, 0.3)',
          color: 'white',
          borderRadius: 1,
          '&:hover': {
            borderColor: 'primary.main',
            bgcolor: 'rgba(99, 102, 241, 0.1)',
          },
          mb: 3
        }}
      >
        Sign up with Google
      </Button>

      <Typography variant="body2" color="text.secondary" textAlign="center">
        Already have an account?{' '}
        <Link to="/login" style={{ color: '#6366f1', textDecoration: 'none' }}>
          Sign in
        </Link>
      </Typography>
    </Box>
  );
};

export default NewSignupForm;
