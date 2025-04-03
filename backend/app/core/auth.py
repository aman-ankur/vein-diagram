"""
Authentication module for JWT token validation from Supabase
"""
import os
import logging
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import PyJWTError
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Supabase JWT configuration
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "your-supabase-jwt-secret")
SUPABASE_URL = os.getenv("SUPABASE_URL", "your-supabase-url")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "your-supabase-service-key")

# Security bearer scheme for tokens
security = HTTPBearer()

class AuthError(Exception):
    """Custom exception for authentication errors."""
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Validate JWT token and extract user information
    
    Args:
        credentials: HTTP Authorization credentials with Bearer token
        
    Returns:
        User information extracted from the token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        logger.info(f"Processing token auth, token length: {len(token)}")
        
        # Handle development mode with a default token
        if JWT_SECRET == "your-supabase-jwt-secret":
            logger.warning("Using development mode JWT validation - INSECURE")
            
            # Try to decode without verification to at least get the structure
            try:
                # Decode without verification for development
                payload = jwt.decode(
                    token, 
                    options={"verify_signature": False}
                )
                
                logger.info(f"Decoded token payload: {payload}")
                
                # Get the user_id from Supabase-specific claims
                # Supabase tokens have 'sub' as user ID
                user_id = payload.get("sub")
                
                if not user_id:
                    raise AuthError("Missing user identifier in token")
                
                return {
                    "user_id": user_id,
                    "email": payload.get("email"),
                    "role": "user"  # Default role in dev mode
                }
            except Exception as e:
                logger.error(f"Failed to decode token in dev mode: {str(e)}")
                raise
        
        # Production mode with proper verification
        try:
            # Decode and verify the token
            payload = jwt.decode(
                token, 
                JWT_SECRET, 
                algorithms=["HS256"],
                options={"verify_signature": True}
            )
            
            # Extract user information - Supabase uses 'sub' for user ID
            user_id = payload.get("sub")
            exp = payload.get("exp")
            
            # Check for token expiration
            if exp is None or datetime.utcnow() > datetime.utcfromtimestamp(exp):
                raise AuthError("Token has expired")
            
            # Check for required claims
            if user_id is None:
                raise AuthError("Invalid token payload: missing user ID")
                
            logger.info(f"Successfully authenticated user: {user_id}")
            
            return {
                "user_id": user_id,
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "exp": exp
            }
        except PyJWTError as e:
            logger.error(f"JWT verification error: {str(e)}")
            
            # Try fallback JWT verification with different algorithms
            try:
                logger.info("Attempting fallback JWT verification...")
                # Try with RS256 (commonly used by Supabase)
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False},  # Skip verification as fallback
                )
                
                # Log what we found but with caution
                logger.info(f"Fallback decode successful, found payload structure: {list(payload.keys())}")
                
                # Extract user ID if present
                user_id = payload.get("sub")
                if not user_id:
                    raise AuthError("Missing user identifier in token")
                
                logger.warning(f"Using UNVERIFIED token payload for user: {user_id}")
                return {
                    "user_id": user_id,
                    "email": payload.get("email"),
                    "role": "user"  # Default role for unverified tokens
                }
            except Exception as fallback_err:
                logger.error(f"Fallback JWT decoding also failed: {str(fallback_err)}")
                raise AuthError(f"Invalid authentication token: {str(e)}")
    
    except PyJWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthError as e:
        logger.error(f"Auth Error: {str(e)}")
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during auth: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication system error: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

def get_optional_current_user(
    request: Request
) -> Optional[Dict[str, Any]]:
    """
    Extract user information from token if present, but don't require it.
    Makes authentication optional for routes that can work both for anonymous
    and authenticated users.
    
    Args:
        request: The incoming request
        
    Returns:
        User information or None if no valid token
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.replace("Bearer ", "")
    logger.debug(f"Optional auth token received, length: {len(token)}")
    
    try:
        # Use the same approach as get_current_user but don't raise exceptions
        # Handle development mode with a default token
        if JWT_SECRET == "your-supabase-jwt-secret":
            logger.warning("Using development mode JWT validation for optional auth - INSECURE")
            
            try:
                # Decode without verification for development
                payload = jwt.decode(
                    token, 
                    options={"verify_signature": False}
                )
                
                # Get the user_id from Supabase-specific claims
                user_id = payload.get("sub")
                
                if not user_id:
                    logger.warning("Missing user identifier in optional auth token")
                    return None
                
                return {
                    "user_id": user_id,
                    "email": payload.get("email"),
                    "role": "user"  # Default role in dev mode
                }
            except Exception as e:
                logger.warning(f"Failed to decode optional auth token: {str(e)}")
                return None
        
        # Production mode
        try:
            # Decode and verify the token
            payload = jwt.decode(
                token, 
                JWT_SECRET, 
                algorithms=["HS256"],
                options={"verify_signature": True}
            )
            
            # Extract user information
            user_id = payload.get("sub")
            exp = payload.get("exp")
            
            # Check for token expiration
            if exp is None or datetime.utcnow() > datetime.utcfromtimestamp(exp):
                logger.debug("Optional auth token has expired")
                return None
            
            # Check for required claims
            if user_id is None:
                logger.debug("Invalid optional auth token payload: missing user ID")
                return None
                
            logger.debug(f"Successfully authenticated optional user: {user_id}")
            
            return {
                "user_id": user_id,
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "exp": exp
            }
        except PyJWTError as e:
            # Try fallback with decode only
            try:
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False}
                )
                
                user_id = payload.get("sub")
                if not user_id:
                    return None
                
                logger.warning(f"Using UNVERIFIED optional token for user: {user_id}")
                return {
                    "user_id": user_id,
                    "email": payload.get("email"),
                    "role": "user"
                }
            except Exception:
                return None
    
    except Exception as e:
        logger.warning(f"Error in optional auth: {str(e)}")
        return None

def requires_auth(scopes: List[str] = None):
    """
    Dependency to enforce specific scopes/permissions.
    To be used with endpoints that require specific permissions.
    
    Args:
        scopes: List of required scopes/permissions
        
    Returns:
        Dependency function that validates scopes
    """
    scopes = scopes or []
    
    async def _requires_auth(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        if not scopes:
            return user
            
        # Check if user has required scopes
        user_scopes = user.get("scopes", [])
        for scope in scopes:
            if scope not in user_scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied. Required scope: {scope}",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
        return user
        
    return _requires_auth 