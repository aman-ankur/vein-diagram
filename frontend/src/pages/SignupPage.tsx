import React from 'react';
import AuthLayout from '../components/auth/AuthLayout';
import SignupForm from '../components/auth/SignupForm';
import GoogleAuthButton from '../components/auth/GoogleAuthButton';
import { useAuth } from '../contexts/AuthContext';
import { Navigate } from 'react-router-dom';

const SignupPage: React.FC = () => {
  const { user, loading } = useAuth();
  
  // If user is already authenticated, redirect to dashboard
  if (user && !loading) {
    return <Navigate to="/dashboard" replace />;
  }
  
  // Show loading state while auth state is initializing
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <AuthLayout title="Create a new account">
      <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
        <SignupForm />
        
        <div className="mt-6">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-white text-gray-500">Or continue with</span>
            </div>
          </div>

          <div className="mt-6">
            <GoogleAuthButton buttonText="Sign up with Google" />
          </div>
        </div>
      </div>
    </AuthLayout>
  );
};

export default SignupPage; 