# Vercel Deployment Summary

## Overview

This document outlines the process of deploying the Vein Diagram frontend to Vercel and connecting it to the backend API deployed on Render.

## Deployment Process

### 1. Frontend Deployment to Vercel

1. Connected the GitHub repository to Vercel
2. Selected the frontend directory as the source directory
3. Used Vercel's default build settings for React/Vite applications:
   - Build command: `npm run build`
   - Output directory: `dist`
4. Configured environment variables in Vercel project settings:
   - `VITE_API_BASE_URL`: Set to the Render backend URL (https://vein-diagram-api.onrender.com)

### 2. Deployment Issues and Fixes

#### TypeScript Errors (First Round)

```
src/pages/VisualizationPage.tsx(735,32): error TS6133: 'event' is declared but its value is never read.
```

**Fix:** Modified the `handleCloseSnackbar` function to use an underscore prefix for the unused parameter:

```typescript
// Before
const handleCloseSnackbar = (event?: React.SyntheticEvent | Event, reason?: string) => {
  // function body
};

// After
const handleCloseSnackbar = (_event?: React.SyntheticEvent | Event, reason?: string) => {
  // function body
};
```

#### TypeScript Errors (Second Round)

After implementing the keep-alive service, we encountered additional TypeScript errors:

```
src/App.tsx(224,10): error TS6133: 'apiAvailable' is declared but its value is never read.
src/services/keepAliveService.ts(37,11): error TS6133: 'response' is declared but its value is never read.
```

**Fix:** 
1. For `App.tsx`, we kept only the setter function:
```typescript
// Before
const [apiAvailable, setApiAvailable] = useState<boolean | null>(null);

// After
const [, setApiAvailable] = useState<boolean | null>(null);
```

2. For `keepAliveService.ts`, we removed the unused response variable:
```typescript
// Before
const response = await fetch(`${API_BASE_URL}/health`, {
  // options
});

// After
await fetch(`${API_BASE_URL}/health`, {
  // options
});
```

#### CORS Configuration Issue

When accessing the deployed frontend, received CORS errors when trying to connect to the backend:

```
Access to XMLHttpRequest at 'https://vein-diagram-api.onrender.com/api/biomarkers?limit=1' 
from origin 'https://vein-diagram-m2qjunh4t-aman-ankurs-projects.vercel.app' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**Fix:** Updated the CORS configuration in the backend's `main.py` file to include the Vercel domains:

```python
origins = [
    # Existing origins...
    "https://vein-diagram-m2qjunh4t-aman-ankurs-projects.vercel.app", # Vercel preview deployment
    "https://vein-diagram.vercel.app", # Vercel production domain
    # ...
]
```

#### Favicon Implementation

Added a custom favicon to make the app more professional in browser tabs:

1. Created a favicon directory in the public folder
2. Added the Vein Diagram logo as favicon.jpeg
3. Updated index.html to reference the custom favicon:

```html
<link rel="icon" type="image/jpeg" href="/favicon/favicon.jpeg" />
```

## SPA Routing Configuration

### Challenge
Single Page Applications (SPAs) with client-side routing face a common issue on static hosting platforms: when a user directly accesses a route (e.g., `/visualization`) or refreshes a page, the server looks for a file at that path and returns a 404 error since the file doesn't exist.

### Solution
We've implemented a comprehensive solution that works across all static hosting providers:

1. **Custom 404.html Page**:
   - Captures the requested path in `sessionStorage`
   - Redirects to the root where `index.html` exists
   - After app initialization, React Router navigates to the intended path

2. **Multiple Fallback Methods**:
   - `vercel.json` with rewrites configuration
   - `_redirects` file for Netlify-compatible hosting
   - Custom Vite plugin to ensure redirect rules are included in every build

3. **SPA-Aware Build**:
   - Updated Vite configuration to add SPA compatibility
   - Added `historyApiFallback` for local development consistency

### Implementation Details
```javascript
// 404.html - Client-side redirect
sessionStorage.setItem('redirectPath', window.location.pathname + window.location.search);
window.location.replace('/');

// App.tsx - Handle redirect after React Router initializes
useEffect(() => {
  const redirectPath = sessionStorage.getItem('redirectPath');
  if (redirectPath) {
    sessionStorage.removeItem('redirectPath');
    navigate(redirectPath);
  }
}, [navigate]);
```

This approach ensures seamless navigation regardless of how users access the application.

## Integration Architecture

```
┌─────────────────┐          ┌─────────────────┐
│                 │          │                 │
│  Vein Diagram   │   HTTP   │  Vein Diagram   │
│    Frontend     │ ───────› │     Backend     │
│   (Vercel)      │          │   (Render)      │
│                 │          │                 │
└─────────────────┘          └─────────────────┘
```

### Frontend (Vercel)
- Hosted on Vercel's global CDN
- Configured with environment variables to connect to the backend
- Built using React, TypeScript, and Vite
- Includes keep-alive service to ping backend and prevent Render instance from spinning down

### Backend (Render)
- Deployed using Docker on Render
- FastAPI application with PostgreSQL database
- Properly configured CORS to accept requests from the Vercel domain
- Free tier limits: Spins down after inactivity (addressed with keep-alive service)

## Testing the Deployment

1. Access the Vercel-deployed frontend
2. Verify that API requests to the backend are successful
3. Test critical functionality:
   - User authentication
   - Biomarker data retrieval
   - PDF processing

## Future Considerations

1. **Custom Domain**: When moving to a custom domain, update CORS settings in the backend
2. **Scaling**: Monitor performance and upgrade plans as needed
3. **CI/CD**: Implement automated testing before deployment to catch issues
4. **Environment Separation**: Create separate development, staging, and production environments

## References

- [Vercel Documentation](https://vercel.com/docs)
- [FastAPI CORS Guide](https://fastapi.tiangolo.com/tutorial/cors/)
- [Render Deployment Guide](https://render.com/docs) 