import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../../../contexts/AuthContext';
import NewSignupForm from '../NewSignupForm';
import { supabase } from '../../../services/supabaseClient';

// Mock the supabase client
const mockSupabase = supabase as jest.Mocked<typeof supabase>;

const renderSignupForm = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <NewSignupForm />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe('NewSignupForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders signup form elements', () => {
    renderSignupForm();
    
    // Check for form elements
    expect(screen.getByLabelText(/email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^password$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: /terms/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('shows validation error for password mismatch', async () => {
    renderSignupForm();
    
    // Fill in form with mismatched passwords
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'password123' }
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'password456' }
    });
    
    // Submit form
    const createButton = screen.getByRole('button', { name: /create account/i });
    fireEvent.click(createButton);
    
    // Check for error message
    expect(await screen.findByText(/passwords do not match/i)).toBeInTheDocument();
  });

  it('shows validation error for unchecked terms', async () => {
    renderSignupForm();
    
    // Fill in form without checking terms
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'password123' }
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'password123' }
    });
    
    // Submit form
    const createButton = screen.getByRole('button', { name: /create account/i });
    fireEvent.click(createButton);
    
    // Check for error message
    expect(await screen.findByText(/you must agree to the terms/i)).toBeInTheDocument();
  });

  it('handles successful signup', async () => {
    // Mock successful signup response
    mockSupabase.auth.signUp.mockResolvedValueOnce({
      data: { user: { id: '123', email: 'test@example.com' }, session: null },
      error: null
    } as any);

    renderSignupForm();
    
    // Fill in form correctly
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'password123' }
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'password123' }
    });
    
    // Check terms checkbox
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    fireEvent.click(termsCheckbox);
    
    // Submit form
    const createButton = screen.getByRole('button', { name: /create account/i });
    fireEvent.click(createButton);
    
    // Verify Supabase was called with correct credentials
    await waitFor(() => {
      expect(mockSupabase.auth.signUp).toHaveBeenCalledWith({
        email: 'test@example.com',
        password: 'password123'
      });
    });
  });

  it('handles signup error', async () => {
    // Mock signup error response
    mockSupabase.auth.signUp.mockResolvedValueOnce({
      data: { user: null, session: null },
      error: { message: 'Email already registered' }
    } as any);

    renderSignupForm();
    
    // Fill in form
    fireEvent.change(screen.getByLabelText(/email address/i), {
      target: { value: 'test@example.com' }
    });
    fireEvent.change(screen.getByLabelText(/^password$/i), {
      target: { value: 'password123' }
    });
    fireEvent.change(screen.getByLabelText(/confirm password/i), {
      target: { value: 'password123' }
    });
    
    // Check terms checkbox
    const termsCheckbox = screen.getByRole('checkbox', { name: /terms/i });
    fireEvent.click(termsCheckbox);
    
    // Submit form
    const createButton = screen.getByRole('button', { name: /create account/i });
    fireEvent.click(createButton);
    
    // Check for error message
    expect(await screen.findByText(/email already registered/i)).toBeInTheDocument();
  });

  it('toggles password visibility', () => {
    renderSignupForm();
    
    // Check password field
    const passwordInput = screen.getByLabelText(/^password$/i);
    expect(passwordInput).toHaveAttribute('type', 'password');
    
    // Toggle password visibility
    const toggleButton = screen.getByRole('button', {
      name: '', // The button doesn't have a name, it just has an icon
    });
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'text');
    
    // Toggle back
    fireEvent.click(toggleButton);
    expect(passwordInput).toHaveAttribute('type', 'password');
  });

  it('handles Google sign in', async () => {
    // Mock Google sign in
    mockSupabase.auth.signInWithOAuth.mockResolvedValueOnce({
      data: { provider: 'google' },
      error: null
    } as any);

    renderSignupForm();
    
    // Click Google sign in button
    const googleButton = screen.getByRole('button', { name: /sign in with google/i });
    fireEvent.click(googleButton);
    
    // Verify Supabase was called
    await waitFor(() => {
      expect(mockSupabase.auth.signInWithOAuth).toHaveBeenCalledWith({
        provider: 'google'
      });
    });
  });
}); 