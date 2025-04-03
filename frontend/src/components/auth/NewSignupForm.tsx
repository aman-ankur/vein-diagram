import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
// Assuming you have icons available, e.g., from react-icons or similar
import { FaEye, FaEyeSlash, FaGoogle } from 'react-icons/fa'; 

const NewSignupForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signUp, signInWithGoogle } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      setLoading(false);
      return;
    }
    if (!agreedToTerms) {
      setError('You must agree to the Terms of Service and Privacy Policy');
      setLoading(false);
      return;
    }

    try {
      await signUp(email, password);
      // Consider adding a success message before redirecting
      navigate('/login'); // Redirect to login after successful signup
    } catch (err: any) {
      setError(err.message || 'Failed to create account. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  const handleGoogleSignIn = async () => {
    setError('');
    setLoading(true);
    try {
      await signInWithGoogle();
      // Google sign-in handles redirection via callback
    } catch (err: any) {
       setError(err.message || 'Failed to sign in with Google. Please try again.');
       setLoading(false);
    }
    // No finally setLoading(false) here as Google redirect might happen
  };

  return (
    // Add shadow to the form container
    <div className="w-full bg-[#0A2342]/10 p-8 rounded-lg shadow-[0_4px_8px_rgba(0,0,0,0.2)]"> 
      {/* Logo */}
      <div className="text-center mb-4">
        <span className="text-3xl font-bold text-[#2D7D90]">VD</span>
      </div>

      {/* Heading: 28px, 600 weight */}
      <h1 className="text-[28px] font-semibold text-center mb-2 text-white">
        Create an account
      </h1>
      {/* Body text: 16px, 400 weight */}
      <p className="text-base font-normal text-center text-[#E0E6ED] mb-6">
        Advanced Vascular Diagnostics starts here.
      </p>
      {/* Optional Value Prop - max 20 words */}
      {/* <p className="text-xs text-center text-[#E0E6ED]/80 mb-6">
        Track, visualize and understand your blood test results with our revolutionary platform. Take control of your health journey.
      </p> */}


      {error && (
        <div className="bg-red-500/20 text-red-300 p-3 rounded-lg mb-4 text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Email Input with Floating Label */}
        <div className="relative">
          <input
            id="email"
            name="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="peer block w-full px-3 py-3 bg-[#FFFFFF20] border border-transparent rounded-lg text-sm text-white placeholder-transparent 
                       focus:outline-none focus:ring-2 focus:ring-[#2D7D90] focus:border-transparent"
            placeholder="Email address"
          />
          <label
            htmlFor="email"
            // Label: 14px (placeholder state), 500 weight
            className="absolute left-3 -top-2.5 text-[#E0E6ED] text-xs transition-all 
                       peer-placeholder-shown:text-sm peer-placeholder-shown:font-medium peer-placeholder-shown:text-[#E0E6ED]/70 peer-placeholder-shown:top-3.5 
                       peer-focus:-top-2.5 peer-focus:text-[#E0E6ED] peer-focus:text-xs pointer-events-none"
          >
            Email address
          </label>
        </div>

        {/* Password Input with Floating Label & Toggle */}
        <div className="relative">
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
            className="peer block w-full px-3 py-3 bg-[#FFFFFF20] border border-transparent rounded-lg text-sm text-white placeholder-transparent 
                       focus:outline-none focus:ring-2 focus:ring-[#2D7D90] focus:border-transparent"
            placeholder="Password"
          />
          <label
            htmlFor="password"
            // Label: 14px (placeholder state), 500 weight
            className="absolute left-3 -top-2.5 text-[#E0E6ED] text-xs transition-all 
                       peer-placeholder-shown:text-sm peer-placeholder-shown:font-medium peer-placeholder-shown:text-[#E0E6ED]/70 peer-placeholder-shown:top-3.5 
                       peer-focus:-top-2.5 peer-focus:text-[#E0E6ED] peer-focus:text-xs pointer-events-none"
          >
            Password
          </label>
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 px-3 flex items-center text-[#E0E6ED]/70 hover:text-[#E0E6ED]"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <FaEyeSlash /> : <FaEye />}
          </button>
        </div>

        {/* Confirm Password Input with Floating Label & Toggle */}
        <div className="relative">
          <input
            id="confirmPassword"
            name="confirmPassword"
            type={showConfirmPassword ? 'text' : 'password'}
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={6}
            className="peer block w-full px-3 py-3 bg-[#FFFFFF20] border border-transparent rounded-lg text-sm text-white placeholder-transparent 
                       focus:outline-none focus:ring-2 focus:ring-[#2D7D90] focus:border-transparent"
            placeholder="Confirm Password"
          />
          <label
            htmlFor="confirmPassword"
            // Label: 14px (placeholder state), 500 weight
            className="absolute left-3 -top-2.5 text-[#E0E6ED] text-xs transition-all 
                       peer-placeholder-shown:text-sm peer-placeholder-shown:font-medium peer-placeholder-shown:text-[#E0E6ED]/70 peer-placeholder-shown:top-3.5 
                       peer-focus:-top-2.5 peer-focus:text-[#E0E6ED] peer-focus:text-xs pointer-events-none"
          >
            Confirm Password
          </label>
           <button
            type="button"
            onClick={() => setShowConfirmPassword(!showConfirmPassword)}
            className="absolute inset-y-0 right-0 px-3 flex items-center text-[#E0E6ED]/70 hover:text-[#E0E6ED]"
            aria-label={showConfirmPassword ? 'Hide confirm password' : 'Show confirm password'}
          >
            {showConfirmPassword ? <FaEyeSlash /> : <FaEye />}
          </button>
        </div>

        {/* Terms Checkbox */}
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="terms"
              name="terms"
              type="checkbox"
              checked={agreedToTerms}
              onChange={(e) => setAgreedToTerms(e.target.checked)}
              className="focus:ring-[#2D7D90] h-4 w-4 text-[#2D7D90] bg-[#FFFFFF20] border-transparent rounded"
            />
          </div>
          <div className="ml-3 text-sm">
            <label htmlFor="terms" className="font-medium text-[#E0E6ED]">
              I agree to the{' '}
              <Link to="/terms" className="text-[#2D7D90] hover:underline">
                Terms of Service
              </Link>{' '}
              and{' '}
              <Link to="/privacy" className="text-[#2D7D90] hover:underline">
                Privacy Policy
              </Link>
            </label>
          </div>
        </div>

        {/* Submit Button */}
        {/* Button text: 16px, 600 weight */}
        <button
          type="submit"
          disabled={loading}
          className="w-full flex justify-center py-3 px-4 border border-transparent rounded-lg shadow-sm text-base font-semibold text-white 
                     bg-gradient-to-r from-[#2D7D90] to-[#1A5F7A] hover:brightness-110 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#2D7D90]
                     disabled:opacity-50 disabled:cursor-not-allowed transition duration-200 ease-in-out transform hover:-translate-y-0.5"
        >
          {loading ? 'Creating Account...' : 'Create Account'}
        </button>
      </form>

      {/* Divider */}
      <div className="my-6 flex items-center justify-center">
        <span className="px-2 text-sm text-[#E0E6ED]/70">Or continue with</span>
      </div>

      {/* Social Logins */}
      <div className="space-y-4">
         <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="w-full flex items-center justify-center py-2.5 px-4 border border-[#FFFFFF20] rounded-lg shadow-sm bg-[#FFFFFF10] 
                     text-sm font-medium text-[#E0E6ED] hover:bg-[#FFFFFF20] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#2D7D90]
                     disabled:opacity-50 disabled:cursor-not-allowed transition duration-200 ease-in-out transform hover:-translate-y-0.5"
        >
          <FaGoogle className="w-5 h-5 mr-2" />
          Sign up with Google
        </button>
        {/* Add other social logins here if needed */}
      </div>

      {/* Sign In Link */}
      <p className="mt-8 text-center text-sm text-[#E0E6ED]/80">
        Already have an account?{' '}
        <Link to="/login" className="font-medium text-[#2D7D90] hover:underline">
          Sign in
        </Link>
      </p>

      {/* Footer */}
       <div className="mt-6 text-center text-xs text-[#E0E6ED]/50">
         © {new Date().getFullYear()} Vein Diagram. All rights reserved.
       </div>
    </div>
  );
};

export default NewSignupForm;
