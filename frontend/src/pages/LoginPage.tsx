import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LoginForm from '../components/auth/LoginForm';
import AuthLayout from '../components/auth/AuthLayout';

const LoginPage: React.FC = () => {
  const { user, loading } = useAuth();
  
  // If user is already authenticated, redirect to dashboard
  if (user && !loading) {
    return <Navigate to="/dashboard" replace />;
  }
  
  // Show loading state while auth state is initializing
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-[#0F1A2E]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#4A7AFF]"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0F1A2E]">
      <LoginForm />
    </div>
  );
};

export default LoginPage; 