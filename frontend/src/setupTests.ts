// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';
import { TextEncoder, TextDecoder } from 'util';

global.TextEncoder = TextEncoder;
// Use 'as any' to bypass type mismatch in test setup
global.TextDecoder = TextDecoder as any;

// Mock Vite's import.meta.env
const mockEnv = {
  VITE_SUPABASE_URL: 'http://localhost:54321',
  VITE_SUPABASE_ANON_KEY: 'test-anon-key',
  VITE_API_URL: 'http://localhost:8000',
  MODE: 'test',
  DEV: true,
  PROD: false,
  SSR: false
};

// Mock import.meta
Object.defineProperty(global, 'import', {
  value: { meta: { env: mockEnv } },
  writable: true,
  configurable: true
});

// Mock the Supabase client
jest.mock('./services/supabaseClient', () => ({
  supabase: {
    auth: {
      getSession: jest.fn().mockResolvedValue({ data: { session: null }, error: null }),
      onAuthStateChange: jest.fn().mockImplementation((callback) => {
        // Store the callback for test usage
        (global as any).authStateCallback = callback;
        return {
          data: {
            subscription: {
              unsubscribe: jest.fn()
            }
          }
        };
      }),
      signInWithPassword: jest.fn().mockResolvedValue({ data: { session: null }, error: null }),
      signOut: jest.fn().mockResolvedValue({ error: null })
    }
  }
}));

// Mock react-router-dom
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useLocation: () => ({
    pathname: '/',
    search: '',
    hash: '',
    state: null
  })
}));
