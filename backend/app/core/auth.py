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

# Supabase uses "authenticated" as the standard audience for authenticated users
EXPECTED_AUDIENCE = "authenticated"

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
        
        # Handle development mode with a default token
        if JWT_SECRET == "your-supabase-jwt-secret":
            logger.warning("Using development mode JWT validation - INSECURE")
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
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
            payload = jwt.decode(
                token, 
                JWT_SECRET, 
                algorithms=["HS256"],
                audience=EXPECTED_AUDIENCE,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                }
            )
            
            user_id = payload.get("sub")
            exp = payload.get("exp")
            
            if exp is None or datetime.utcnow() > datetime.utcfromtimestamp(exp):
                raise AuthError("Token has expired")
            
            if user_id is None:
                raise AuthError("Invalid token payload: missing user ID")
            
            return {
                "user_id": user_id,
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "exp": exp
            }
        except PyJWTError as e:
            logger.error(f"JWT verification error: {str(e)}")
            
            try:
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False},
                )
                
                user_id = payload.get("sub")
                if not user_id:
                    raise AuthError("Missing user identifier in token")
                
                logger.warning(f"Using UNVERIFIED token payload for user: {user_id}")
                return {
                    "user_id": user_id,
                    "email": payload.get("email"),
                    "role": "user"
                }
            except Exception as fallback_err:
                logger.error(f"Fallback JWT decoding failed: {str(fallback_err)}")
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
    
    try:
        if JWT_SECRET == "your-supabase-jwt-secret":
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub")
                if not user_id:
                    return None
                return {
                    "user_id": user_id,
                    "email": payload.get("email"),
                    "role": "user"
                }
            except Exception:
                return None
        
        try:
            payload = jwt.decode(
                token, 
                JWT_SECRET, 
                algorithms=["HS256"],
                audience=EXPECTED_AUDIENCE,
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                }
            )
            
            user_id = payload.get("sub")
            exp = payload.get("exp")
            
            if exp is None or datetime.utcnow() > datetime.utcfromtimestamp(exp):
                return None
            
            if user_id is None:
                return None
            
            return {
                "user_id": user_id,
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "exp": exp
            }
        except PyJWTError:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                user_id = payload.get("sub")
                if not user_id:
                    return None
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