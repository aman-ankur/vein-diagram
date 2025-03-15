/**
 * Application configuration
 */

// API base URL - defaults to local development server
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Maximum file size for uploads in bytes (30MB)
export const MAX_FILE_SIZE = 30 * 1024 * 1024;

// Supported file types
export const SUPPORTED_FILE_TYPES = ['application/pdf'];

// Polling interval for status checks in milliseconds
export const STATUS_POLLING_INTERVAL = 2000; 