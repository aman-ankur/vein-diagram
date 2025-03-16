import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme, responsiveFontSizes } from '@mui/material';
import App from './App';
import './styles/global.css';

// Create a theme instance with a more professional design
const baseTheme = createTheme({
  palette: {
    primary: {
      light: '#5e72e4',
      main: '#3f51b5',
      dark: '#2c3e8f',
      contrastText: '#ffffff',
    },
    secondary: {
      light: '#12d8c0',
      main: '#00bfa5',
      dark: '#008b76',
      contrastText: '#000000',
    },
    background: {
      default: '#f8f9fa',
      paper: '#ffffff',
    },
    error: {
      main: '#f44336',
    },
    success: {
      main: '#4caf50',
    },
    warning: {
      main: '#ff9800',
    },
    info: {
      main: '#0288d1',
    },
    text: {
      primary: '#1f2937',
      secondary: '#6b7280',
    },
    grey: {
      50: '#f9fafb',
      100: '#f3f4f6',
      200: '#e5e7eb',
      300: '#d1d5db',
      400: '#9ca3af',
      500: '#6b7280',
      600: '#4b5563',
      700: '#374151',
      800: '#1f2937',
      900: '#111827',
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
    borderRadius: 8,
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          padding: '10px 24px',
          transition: 'all 0.2s ease-in-out',
          boxShadow: 'none',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 5px 15px rgba(0, 0, 0, 0.05)',
          },
        },
        contained: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
        },
        outlined: {
          borderWidth: 1.5,
          '&:hover': {
            borderWidth: 1.5,
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 20px rgba(0, 0, 0, 0.05)',
          transition: 'all 0.3s ease',
          '&:hover': {
            transform: 'translateY(-4px)',
            boxShadow: '0 12px 30px rgba(0, 0, 0, 0.08)',
          },
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 12,
        },
        elevation1: {
          boxShadow: '0 2px 12px rgba(0, 0, 0, 0.05)',
        },
        elevation2: {
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.06)',
        },
        elevation3: {
          boxShadow: '0 6px 20px rgba(0, 0, 0, 0.07)',
        },
        elevation4: {
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
            transition: 'border-color 0.2s ease',
            '&:hover fieldset': {
              borderColor: '#3f51b5',
            },
          },
        },
      },
    },
  },
});

// Make typography responsive
export const theme = responsiveFontSizes(baseTheme);

// Log to console to verify script is running
console.log('main.tsx is executing - With Enhanced Material UI Theme');

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