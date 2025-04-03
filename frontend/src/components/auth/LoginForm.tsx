import React, { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, ArrowLeft, CheckCircle } from 'lucide-react';
import GoogleAuthButton from './GoogleAuthButton';

// Import an image for the left panel
// (This should be replaced with an actual image in your assets folder)
const medicalImageUrl = 'https://images.unsplash.com/photo-1581093196277-9f608bb3d4b7?ixlib=rb-4.0.3&auto=format&fit=crop&w=1000&q=80';

const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get the redirect path from location state, or default to dashboard
  const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      setErrorMessage('Please enter both email and password');
      return;
    }
    
    try {
      setIsLoading(true);
      setErrorMessage('');
      
      const { error } = await signIn(email, password);
      
      if (error) {
        throw error;
      }
      
      // Redirect to the page they were trying to access, or default to dashboard
      navigate(from, { replace: true });
    } catch (error: any) {
      console.error('Login error:', error);
      setErrorMessage(error.message || 'Failed to sign in');
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
              Welcome back to Vein Diagram. Sign in to view your latest health insights
              and biomarker visualizations.
            </p>
            <div className="space-y-3">
              <div className="flex items-center text-[#E0E7FF]">
                <CheckCircle className="h-5 w-5 mr-2 text-[#4A7AFF]" />
                <span>View your personalized health dashboard</span>
              </div>
              <div className="flex items-center text-[#E0E7FF]">
                <CheckCircle className="h-5 w-5 mr-2 text-[#4A7AFF]" />
                <span>Track biomarker changes over time</span>
              </div>
              <div className="flex items-center text-[#E0E7FF]">
                <CheckCircle className="h-5 w-5 mr-2 text-[#4A7AFF]" />
                <span>Access your securely stored test results</span>
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
            <h1 className="text-3xl font-bold text-white">Welcome back</h1>
            <p className="text-[#7A8CA6] mt-2">Sign in to your account to continue</p>
          </div>
          
          {errorMessage && (
            <div className="p-4 mb-6 text-sm text-red-400 bg-red-900/20 rounded-lg border border-red-800" role="alert">
              {errorMessage}
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
                <div className="flex items-center justify-between">
                  <label htmlFor="password" className="block text-sm font-medium text-[#7A8CA6] mb-1">
                    Password
                  </label>
                  <Link to="/reset-password" className="text-sm font-medium text-[#4A7AFF] hover:text-[#6991FF]">
                    Forgot password?
                  </Link>
                </div>
                <div className="relative">
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? "text" : "password"}
                    autoComplete="current-password"
                    required
                    className="appearance-none block w-full px-4 py-3 bg-[#1A2A44] border border-[#2A3A54] 
                             rounded-lg text-white placeholder-[#506181] 
                             focus:outline-none focus:ring-2 focus:ring-[#4A7AFF] focus:border-transparent
                             transition-all duration-200"
                    placeholder="Enter your password"
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
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg text-white bg-[#1C3E72] hover:bg-[#2A4F87] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4A7AFF] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? 'Signing in...' : 'Sign in'}
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
              <GoogleAuthButton buttonText="Sign in with Google" className="bg-[#1A2A44] hover:bg-[#243552] text-white border-[#2A3A54]" />
            </div>
          </div>
          
          <div className="text-center mt-8">
            <p className="text-sm text-[#7A8CA6]">
              Don't have an account?{' '}
              <Link to="/signup" className="font-medium text-[#4A7AFF] hover:text-[#6991FF]">
                Sign up
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

export default LoginForm; 