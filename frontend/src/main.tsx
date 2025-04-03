import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { CssBaseline, ThemeProvider, createTheme, responsiveFontSizes, alpha } from '@mui/material';
import App from './App';
import './styles/index.css';
import './styles/global.css';
import { ProfileProvider } from './contexts/ProfileContext';

// Create a modern, elegant dark theme inspired by reading apps
const baseTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      light: '#9089fc',
      main: '#6366f1', // Soft indigo primary
      dark: '#4f46e5',
      contrastText: '#ffffff',
    },
    secondary: {
      light: '#f472b6',
      main: '#ec4899', // Soft pink secondary
      dark: '#db2777',
      contrastText: '#ffffff',
    },
    background: {
      default: '#0f172a', // Deep blue-black
      paper: '#1e293b',   // Slightly lighter blue-gray
    },
    error: {
      main: '#ef4444',
      light: '#fca5a5',
      dark: '#b91c1c',
    },
    success: {
      main: '#10b981',
      light: '#6ee7b7',
      dark: '#047857',
    },
    warning: {
      main: '#f59e0b',
      light: '#fcd34d',
      dark: '#d97706',
    },
    info: {
      main: '#3b82f6',
      light: '#93c5fd',
      dark: '#1d4ed8',
    },
    text: {
      primary: '#f8fafc',
      secondary: '#94a3b8',
    },
    divider: 'rgba(226, 232, 240, 0.08)',
    grey: {
      50: '#f8fafc',
      100: '#f1f5f9',
      200: '#e2e8f0',
      300: '#cbd5e1',
      400: '#94a3b8',
      500: '#64748b',
      600: '#475569',
      700: '#334155',
      800: '#1e293b',
      900: '#0f172a',
      A100: '#cbd5e1',
      A200: '#94a3b8',
      A400: '#475569',
      A700: '#334155',
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      '"Helvetica Neue"',
      'Arial',
      'sans-serif',
    ].join(','),
    h1: {
      fontWeight: 700,
      fontSize: '3rem',
      lineHeight: 1.2,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontWeight: 700,
      fontSize: '2.5rem',
      lineHeight: 1.2,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontWeight: 600,
      fontSize: '2rem',
      lineHeight: 1.2,
      letterSpacing: '-0.005em',
    },
    h4: {
      fontWeight: 600,
      fontSize: '1.5rem',
      lineHeight: 1.2,
      letterSpacing: '-0.005em',
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
      letterSpacing: '0em',
    },
    subtitle1: {
      fontWeight: 500,
      fontSize: '1rem',
      lineHeight: 1.5,
      letterSpacing: '0em',
    },
    subtitle2: {
      fontWeight: 500,
      fontSize: '0.875rem',
      lineHeight: 1.5,
      letterSpacing: '0em',
    },
    body1: {
      fontSize: '1rem',
      lineHeight: 1.6,
      letterSpacing: '0em',
    },
    body2: {
      fontSize: '0.875rem',
      lineHeight: 1.6,
      letterSpacing: '0em',
    },
    button: {
      fontWeight: 600,
      fontSize: '0.875rem',
      lineHeight: 1.75,
      letterSpacing: '0.01em',
      textTransform: 'none',
    },
    caption: {
      fontSize: '0.75rem',
      lineHeight: 1.66,
      letterSpacing: '0.01em',
    },
    overline: {
      fontSize: '0.75rem',
      fontWeight: 500,
      lineHeight: 1.66,
      letterSpacing: '0.06em',
      textTransform: 'uppercase',
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          backgroundImage: 'radial-gradient(at 20% 25%, hsla(240, 40%, 5%, 0.8) 0px, transparent 50%), radial-gradient(at 80% 80%, hsla(240, 60%, 5%, 0.8) 0px, transparent 50%)',
          backgroundAttachment: 'fixed',
          backgroundSize: 'cover',
          scrollBehavior: 'smooth',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          padding: '8px 20px',
          transition: 'all 0.2s ease-in-out',
          boxShadow: 'none',
          position: 'relative',
          overflow: 'hidden',
          '&:hover': {
            transform: 'translateY(-2px)',
            boxShadow: '0 5px 15px rgba(99, 102, 241, 0.15)',
          },
        },
        contained: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        },
        outlined: {
          borderWidth: 1,
          '&:hover': {
            borderWidth: 1,
            boxShadow: '0 0 10px rgba(99, 102, 241, 0.2)',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 4px 15px rgba(0, 0, 0, 0.15)',
          transition: 'all 0.3s ease',
          backdropFilter: 'blur(10px)',
          '&:hover': {
            transform: 'translateY(-3px)',
            boxShadow: '0 8px 25px rgba(0, 0, 0, 0.2)',
          },
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
        elevation1: {
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)',
        },
        elevation2: {
          boxShadow: '0 3px 6px rgba(0, 0, 0, 0.15), 0 2px 4px rgba(0, 0, 0, 0.12)',
        },
        elevation3: {
          boxShadow: '0 10px 20px rgba(0, 0, 0, 0.15), 0 3px 6px rgba(0, 0, 0, 0.1)',
        },
        elevation4: {
          boxShadow: '0 15px 25px rgba(0, 0, 0, 0.15), 0 5px 10px rgba(0, 0, 0, 0.05)',
        },
        elevation8: {
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.2)',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid rgba(226, 232, 240, 0.08)',
          padding: '16px',
        },
        head: {
          fontWeight: 600,
          color: '#94a3b8',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          fontWeight: 500,
        },
        filled: {
          backgroundColor: 'rgba(99, 102, 241, 0.15)',
        },
        outlined: {
          borderColor: 'rgba(226, 232, 240, 0.2)',
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: 16,
          boxShadow: '0 25px 50px rgba(0, 0, 0, 0.25)',
          backgroundImage: 'linear-gradient(145deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.95))',
          backdropFilter: 'blur(20px)',
        },
      },
    },
    MuiInputBase: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          transition: 'all 0.2s ease',
          '&.Mui-focused': {
            boxShadow: '0 0 0 2px rgba(99, 102, 241, 0.2)',
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          fontWeight: 500,
          transition: 'all 0.2s ease',
          '&.Mui-selected': {
            fontWeight: 600,
          },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          borderRadius: 10,
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        },
      },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
        },
      },
    },
    MuiListItem: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          transition: 'background-color 0.2s ease',
        },
      },
    },
  },
});

// Apply responsive font sizes and export the theme
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
            <ProfileProvider>
              <App />
            </ProfileProvider>
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