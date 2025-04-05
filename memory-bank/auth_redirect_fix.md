# Fixing Authentication Redirects for Vercel Deployment

## Issue

When attempting to sign in with Google authentication on the Vercel-deployed frontend, users encountered the following issues:

1. Content Security Policy (CSP) errors in the console:
   ```
   Refused to execute inline script because it violates the following Content Security Policy directive: "script-src 'report-sample' 'nonce-BTrlV_eaBQgo9Xl8V9TLZQ' 'unsafe-inline' 'unsafe-eval'".
   ```

2. Redirect to localhost instead of the Vercel domain:
   ```
   http://localhost:3000/#access_token=eyJhbGci...
   ```

## Root Cause

1. Supabase authentication was configured to redirect back to the local development URL (`http://localhost:3000`) rather than the production Vercel domain.

2. The application code was using `window.location.origin` for redirect URLs, which doesn't account for different environments (development vs. production).

## Solution

### 1. Update Supabase Project Settings

1. Log in to the Supabase dashboard (https://app.supabase.com)
2. Navigate to your project > Authentication > URL Configuration
3. Add the following URLs to the "Redirect URLs" list:
   - `https://vein-diagram.vercel.app/auth/callback`
   - `https://vein-diagram-m2qjunh4t-aman-ankurs-projects.vercel.app/auth/callback`
4. Save changes

### 2. Update Application Code

Modify `frontend/src/contexts/AuthContext.tsx` to use an environment variable for the redirect URL:

```typescript
// Sign in with Google OAuth
const signInWithGoogle = async () => {
  setError(null);
  // Use environment variable for redirect URL instead of window.location.origin
  const redirectUrl = import.meta.env.VITE_FRONTEND_URL || window.location.origin;
  console.log(`Auth redirect URL: ${redirectUrl}/auth/callback`);
  
  return await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${redirectUrl}/auth/callback`,
    },
  });
};

// Reset password
const resetPassword = async (email: string) => {
  setError(null);
  // Use environment variable for redirect URL instead of window.location.origin
  const redirectUrl = import.meta.env.VITE_FRONTEND_URL || window.location.origin;
  
  return await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${redirectUrl}/reset-password`,
  });
};
```

### 3. Create Environment-Specific Configuration

Create a `.env.production` file with the proper production values:

```
# API Configuration
VITE_API_BASE_URL=https://vein-diagram-api.onrender.com

# Frontend URL for Auth Redirects
VITE_FRONTEND_URL=https://vein-diagram.vercel.app

# Supabase Configuration
VITE_SUPABASE_URL=https://qbhopetkwddrqqlsucqi.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

### 4. Configure Vercel Environment Variables

Add the following environment variables in the Vercel project settings:

1. `VITE_API_BASE_URL` = `https://vein-diagram-api.onrender.com`
2. `VITE_FRONTEND_URL` = `https://vein-diagram.vercel.app`
3. `VITE_SUPABASE_URL` = `https://qbhopetkwddrqqlsucqi.supabase.co`
4. `VITE_SUPABASE_ANON_KEY` = `your-anon-key`

### 5. Re-deploy the Application

Deploy the updated code to Vercel.

## Verification

After implementing these changes:

1. Navigate to the Vercel-deployed application
2. Attempt to sign in with Google
3. Verify that you're redirected back to the Vercel domain with a valid session
4. Check that you can access authenticated routes

## Lessons Learned

1. **Environment-Specific Configuration**: Always use environment variables for URLs and configuration that differs between environments.
2. **Authentication Redirect Testing**: Test authentication flows in each environment before deployment.
3. **Supabase Configuration**: Update Supabase URL configuration when deploying to new domains.
4. **Logging**: Add logging around authentication flows to help diagnose issues. 