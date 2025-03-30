/**
 * Application Configuration
 * 
 * This file contains global configuration settings for the application.
 * Environment variables can be used to override these settings.
 */

// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// File Upload Settings
export const MAX_FILE_SIZE = 30 * 1024 * 1024; // 30MB
export const SUPPORTED_FILE_TYPES = [
  'application/pdf'
];

// API Polling Configuration
export const STATUS_CHECK_INTERVAL = 3000; // 3 seconds
export const MAX_POLLING_RETRIES = 10;

// LocalStorage Keys
export const STORAGE_KEYS = {
  UPLOADED_FILES: 'vein-diagram:uploaded-files',
  USER_PREFERENCES: 'vein-diagram:user-preferences',
  THEME_PREFERENCE: 'vein-diagram:theme-preference',
  AUTH_TOKEN: 'vein-diagram:auth-token'
};

// Date and Time Formatting
export const DATE_FORMAT = {
  DISPLAY: 'MMM dd, yyyy',
  API: 'yyyy-MM-dd'
};

// Default Settings
export const DEFAULT_SETTINGS = {
  showTooltips: true,
  enableAnimations: true,
  notificationsEnabled: true,
  darkMode: false,
  compactView: false,
  dataDecimals: 2
};

// Dashboard Settings
export const DASHBOARD = {
  recentItemsCount: 5,
  refreshInterval: 60000, // 1 minute
  chartAnimation: true
};

// Feature Flags
export const FEATURES = {
  enableDarkMode: true,
  enableExport: true,
  enableCompare: true,
  enableSharing: false, // Not implemented yet
  enablePrinting: true,
  enableDataDownload: true
};

// Error Messages
export const ERROR_MESSAGES = {
  FILE_TOO_LARGE: `File is too large. Maximum size is ${MAX_FILE_SIZE / 1024 / 1024}MB.`,
  UNSUPPORTED_FILE_TYPE: 'Unsupported file type. Please upload a PDF file.',
  UPLOAD_FAILED: 'Failed to upload file. Please try again.',
  PROCESSING_FAILED: 'Failed to process file. Please try again.',
  API_UNAVAILABLE: 'API service is currently unavailable. Please try again later.',
  NETWORK_ERROR: 'Network error. Please check your connection and try again.'
};

export default {
  API_BASE_URL,
  MAX_FILE_SIZE,
  SUPPORTED_FILE_TYPES,
  STATUS_CHECK_INTERVAL,
  MAX_POLLING_RETRIES,
  STORAGE_KEYS,
  DATE_FORMAT,
  DEFAULT_SETTINGS,
  DASHBOARD,
  FEATURES,
  ERROR_MESSAGES
}; 