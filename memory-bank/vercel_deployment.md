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

#### TypeScript Error

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

### Backend (Render)
- Deployed using Docker on Render
- FastAPI application with PostgreSQL database
- Properly configured CORS to accept requests from the Vercel domain

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