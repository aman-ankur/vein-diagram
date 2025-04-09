import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../services/supabaseClient';
import { Box, CircularProgress, Typography, Alert, Paper, Container } from '@mui/material';

const AuthCallbackPage: React.FC = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Supabase handles the session automatically based on the URL hash
        const hashFragment = window.location.hash;
        if (!hashFragment) {
          // If there's no hash, maybe it was a direct navigation?
          // Redirect to login or home page
          navigate('/login');
          return;
        }

        const { data, error: sessionError } = await supabase.auth.getSession();

        if (sessionError) {
          throw new Error(sessionError.message || 'Failed to get session after callback.');
        }

        if (data.session) {
          // setSession(data.session); // REMOVED: AuthProvider handles this via onAuthStateChange

          // Check for redirect path stored before authentication
          const redirectPath = sessionStorage.getItem('redirectPath') || '/';
          sessionStorage.removeItem('redirectPath'); // Clear the stored path
          navigate(redirectPath, { replace: true });
        } else {
          // No session could be established, which is unexpected after a callback
          throw new Error('No session established after authentication callback.');
        }
      } catch (err: any) {
        setError(`Authentication failed: ${err.message || 'Unknown error occurred.'}`);
      }
    };

    handleAuthCallback();
    // We only want this to run once when the component mounts
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [navigate]); // Remove setSession from dependencies

  // Render a loading state or error
  return (
    <Container maxWidth="sm">
      <Box sx={{ 
        display: 'flex', 
        flexDirection: 'column',
        alignItems: 'center', 
        justifyContent: 'center', 
        minHeight: '80vh'
      }}>
        <Paper 
          elevation={3} 
          sx={{ 
            p: 4, 
            width: '100%', 
            borderRadius: 2,
            textAlign: 'center' 
          }}
        >
          {error ? (
            <>
              <Typography variant="h5" color="error" gutterBottom>
                Authentication Error
              </Typography>
              <Alert severity="error" sx={{ my: 2 }}>
                {error}
              </Alert>
              <Typography variant="body2" color="text.secondary">
                Redirecting you to the login page in 5 seconds...
              </Typography>
            </>
          ) : (
            <>
              <Typography variant="h5" gutterBottom>
                {loading ? "Completing Authentication" : "Authentication Complete"}
              </Typography>
              {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
                  <CircularProgress />
                </Box>
              )}
              <Typography variant="body1">
                {loading 
                  ? "Please wait while we complete the sign-in process..." 
                  : "Redirecting you to the dashboard..."}
              </Typography>
            </>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default AuthCallbackPage; 