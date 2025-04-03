import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';

// Import an image for the left panel
// (This should be replaced with an actual image in your assets folder)
const medicalImageUrl = 'https://images.unsplash.com/photo-1530026186672-2cd00ffc50fe?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80';

const ResetPasswordForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { resetPassword } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setErrorMessage('Please enter your email address');
      return;
    }
    
    try {
      setIsLoading(true);
      setErrorMessage('');
      setSuccessMessage('');
      
      const { error } = await resetPassword(email);
      
      if (error) {
        throw error;
      }
      
      setSuccessMessage('Password reset instructions have been sent to your email address.');
    } catch (error: any) {
      console.error('Reset password error:', error);
      setErrorMessage(error.message || 'Failed to send reset password email');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-[#0F1A2E]">
      {/* Left panel with medical image */}
      <div className="hidden lg:block lg:w-1/2 relative">
        <img 
          src={medicalImageUrl} 
          alt="Medical illustration" 
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-[#1C3E72]/90 to-[#0F1A2E]/70 flex flex-col justify-center px-12">
          <div className="text-white">
            <div className="text-3xl font-bold mb-4 flex items-center">
              <span className="text-5xl font-light bg-[#1C3E72] p-2 rounded-lg mr-3">VD</span>
              Vein Diagram
            </div>
            <h2 className="text-2xl font-light mb-6">Account Recovery</h2>
            <p className="text-[#E0E7FF] opacity-90 mb-8 max-w-md">
              We'll help you reset your password and regain access to your health data.
              Enter your email address to receive recovery instructions.
            </p>
          </div>
        </div>
      </div>
      
      {/* Right panel with form */}
      <div className="w-full lg:w-1/2 flex flex-col min-h-screen">
        <div className="p-8">
          <Link to="/" className="text-[#7A8CA6] hover:text-white flex items-center mb-8 transition-colors">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to website
          </Link>
          
          <div className="mb-8 text-center lg:text-left">
            <h1 className="text-3xl font-bold text-white">Reset Your Password</h1>
            <p className="text-[#7A8CA6] mt-2">Enter your email to receive recovery instructions</p>
          </div>
          
          {errorMessage && (
            <div className="p-4 mb-6 text-sm text-red-400 bg-red-900/20 rounded-lg border border-red-800" role="alert">
              {errorMessage}
            </div>
          )}
          
          {successMessage && (
            <div className="p-4 mb-6 text-sm text-green-400 bg-green-900/20 rounded-lg border border-green-800" role="alert">
              {successMessage}
            </div>
          )}
          
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-[#7A8CA6] mb-1">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none block w-full px-4 py-3 bg-[#1A2A44] border border-[#2A3A54] 
                         rounded-lg text-white placeholder-[#506181] 
                         focus:outline-none focus:ring-2 focus:ring-[#4A7AFF] focus:border-transparent
                         transition-all duration-200"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-[#1C3E72] hover:bg-[#2A4F87] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4A7AFF] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Sending...' : 'Send Reset Link'}
              </button>
            </div>
          </form>
          
          <div className="text-center mt-8">
            <p className="text-sm text-[#7A8CA6]">
              Remember your password?{' '}
              <Link to="/login" className="font-medium text-[#4A7AFF] hover:text-[#6991FF]">
                Sign in
              </Link>
            </p>
          </div>
        </div>
        
        <div className="mt-auto p-6 text-center text-xs text-[#7A8CA6] border-t border-[#2A3A54]">
          <p>© {new Date().getFullYear()} Vein Diagram. All rights reserved.</p>
          <div className="mt-2 space-x-4">
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Support</a>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ResetPasswordForm; 