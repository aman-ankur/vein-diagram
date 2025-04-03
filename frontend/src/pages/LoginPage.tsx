import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import LoginForm from '../components/auth/LoginForm';

// Create a theme specifically for the login page
const loginTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#0ea5e9', // Tailwind sky-500
    },
    background: {
      default: '#0f172a', // Tailwind slate-900
      paper: '#1e293b',  // Tailwind slate-800
    },
  },
  typography: {
    fontFamily: [
      'Inter',
      '-apple-system',
      'BlinkMacSystemFont',
      '"Segoe UI"',
      'Roboto',
      'sans-serif'
    ].join(','),
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          margin: 0,
          padding: 0,
        },
      },
    },
  },
});

const LoginPage: React.FC = () => {
  const { user, loading } = useAuth();
  
  // If user is already authenticated, redirect to dashboard
  if (user && !loading) {
    return <Navigate to="/dashboard" replace />;
  }
  
  // Show loading state while auth state is initializing
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh',
        background: 'linear-gradient(to bottom, #0A1525, #132238)',
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            borderRadius: '50%', 
            border: '2px solid transparent',
            borderTopColor: '#0ea5e9',
            borderBottomColor: '#0ea5e9',
            animation: 'spin 1s linear infinite',
          }} />
          <p style={{ color: '#94a3b8', marginTop: '16px', fontSize: '14px', fontWeight: 500 }}>
            Loading your account...
          </p>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  // Render the login page outside of the app's container layout
  return (
    <ThemeProvider theme={loginTheme}>
      <div style={{ 
        position: 'fixed', 
        top: 0, 
        left: 0, 
        right: 0, 
        bottom: 0, 
        zIndex: 9999,
        background: 'linear-gradient(to bottom, #0A1525, #132238)',
      }}>
        <LoginForm />
      </div>
    </ThemeProvider>
  );
};

export default LoginPage; 