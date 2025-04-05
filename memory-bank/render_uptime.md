# Keeping Render Instance Alive

Free tier instances on Render spin down after periods of inactivity. Here are several methods to keep your instance active:

## 1. GitHub Actions Ping Service (Recommended)

Create a GitHub workflow that periodically pings your Render API:

1. Create a file `.github/workflows/ping.yml` in your repository:

```yaml
name: Ping Render Service

on:
  schedule:
    - cron: '*/10 * * * *'  # Run every 10 minutes

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping API Health Endpoint
        run: curl -X GET https://vein-diagram-api.onrender.com/health
```

## 2. UptimeRobot (Free Alternative)

1. Create an account at [UptimeRobot](https://uptimerobot.com/)
2. Set up a new monitor to ping your `/health` endpoint every 5 minutes
3. UptimeRobot will ping your service, keeping it active and monitoring uptime

## 3. Cron Job on Another Server

If you have access to another server that's always running:

```bash
# Add to crontab
*/10 * * * * curl -s https://vein-diagram-api.onrender.com/health > /dev/null 2>&1
```

## 4. Client-Side Pinging (Fallback Option)

Add a script to your frontend that pings the backend while users have the app open:

```typescript
// In a service file
const keepAliveInterval = 5 * 60 * 1000; // 5 minutes

export function startKeepAliveService() {
  setInterval(() => {
    fetch('https://vein-diagram-api.onrender.com/health', { 
      method: 'GET',
      mode: 'no-cors' // Prevents CORS issues
    }).catch(() => {
      // Silent failure is fine here
    });
  }, keepAliveInterval);
}

// Call this from your app initialization
```

## Notes

- The `/health` endpoint should be lightweight and not count against any API limits
- Consider upgrading to a paid plan for production use
- Excessive pinging may violate Render's terms of service
- A 10-15 minute interval is usually sufficient 