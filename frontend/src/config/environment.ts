// Environment detection
export const isProduction = import.meta.env.PROD || import.meta.env.MODE === 'production';
export const isDevelopment = import.meta.env.DEV || import.meta.env.MODE === 'development';
export const isTest = import.meta.env.MODE === 'test';

// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Feature flags
export const ENABLE_DEBUG_TOOLS = isDevelopment;
export const ENABLE_PERFORMANCE_MONITORING = isProduction;

// Logging configuration
export const LOG_LEVEL = isProduction ? 'warn' : 'debug';
export const ENABLE_CONSOLE_LOGS = !isProduction;

// Auth configuration
export const AUTH_ENABLED = true;
export const AUTH_COOKIE_NAME = 'vein_diagram_auth';

// Performance thresholds (in milliseconds)
export const PERFORMANCE_THRESHOLDS = {
  API_CALL: 1000,
  RENDER: 100,
  ANIMATION: 16
}; 