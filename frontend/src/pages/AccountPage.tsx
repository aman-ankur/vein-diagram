import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { Navigate, useNavigate } from 'react-router-dom';
import { LogOut, User, Shield, Clock, ArrowLeft } from 'lucide-react';

const AccountPage: React.FC = () => {
  const { user, loading, signOut } = useAuth();
  const [isSigningOut, setIsSigningOut] = useState(false);
  const navigate = useNavigate();
  
  // Redirect to login if not authenticated
  if (!user && !loading) {
    return <Navigate to="/login" replace />;
  }
  
  // Show loading state while auth state is initializing
  if (loading) {
    return (
      <div className="flex justify-center items-center h-screen bg-[#0F1A2E]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-[#4A7AFF]"></div>
      </div>
    );
  }

  const handleSignOut = async () => {
    try {
      setIsSigningOut(true);
      await signOut();
      navigate('/login');
    } catch (error) {
      console.error('Error signing out:', error);
      setIsSigningOut(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0F1A2E] text-white">
      <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <button 
            onClick={() => navigate('/dashboard')} 
            className="inline-flex items-center text-[#7A8CA6] hover:text-white transition-colors"
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Dashboard
          </button>
        </div>
        
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-white">Account Settings</h1>
          <p className="mt-2 text-[#7A8CA6]">Manage your account preferences and security</p>
        </div>
        
        <div className="bg-[#1A2A44] rounded-lg shadow-lg overflow-hidden border border-[#2A3A54]">
          <div className="px-6 py-5 border-b border-[#2A3A54]">
            <h2 className="text-xl font-semibold flex items-center">
              <User className="mr-2 h-5 w-5 text-[#4A7AFF]" />
              User Information
            </h2>
          </div>
          
          <div className="divide-y divide-[#2A3A54]">
            <div className="px-6 py-5 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-[#7A8CA6]">Email address</dt>
              <dd className="mt-1 text-sm sm:mt-0 sm:col-span-2">{user?.email}</dd>
            </div>
            
            <div className="px-6 py-5 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-[#7A8CA6]">User ID</dt>
              <dd className="mt-1 text-sm sm:mt-0 sm:col-span-2 text-[#7A8CA6]">{user?.id}</dd>
            </div>
            
            <div className="px-6 py-5 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-[#7A8CA6]">Authentication method</dt>
              <dd className="mt-1 text-sm sm:mt-0 sm:col-span-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-[#1C3E72] text-white">
                  {user?.app_metadata?.provider === 'google' ? 'Google' : 'Email/Password'}
                </span>
              </dd>
            </div>
            
            <div className="px-6 py-5 sm:grid sm:grid-cols-3 sm:gap-4">
              <dt className="text-sm font-medium text-[#7A8CA6]">Account created</dt>
              <dd className="mt-1 text-sm sm:mt-0 sm:col-span-2 flex items-center">
                <Clock className="mr-2 h-4 w-4 text-[#7A8CA6]" />
                {new Date(user?.created_at ?? '').toLocaleString()}
              </dd>
            </div>
          </div>
        </div>
        
        <div className="mt-8 bg-[#1A2A44] rounded-lg shadow-lg overflow-hidden border border-[#2A3A54]">
          <div className="px-6 py-5 border-b border-[#2A3A54]">
            <h2 className="text-xl font-semibold flex items-center">
              <Shield className="mr-2 h-5 w-5 text-[#4A7AFF]" />
              Security & Privacy
            </h2>
          </div>
          
          <div className="px-6 py-5">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-medium">Password</h3>
                <p className="text-xs text-[#7A8CA6] mt-1">Change your password or reset it if forgotten</p>
              </div>
              <button 
                onClick={() => navigate('/reset-password')}
                className="px-3 py-1.5 text-sm bg-[#1C3E72] hover:bg-[#2A4F87] text-white rounded-md transition-colors"
              >
                Change Password
              </button>
            </div>
          </div>
        </div>
        
        <div className="mt-8 flex justify-end">
          <button
            onClick={handleSignOut}
            disabled={isSigningOut}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50 focus:ring-offset-[#0F1A2E]"
          >
            <LogOut className="mr-2 h-4 w-4" />
            {isSigningOut ? 'Signing Out...' : 'Sign Out'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AccountPage; 