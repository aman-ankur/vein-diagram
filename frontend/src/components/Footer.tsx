import React from 'react';
import Box from '@mui/material/Box';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';

/**
 * Simplified Footer component for the application
 */
const Footer: React.FC = () => {
  console.log('Footer component rendering');
  
  return (
    <Box
      component="footer"
      sx={{
        py: 3,
        px: 2,
        mt: 'auto',
        backgroundColor: (theme) => theme.palette.grey[100],
      }}
    >
      <Container maxWidth="lg">
        <Typography variant="body2" color="text.secondary" align="center">
          © {new Date().getFullYear()} Vein Diagram. All rights reserved.
        </Typography>
      </Container>
    </Box>
  );
};

export default Footer; 