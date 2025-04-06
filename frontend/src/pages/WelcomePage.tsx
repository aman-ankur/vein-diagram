import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Container, Typography, Paper, Box } from '@mui/material';

const WelcomePage: React.FC = () => {
  const navigate = useNavigate();

  const handleCreateProfile = () => {
    navigate('/profiles');
  };

  const handleSkip = () => {
    navigate('/dashboard'); // Navigate to dashboard even if it might be empty/blocked for now
  };

  return (
    <Container component="main" maxWidth="sm" sx={{ mt: 8 }}>
      <Paper elevation={3} sx={{ p: 4, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Typography component="h1" variant="h4" gutterBottom sx={{ mb: 2 }}>
          Welcome to Vein Diagram!
        </Typography>
        <Typography variant="body1" align="center" sx={{ mb: 4 }}>
          Unlock insights from your blood tests. Visualize trends, understand your biomarkers, and take control of your health journey.
          <br /><br />
          To get started, let's create your first health profile.
        </Typography>
        <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 2 }}>
          <Button
            variant="contained"
            color="primary"
            size="large"
            onClick={handleCreateProfile}
            fullWidth
          >
            Create Your First Profile
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            size="large"
            onClick={handleSkip}
            fullWidth
          >
            Skip for Now
          </Button>
        </Box>
      </Paper>
    </Container>
  );
};

export default WelcomePage;
