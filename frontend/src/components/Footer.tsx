import React from 'react';
import { Box, Container, Typography, Link, Grid, Divider } from '@mui/material';

const Footer: React.FC = () => {
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
        <Divider sx={{ mb: 3 }} />
        
        <Grid container spacing={4}>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Vein Diagram
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Advanced biomarker analysis and visualization for your lab reports.
            </Typography>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Quick Links
            </Typography>
            <Link href="/" color="inherit" sx={{ display: 'block', mb: 1 }}>
              Home
            </Link>
            <Link href="/upload" color="inherit" sx={{ display: 'block', mb: 1 }}>
              Upload Lab Report
            </Link>
            <Link href="/biomarkers" color="inherit" sx={{ display: 'block', mb: 1 }}>
              Biomarker Dashboard
            </Link>
          </Grid>
          
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Resources
            </Typography>
            <Link href="#" color="inherit" sx={{ display: 'block', mb: 1 }}>
              About Us
            </Link>
            <Link href="#" color="inherit" sx={{ display: 'block', mb: 1 }}>
              Privacy Policy
            </Link>
            <Link href="#" color="inherit" sx={{ display: 'block', mb: 1 }}>
              Terms of Service
            </Link>
          </Grid>
        </Grid>
        
        <Box mt={3} pt={3} borderTop={1} borderColor="divider">
          <Typography variant="body2" color="text.secondary" align="center">
            {'© '}
            {new Date().getFullYear()}
            {' Vein Diagram. All rights reserved.'}
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer; 