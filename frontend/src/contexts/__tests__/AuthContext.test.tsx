// React import removed - unused
import { render, screen, act, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../AuthContext';
import { supabase } from '../../services/supabaseClient';

// Mock environment variables
const mockEnv = {
  API_BASE_URL: 'http://localhost:8000',
  DEV: true,
  PROD: false,
  MODE: 'development'
};

// Test component that uses the auth context
const TestComponent = () => {
  const { loading, user, error } = useAuth(); // Changed isLoading to loading

  if (loading) return <div>Loading...</div>; // Changed isLoading to loading
  if (error) return <div>Error: {error}</div>;
  if (user) return <div>User: {user.email}</div>;
  return <div>Not authenticated</div>;
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock import.meta.env for each test - Using 'any' to bypass stricter type checks in test environment
    // A more robust solution might involve Jest module mocking if this causes issues.
    (global as any).import = {
      meta: {
        env: mockEnv
      }
    };
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('should show loading state initially', () => {
    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('should initialize session on mount', async () => {
    const mockUser = { id: '123', email: 'test@example.com' };
    const mockSession = { user: mockUser };
    
    (supabase.auth.getSession as jest.Mock).mockResolvedValueOnce({
      data: { session: mockSession },
      error: null
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(`User: ${mockUser.email}`)).toBeInTheDocument();
    });
  });

  it('should handle session initialization error', async () => {
    const mockError = new Error('Failed to initialize session');
    
    (supabase.auth.getSession as jest.Mock).mockResolvedValueOnce({
      data: { session: null },
      error: mockError
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Error: Failed to initialize authentication')).toBeInTheDocument();
    });
  });

  it('should handle auth state changes', async () => {
    const mockUser = { id: '123', email: 'test@example.com' };
    const mockSession = { user: mockUser };
    
    (supabase.auth.getSession as jest.Mock).mockResolvedValueOnce({
      data: { session: null },
      error: null
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('Not authenticated')).toBeInTheDocument();
    });

    // Simulate auth state change using the stored callback
    act(() => {
      (global as any).authStateCallback('SIGNED_IN', mockSession);
    });

    await waitFor(() => {
      expect(screen.getByText(`User: ${mockUser.email}`)).toBeInTheDocument();
    });
  });

  it('should handle sign out', async () => {
    const mockUser = { id: '123', email: 'test@example.com' };
    const mockSession = { user: mockUser };
    
    (supabase.auth.getSession as jest.Mock).mockResolvedValueOnce({
      data: { session: mockSession },
      error: null
    });

    render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(`User: ${mockUser.email}`)).toBeInTheDocument();
    });

    // Simulate sign out using the stored callback
    act(() => {
      (global as any).authStateCallback('SIGNED_OUT', null);
    });

    await waitFor(() => {
      expect(screen.getByText('Not authenticated')).toBeInTheDocument();
    });
  });
});
