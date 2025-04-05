/**
 * Keep Alive Service
 * 
 * This service periodically pings the backend API to prevent Render free tier
 * from spinning down due to inactivity.
 */

import { API_BASE_URL } from '../config/environment';

const KEEP_ALIVE_INTERVAL = 4 * 60 * 1000; // 4 minutes interval

/**
 * Starts a service that periodically pings the backend API health endpoint
 * to keep the server active on Render free tier.
 */
export function startKeepAliveService(): () => void {
  console.log('Starting keep-alive service for backend');
  
  // Perform an initial ping immediately
  pingBackend();
  
  // Set up interval for regular pings
  const intervalId = setInterval(pingBackend, KEEP_ALIVE_INTERVAL);
  
  // Return a function to stop the service if needed
  return () => {
    console.log('Stopping keep-alive service');
    clearInterval(intervalId);
  };
}

/**
 * Sends a ping request to the backend's health endpoint
 */
async function pingBackend(): Promise<void> {
  try {
    // Use void to explicitly ignore the response
    await fetch(`${API_BASE_URL}/health`, {
      method: 'GET',
      mode: 'no-cors', // Prevents CORS issues
      cache: 'no-cache',
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    });
    
    if (process.env.NODE_ENV !== 'production') {
      console.log('Backend ping completed', new Date().toISOString());
    }
    
    return Promise.resolve();
  } catch (error) {
    // Silent failure - we don't want to disrupt the application
    // if the backend is temporarily unavailable
    if (process.env.NODE_ENV !== 'production') {
      console.warn('Backend ping failed:', error);
    }
    return Promise.resolve();
  }
} 