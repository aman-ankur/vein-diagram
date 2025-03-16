import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme, responsiveFontSizes } from '@mui/material';
import App from './App';
import './styles/global.css';

// Create a dark, sleek, futuristic theme
const baseTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      light: '#6573c3',
      main: '#2c3e50', // Darker blue for primary
      dark: '#1a2639',
      contrastText: '#ffffff',
    },
    secondary: {
      light: '#33eaff',
      main: '#00b8d4', // Bright cyan for accents
      dark: '#0088a3',
      contrastText: '#ffffff',
    },
    background: {
      default: '#121212', // Very dark background
      paper: '#1e1e1e',   // Dark paper background
    },
    error: {
      main: '#ff5252',
    },
    success: {
      main: '#69f0ae',
    },
    warning: {
      main: '#ffc107',
    },
    info: {
      main: '#64b5f6',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0bec5',
    },
    grey: {
      50: '#fafafa',
      100: '#f5f5f5',
      200: '#eeeeee',
      300: '#e0e0e0',
      400: '#bdbdbd',
      500: '#9e9e9e',
      600: '#757575',
      700: '#616161',
      800: '#424242',
      900: '#212121',
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      'Roboto',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontWeight: 700,
      fontSize: '3rem',
      lineHeight: 1.2,
      letterSpacing: '-0.01562em',
    },
    h2: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
      letterSpacing: '-0.00833em',
    },
    h3: {
      fontWeight: 600,
      fontSize: '2rem',
      lineHeight: 1.2,
      letterSpacing: '0em',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.2,
      letterSpacing: '0.00735em',
    },
    h5: {
      fontWeight: 600,
      fontSize: '1.25rem',
      lineHeight: 1.2,
      letterSpacing: '0em',
    },
    h6: {
      fontWeight: 600,
      fontSize: '1rem',
      lineHeight: 1.2,
      letterSpacing: '0.0075em',
    },
    subtitle1: {
      fontWeight: 500,
      fontSize: '1rem',
      lineHeight: 1.5,
      letterSpacing: '0.00938em',
    },
    subtitle2: {
      fontWeight: 500,
      fontSize: '0.875rem',
      lineHeight: 1.5,
      letterSpacing: '0.00714em',
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      letterSpacing: '0.00938em',
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
      letterSpacing: '0.01071em',
    },
    button: {
      fontWeight: 600,
      fontSize: '0.875rem',
      lineHeight: 1.75,
      letterSpacing: '0.02857em',
      textTransform: 'none',
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.66,
      letterSpacing: '0.03333em',
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 600,
      lineHeight: 2.66,
      letterSpacing: '0.08333em',
      textTransform: 'uppercase',
    },
  },
  shape: {
    borderRadius: 12, // More rounded corners for futuristic look
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 24px',
          transition: 'all 0.2s ease-in-out',
          boxShadow: 'none',
          position: 'relative',
          overflow: 'hidden',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 8px 15px rgba(0, 184, 212, 0.2)',
            '&::after': {
              opacity: 1,
            },
          },
          '&::after': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            background: 'linear-gradient(rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0))',
            opacity: 0,
            transition: 'opacity 0.2s ease-in-out',
          },
        },
        contained: {
          boxShadow: '0 4px 8px rgba(0, 0, 0, 0.2)',
        },
        outlined: {
          borderWidth: 1.5,
          '&:hover': {
            borderWidth: 1.5,
            boxShadow: '0 0 12px rgba(0, 184, 212, 0.5)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 8px 20px rgba(0, 0, 0, 0.2)',
          transition: 'all 0.3s ease',
          background: 'linear-gradient(145deg, #1e1e1e, #2d2d2d)',
          backdropFilter: 'blur(10px)',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.3)',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.2)',
          backdropFilter: 'blur(10px)',
          background: 'rgba(30, 30, 30, 0.8)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
        },
        elevation1: {
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        },
        elevation2: {
          boxShadow: '0 6px 16px rgba(0, 0, 0, 0.18)',
        },
        elevation3: {
          boxShadow: '0 8px 20px rgba(0, 0, 0, 0.2)',
        },
        elevation4: {
          boxShadow: '0 10px 24px rgba(0, 0, 0, 0.22)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 12,
            transition: 'all 0.2s ease',
            '&:hover fieldset': {
              borderColor: '#00b8d4',
              boxShadow: '0 0 8px rgba(0, 184, 212, 0.3)',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#00b8d4',
              boxShadow: '0 0 12px rgba(0, 184, 212, 0.4)',
            },
          },
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        },
        head: {
          fontWeight: 600,
          backgroundColor: 'rgba(0, 0, 0, 0.2)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          transition: 'all 0.2s ease',
          '&:hover': {
            boxShadow: '0 2px 8px rgba(0, 184, 212, 0.3)',
          },
        },
      },
    },
  },
});

// Make typography responsive
export const theme = responsiveFontSizes(baseTheme);

// Log to console to verify script is running
console.log('main.tsx is executing - With Enhanced Dark UI Theme');

// Function to attempt rendering with different methods
function renderApp() {
  const rootElement = document.getElementById('root');
  
  // Log if root is found or not
  console.log('Root element found:', rootElement !== null);
  
  if (!rootElement) {
    console.error('Root element not found, creating one');
    const newRoot = document.createElement('div');
    newRoot.id = 'root';
    document.body.appendChild(newRoot);
    
    // Try again with the newly created root
    setTimeout(renderApp, 100);
    return;
  }
  
  try {
    console.log('Attempting to render with modern React 18 API');
    
    // Use the modern createRoot API for React 18
    const root = ReactDOM.createRoot(rootElement);
    root.render(
      <React.StrictMode>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </ThemeProvider>
      </React.StrictMode>
    );
    
    console.log('React rendering with enhanced Material UI completed');
  } catch (error) {
    console.error('Error during React rendering:', error);
    
    // Fallback to direct DOM manipulation if React fails
    rootElement.innerHTML = `
      <div style="color: red; padding: 20px; border: 2px solid red; margin: 20px;">
        <h1>React Rendering Error</h1>
        <p>There was an error rendering the React app with Material UI: ${error instanceof Error ? error.message : 'Unknown error'}</p>
        <p>Please check the console for more details.</p>
      </div>
    `;
  }
}

// Start the rendering process
console.log('Starting React rendering process with enhanced Material UI...');
renderApp(); 