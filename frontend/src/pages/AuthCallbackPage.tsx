import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../services/supabaseClient';
import { Box, CircularProgress, Typography, Alert, Paper, Container } from '@mui/material';

const AuthCallbackPage = () => {
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [processing, setProcessing] = useState<boolean>(true);

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        console.log("Auth callback page loaded");
        
        // Extract the hash fragment from the URL (used by Supabase auth)
        const hashFragment = window.location.hash;
        console.log("Hash fragment present:", !!hashFragment);
        
        if (!hashFragment) {
          throw new Error('No auth hash fragment found in URL');
        }

        // The correct way to handle the OAuth callback with Supabase
        // is to call getSession(), which will parse the hash and set up the session
        console.log("Calling supabase.auth.getSession()");
        const { data, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError) {
          console.error("Session error:", sessionError);
          throw sessionError;
        }

        console.log("Session retrieved successfully:", !!data.session);
        
        if (!data.session) {
          throw new Error('No session data returned from Supabase');
        }

        console.log("Authentication successful, redirecting to dashboard");
        // Redirect to dashboard upon successful authentication
        navigate('/dashboard', { replace: true });
      } catch (err: any) {
        console.error('Auth callback error:', err);
        setError(err.message || 'Authentication failed');
        setProcessing(false);
        
        // Redirect to login after a short delay
        setTimeout(() => {
          navigate('/login', { replace: true });
        }, 5000);
      }
    };

    handleAuthCallback();
  }, [navigate]);

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
                Completing Authentication
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}>
                <CircularProgress />
              </Box>
              <Typography variant="body1">
                Please wait while we complete the sign-in process...
              </Typography>
            </>
          )}
        </Paper>
      </Box>
    </Container>
  );
};

export default AuthCallbackPage; 