/**
 * Keep Alive Service
 * 
 * This service periodically pings the backend API to prevent Render free tier
 * from spinning down due to inactivity.
 */

import axios from 'axios';
import { supabase } from './supabaseClient'; // Assuming supabase client is configured for auth

const PING_INTERVAL = 5 * 60 * 1000; // 5 minutes
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const HEALTH_CHECK_ENDPOINT = `${API_BASE_URL}/health`;

let intervalId: number | null = null;

/**
 * Starts a service that periodically pings the backend API health endpoint
 * to keep the server active on Render free tier.
 */
export const startKeepAliveService = () => {
  if (intervalId !== null) {
    // console.log('Keep-alive service already running');
    return; // Already running
  }

  // console.log('Starting keep-alive service for backend');
  
  const pingBackend = async () => {
    try {
      const token = (await supabase.auth.getSession())?.data?.session?.access_token;
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      // Use a timeout for the request
      const response = await axios.get(HEALTH_CHECK_ENDPOINT, {
         headers,
         timeout: 10000 // 10 second timeout
       });

      if (response.status === 200 && response.data.status === 'ok') {
        // console.log('Backend ping successful', new Date().toISOString());
        // No action needed on success
      } else {
        // console.warn('Backend ping returned non-ok status:', response.status, response.data);
        // Optionally: Implement logic to notify the user or attempt recovery
      }
    } catch (error) {
      // console.warn('Backend ping failed:', error);
      // Optionally: Implement logic to notify the user or attempt recovery
      // Example: Check if it's a network error vs. timeout vs. server error
      if (axios.isAxiosError(error)) {
        // ... existing code ...
      }
    }
  };

  // Initial ping immediately
  pingBackend();

  // Then ping periodically
  intervalId = window.setInterval(pingBackend, PING_INTERVAL);
};

export const stopKeepAliveService = () => {
  if (intervalId !== null) {
    // console.log('Stopping keep-alive service');
    window.clearInterval(intervalId);
    intervalId = null;
  }
};

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