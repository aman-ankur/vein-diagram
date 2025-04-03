import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import ResetPasswordForm from '../components/auth/ResetPasswordForm';

const ResetPasswordPage: React.FC = () => {
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
      <ResetPasswordForm />
    </div>
  );
};

export default ResetPasswordPage; 