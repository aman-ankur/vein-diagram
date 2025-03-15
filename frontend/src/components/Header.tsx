import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import Container from '@mui/material/Container';

/**
 * Simplified Header component for the application
 */
const Header: React.FC = () => {
  console.log('Header component rendering');
  
  return (
    <AppBar position="static" color="default" elevation={1}>
      <Container maxWidth="xl">
        <Toolbar>
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            sx={{
              mr: 2,
              fontWeight: 700,
              color: 'inherit',
              textDecoration: 'none',
              flexGrow: 1,
            }}
          >
            Vein Diagram
          </Typography>
          
          <Box>
            <Button
              component={RouterLink}
              to="/"
              color="inherit"
              sx={{ mr: 1 }}
            >
              Home
            </Button>
            
            <Button
              component={RouterLink}
              to="/upload"
              color="inherit"
              sx={{ mr: 1 }}
            >
              Upload
            </Button>
            
            <Button
              component={RouterLink}
              to="/biomarkers"
              color="inherit"
            >
              Biomarkers
            </Button>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Header; 