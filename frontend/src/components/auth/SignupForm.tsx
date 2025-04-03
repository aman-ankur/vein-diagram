import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff, ArrowLeft, CheckCircle } from 'lucide-react';
import GoogleAuthButton from './GoogleAuthButton';

// Import an image for the left panel
// (This should be replaced with an actual image in your assets folder)
const medicalImageUrl = 'https://images.unsplash.com/photo-1576091160550-2173dba999ef?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80';

const SignupForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [successMessage, setSuccessMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [agreeToTerms, setAgreeToTerms] = useState(false);
  
  const { signUp } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Form validation
    if (!email || !password || !confirmPassword) {
      setErrorMessage('Please fill out all fields');
      return;
    }
    
    if (password !== confirmPassword) {
      setErrorMessage('Passwords do not match');
      return;
    }
    
    if (password.length < 6) {
      setErrorMessage('Password must be at least 6 characters');
      return;
    }
    
    if (!agreeToTerms) {
      setErrorMessage('You must agree to the terms and conditions');
      return;
    }
    
    try {
      setIsLoading(true);
      setErrorMessage('');
      setSuccessMessage('');
      
      const { error, data } = await signUp(email, password);
      
      if (error) {
        throw error;
      }
      
      // Check if email confirmation is required
      if (data?.user && data.user.identities?.length === 0) {
        setSuccessMessage('Registration successful! Please check your email for a confirmation link.');
      } else {
        setSuccessMessage('Registration successful! You can now log in.');
        
        // Redirect to login page after a short delay
        setTimeout(() => {
          navigate('/login');
        }, 2000);
      }
    } catch (error: any) {
      console.error('Signup error:', error);
      setErrorMessage(error.message || 'Failed to sign up');
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
            <h2 className="text-2xl font-light mb-6">Advanced Vascular Diagnostics</h2>
            <p className="text-[#E0E7FF] opacity-90 mb-8 max-w-md">
              Track, visualize and understand your blood test results with our revolutionary platform.
              Take control of your health journey with data-driven insights.
            </p>
            <div className="space-y-3">
              <div className="flex items-center text-[#E0E7FF]">
                <CheckCircle className="h-5 w-5 mr-2 text-[#4A7AFF]" />
                <span>Secure, private management of your health data</span>
              </div>
              <div className="flex items-center text-[#E0E7FF]">
                <CheckCircle className="h-5 w-5 mr-2 text-[#4A7AFF]" />
                <span>Advanced visualization of biomarker trends</span>
              </div>
              <div className="flex items-center text-[#E0E7FF]">
                <CheckCircle className="h-5 w-5 mr-2 text-[#4A7AFF]" />
                <span>AI-powered insights for health optimization</span>
              </div>
            </div>
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
            <h1 className="text-3xl font-bold text-white">Create an account</h1>
            <p className="text-[#7A8CA6] mt-2">Join thousands of medical professionals and patients</p>
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
            <div className="space-y-4">
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
                <label htmlFor="password" className="block text-sm font-medium text-[#7A8CA6] mb-1">
                  Password
                </label>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="new-password"
                    required
                    className="appearance-none block w-full px-4 py-3 bg-[#1A2A44] border border-[#2A3A54] 
                             rounded-lg text-white placeholder-[#506181] 
                             focus:outline-none focus:ring-2 focus:ring-[#4A7AFF] focus:border-transparent
                             transition-all duration-200"
                    placeholder="Create a strong password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button 
                    type="button" 
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#7A8CA6] hover:text-white transition-colors"
                  >
                    {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
                <p className="mt-1 text-xs text-[#7A8CA6]">Must be at least 6 characters</p>
              </div>
              
              <div>
                <label htmlFor="confirm-password" className="block text-sm font-medium text-[#7A8CA6] mb-1">
                  Confirm Password
                </label>
                <div className="relative">
                  <input
                    id="confirm-password"
                    name="confirm-password"
                    type={showConfirmPassword ? "text" : "password"}
                    autoComplete="new-password"
                    required
                    className="appearance-none block w-full px-4 py-3 bg-[#1A2A44] border border-[#2A3A54] 
                             rounded-lg text-white placeholder-[#506181] 
                             focus:outline-none focus:ring-2 focus:ring-[#4A7AFF] focus:border-transparent
                             transition-all duration-200"
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                  />
                  <button 
                    type="button" 
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center text-[#7A8CA6] hover:text-white transition-colors"
                  >
                    {showConfirmPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id="terms"
                  name="terms"
                  type="checkbox"
                  checked={agreeToTerms}
                  onChange={(e) => setAgreeToTerms(e.target.checked)}
                  className="h-4 w-4 rounded border-[#2A3A54] bg-[#1A2A44] text-[#4A7AFF] focus:ring-[#4A7AFF] focus:ring-offset-[#0F1A2E]"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor="terms" className="text-[#7A8CA6]">
                  I agree to the <a href="#" className="text-[#4A7AFF] hover:text-[#6991FF]">Terms of Service</a> and <a href="#" className="text-[#4A7AFF] hover:text-[#6991FF]">Privacy Policy</a>
                </label>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-[#1C3E72] hover:bg-[#2A4F87] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4A7AFF] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Creating account...' : 'Create account'}
              </button>
            </div>
          </form>
          
          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-[#2A3A54]"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-[#0F1A2E] text-[#7A8CA6]">Or continue with</span>
              </div>
            </div>

            <div className="mt-6">
              <GoogleAuthButton buttonText="Sign up with Google" className="bg-[#1A2A44] hover:bg-[#243552] text-white border-[#2A3A54]" />
            </div>
          </div>
          
          <div className="text-center mt-8">
            <p className="text-sm text-[#7A8CA6]">
              Already have an account?{' '}
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

export default SignupForm; 