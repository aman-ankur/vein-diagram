# Vein Diagram Authentication Implementation - Complete Reference

## Authentication Overview
Vein Diagram implements a secure authentication system using Supabase Auth, providing email/password and social authentication options with a medical-themed UI aligned with the application's purpose. The system includes complete user flows for signup, login, password reset, and account management.

## Frontend Components

### Auth Context
- **Location**: `src/contexts/AuthContext.tsx`
- **Purpose**: Central provider for authentication state and methods
- **Key Functions**:
  - `signUp(email, password)`: Email registration
  - `signIn(email, password)`: Email login
  - `signInWithGoogle()`: Google OAuth flow
  - `resetPassword(email)`: Password recovery
  - `signOut()`: User logout
  - `updateUserProfile(data)`: Profile updates
- **State Management**: 
  - User object
  - Loading states
  - Authentication status

### Page Components
- **NewSignupPage.tsx**: Split-panel container with styled left side and form (using Tailwind CSS as per latest implementation).
- **LoginPage.tsx**: Login form container with similar split-panel design.
- **ResetPasswordPage.tsx**: Password recovery form container.
- **AccountPage.tsx**: User profile and security settings page.
  - **Updated Implementation**: Now uses Material UI with custom styled components
  - **Design Features**:
    - Clean, spacious layout with animated transitions
    - Gradient text headings and hover effects on cards
    - User avatar with email initials 
    - Card-based information grouping with consistent spacing
    - Custom styled Material UI components (StyledCard, InfoListItem, etc.)
    - Responsive design that adapts to mobile and desktop views
  - **Organization**: 
    - User Information card with email, ID, authentication method, creation date
    - Security & Privacy card with password management and data protection info
    - Visually distinct sign-out button with hover animation
  - **Interaction Enhancements**:
    - Interactive hover states for all elements
    - Smooth transitions and subtle animations
    - Clear visual hierarchy with proper spacing between elements
- **AuthCallbackPage.tsx**: Handles OAuth redirects.

### Form Components
- **NewSignupForm.tsx**: 
  - Form fields: email, password, confirm password, terms agreement
  - Form validation with error handling
  - Password visibility toggles
  - Google OAuth button integration
  - Error/success messaging
  - Navigation to login after registration

- **LoginForm.tsx**:
  - Email/password fields with validation
  - "Remember me" option
  - Password reset link
  - Google OAuth button
  - Error handling

- **ResetPasswordForm.tsx**:
  - Email field with validation
  - Success/error states
  - Return to login link

- **GoogleAuthButton.tsx**:
  - Reusable Google OAuth button
  - Loading state handling

### UI Design System (Auth Specific)
- **Color Palette**:
  - Background: `#0F1A2E` (dark blue)
  - Form background: `#0A2342/10` (semi-transparent) or `#FFFFFF20` for inputs
  - Primary: `#2D7D90` (teal)
  - Secondary: `#1A5F7A` (darker teal for gradients)
  - Text: `#FFFFFF` (white), `#E0E6ED` (light gray)
  - Muted text: `#E0E6ED/70` (semi-transparent white)

- **Layout**:
  - Split-panel design (40/60 ratio) for Login/Signup.
  - Left panel: Decorative (e.g., abstract vascular pattern placeholder).
  - Right panel: Form container.
  - Responsive: Collapses to single panel on mobile.
  - **Account Page**: Single-column card layout with responsive adaptation for mobile.

- **Typography**:
  - Font family: `Inter, SF Pro`
  - Headings: 28px, 600 weight
  - Form labels: 14px (placeholder), 12px (active/floating)
  - Button text: 16px, 600 weight

- **Form Components**:
  - Floating labels (Tailwind `peer` implementation in `NewSignupForm.tsx`).
  - Focused states with teal ring (`focus:ring-[#2D7D90]`).
  - Semi-transparent input backgrounds (`bg-[#FFFFFF20]`).
  - Password visibility toggles (`react-icons`).
  - Custom checkboxes (Tailwind styled).
  - Error messages in red alert box (`bg-red-500/20 text-red-300`).

## Authentication Flows

### Registration Flow
1. User completes signup form (`NewSignupForm.tsx` on `NewSignupPage.tsx`).
2. Frontend validation (password match, terms checked, etc.).
3. `signUp()` from `AuthContext` called with email/password.
4. Supabase creates user account.
5. Success redirects to login page (`/login`).
6. Optional email verification (if configured in Supabase).

### Login Flow
1. User enters credentials on `LoginPage.tsx` (`LoginForm.tsx`).
2. `signIn()` from `AuthContext` called with email/password.
3. Success redirects to dashboard/home (`/dashboard` or `/`).
4. JWT stored in local storage by Supabase client library.
5. Auth context updated with user details.

### Google OAuth Flow
1. User clicks Google button (`GoogleAuthButton.tsx`).
2. `signInWithGoogle()` from `AuthContext` initiates OAuth redirect.
3. User authenticates with Google.
4. Redirect to `/auth/callback` (`AuthCallbackPage.tsx`).
5. Callback page handles token exchange via Supabase client library.
6. Success redirects to dashboard/home.

### Password Reset Flow
1. User requests reset with email on `ResetPasswordPage.tsx` (`ResetPasswordForm.tsx`).
2. `resetPassword()` from `AuthContext` called.
3. Supabase sends reset email.
4. User clicks link in email.
5. Redirected to password reset confirmation page (handled by Supabase or a dedicated app route).
6. User sets new password.

### Protected Routes
- `ProtectedRoute.tsx` component wraps private routes in `App.tsx`.
- Checks authentication status using `useAuth()` from `AuthContext`.
- Redirects to `/login` if not authenticated.
- Can be configured for role-based access (not currently implemented).

## Backend Integration

### Supabase Configuration
- **Client Setup**: `src/services/supabaseClient.ts` (Assumed location, verify if needed).
- **Environment Variables**:
  - `VITE_SUPABASE_URL`: Project URL.
  - `VITE_SUPABASE_ANON_KEY`: Public API key.

### User Data Storage
- **Supabase Auth Users**: Managed by Supabase (`auth.users` table).
- **User Profiles Table (`profiles`)**: Stores additional application-specific user data (name, dob, gender, favorites, etc.).
- **Foreign Key**: `user_id` column in `profiles` table should link to Supabase Auth users (`auth.users.id`). (Need to verify if this link/trigger exists).
- **Profile Creation**: Triggered on successful signup (likely via Supabase trigger or backend logic).

### API Authentication (Backend)
- **JWT Verification**: Backend API (FastAPI) validates Supabase JWTs sent in the `Authorization: Bearer <token>` header.
- **Middleware**: `app/core/auth.py` likely contains dependency/middleware to handle token decoding and validation.
- **User Context**: API endpoints access current user ID via the auth dependency.
- **Data Filtering**: Database queries in backend services are filtered by the authenticated `user_id` to ensure data isolation.

## Form Validation Rules

- **Email**: Standard format validation.
- **Password**: Minimum 6 characters.
- **Confirm Password**: Must match password field.
- **Terms Agreement**: Must be checked before submission.
- **All Fields**: Required validation.

## Error Handling

- **Validation Errors**: Displayed inline below fields or in a summary area within the form component.
- **API Errors**: Shown in styled alert box (`bg-red-500/20`) with user-friendly message.
- **Network Errors**: Handled with general error messages.
- **OAuth Errors**: Redirected back from Supabase/Google with error messages displayed on the login/signup page.

## Testing Implementation

- **Unit Tests**: Form validation logic, `AuthContext` functions (mocking Supabase client), utility functions.
- **Integration Tests**: Testing interaction between components and context, mocking API/Supabase calls.
- **E2E Tests**: User journeys (signup, login, reset password, social login) using frameworks like Cypress or Playwright (if implemented).

## Google OAuth Integration

### Implementation
The application uses Supabase's built-in OAuth providers to handle Google authentication. The integration is configured in the `AuthContext.tsx` file:

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
      queryParams: {
        prompt: 'select_account',  // Force Google to show the account selection screen
        access_type: 'online'      // Request fresh token each time
      }
    },
  });
};
```

### Key Features
1. **Configurable Redirect URL**: Uses `VITE_FRONTEND_URL` environment variable or falls back to `window.location.origin`
2. **Account Selection**: Forces Google to display the account selection screen with `prompt: 'select_account'`
3. **Fresh Token**: Requests a new token with each authentication using `access_type: 'online'`
4. **Callback Handling**: Redirects to `/auth/callback` for processing the authentication response

### OAuth Flow
1. User clicks "Sign in with Google"
2. Application calls `signInWithGoogle()`
3. Redirects to Google's authorization endpoint with parameters to show account selection
4. User selects their Google account and grants permissions
5. Google redirects back to `/auth/callback` endpoint
6. `AuthCallbackPage` component processes the token and establishes the session
7. User is redirected to the dashboard

### Multi-Account Support
The application is specifically configured to support users with multiple Google accounts:
- The `prompt: 'select_account'` parameter ensures users can choose which account to use
- This prevents automatic sign-in with the last used account, improving user control
- The approach balances security and convenience for users with multiple profiles

This comprehensive reference provides all necessary context for any LLM IDE to understand and work with the authentication system in the Vein Diagram application.
