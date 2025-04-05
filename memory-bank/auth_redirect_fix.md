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

3. After fixing the redirect URL, being stuck on the auth callback page:
   ```
   https://vein-diagram-m2qjunh4t-aman-ankurs-projects.vercel.app/auth/callback#access_token=eyJhbGci...
   ```

## Root Cause

1. Supabase authentication was configured to redirect back to the local development URL (`http://localhost:3000`) rather than the production Vercel domain.

2. The application code was using `window.location.origin` for redirect URLs, which doesn't account for different environments (development vs. production).

3. The `AuthCallbackPage` component wasn't properly handling the authentication flow or processing the hash fragment correctly.

## Solution

### 1. Update Supabase Project Settings

1. Log in to the Supabase dashboard (https://app.supabase.com)
2. Navigate to your project > Authentication > URL Configuration
3. Add the following URLs to the "Redirect URLs" list:
   - `https://vein-diagram.vercel.app/auth/callback`
   - `https://vein-diagram-m2qjunh4t-aman-ankurs-projects.vercel.app/auth/callback`
4. Save changes

### 2. Update Authentication Redirect URLs

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

### 3. Fix the Auth Callback Handler

Update `frontend/src/pages/AuthCallbackPage.tsx` to properly handle the Supabase authentication callback:

```typescript
const handleAuthCallback = async () => {
  try {
    console.log("Auth callback page loaded");
    
    // Extract the hash fragment from the URL (used by Supabase auth)
    const hashFragment = window.location.hash;
    console.log("Hash fragment present:", !!hashFragment);
    
    if (!hashFragment) {
      throw new Error('No auth hash fragment found in URL');
    }

    // The correct way to handle the OAuth callback with Supabase
    // is to call getSession(), which will parse the hash and set up the session
    console.log("Calling supabase.auth.getSession()");
    const { data, error: sessionError } = await supabase.auth.getSession();
    
    if (sessionError) {
      console.error("Session error:", sessionError);
      throw sessionError;
    }

    console.log("Session retrieved successfully:", !!data.session);
    
    if (!data.session) {
      throw new Error('No session data returned from Supabase');
    }

    console.log("Authentication successful, redirecting to dashboard");
    // Redirect to dashboard upon successful authentication
    navigate('/dashboard', { replace: true });
  } catch (err: any) {
    console.error('Auth callback error:', err);
    setError(err.message || 'Authentication failed');
    setProcessing(false);
    
    // Redirect to login after a short delay
    setTimeout(() => {
      navigate('/login', { replace: true });
    }, 5000);
  }
};
```

Key improvements include:
- Adding detailed logging for better debugging
- Properly handling the session data returned from Supabase
- Using `{ replace: true }` with navigation to prevent back-button issues
- Increasing the error timeout to give users time to see the error message
- Checking explicitly for session data existence

### 4. Create Environment-Specific Configuration

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

### 5. Configure Vercel Environment Variables

Add the following environment variables in the Vercel project settings:

1. `VITE_API_BASE_URL` = `https://vein-diagram-api.onrender.com`
2. `VITE_FRONTEND_URL` = `https://vein-diagram.vercel.app`
3. `VITE_SUPABASE_URL` = `https://qbhopetkwddrqqlsucqi.supabase.co`
4. `VITE_SUPABASE_ANON_KEY` = `your-anon-key`

### 6. Re-deploy the Application

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
4. **Logging**: Add detailed logging around authentication flows to help diagnose issues.
5. **Auth Callback Handling**: Ensure callback pages properly process hash fragments and session data. 