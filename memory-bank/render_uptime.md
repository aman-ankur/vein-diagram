# Keeping Render Instance Alive

Free tier instances on Render spin down after periods of inactivity. Here are several methods to keep your instance active:

## 1. GitHub Actions Ping Service (Implemented)

We've implemented a GitHub workflow that periodically pings our Render API:

Created `.github/workflows/ping.yml` in the repository:

```yaml
name: Keep Render Instance Alive

on:
  schedule:
    - cron: '*/10 * * * *'  # Run every 10 minutes
  # Also run this workflow on push to main branch to verify it works
  push:
    branches:
      - main
      - master

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping API Health Endpoint
        run: |
          curl -X GET https://vein-diagram-api.onrender.com/health || true
          echo "Ping completed at $(date)"
      
      - name: Verify API Status
        run: |
          RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" https://vein-diagram-api.onrender.com/health)
          if [[ "$RESPONSE" -ge 200 && "$RESPONSE" -lt 300 ]]; then
            echo "✅ API is responding with status code $RESPONSE"
          else
            echo "⚠️ API returned status code $RESPONSE"
            # Don't fail the workflow, as this could be during cold start
          fi
```

This action will:
- Run every 10 minutes
- Also run on pushes to main/master branches for verification
- Ping the health endpoint and capture the response code
- Log the status without failing if the server is in cold start mode

## 2. Client-Side Pinging (Implemented)

We've also implemented a client-side service that pings the backend while users have the app open:

Created `frontend/src/services/keepAliveService.ts`:

```typescript
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
```

Added to `App.tsx` to initialize the service:

```typescript
// Initialize keep-alive service
useEffect(() => {
  // Start the keep-alive service when the app loads
  const stopKeepAliveService = startKeepAliveService();
  
  // Clean up function to stop the interval when component unmounts
  return () => {
    stopKeepAliveService();
  };
}, []);
```

## Additional Options (Not Currently Implemented)

### 3. UptimeRobot (Free Alternative)

1. Create an account at [UptimeRobot](https://uptimerobot.com/)
2. Set up a new monitor to ping your `/health` endpoint every 5 minutes
3. UptimeRobot will ping your service, keeping it active and monitoring uptime

### 4. Cron Job on Another Server

If you have access to another server that's always running:

```bash
# Add to crontab
*/10 * * * * curl -s https://vein-diagram-api.onrender.com/health > /dev/null 2>&1
```

## Notes

- Our current solution combines GitHub Actions (server-side) and client-side pinging for maximal uptime
- The `/health` endpoint is lightweight and doesn't count against any API limits
- Consider upgrading to a paid plan for production use to avoid these workarounds
- Our combined approach should prevent most cold starts during normal usage hours 