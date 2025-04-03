from typing import Dict, Any
from fastapi import HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.logger import logger

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
        # ... existing code ...
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")

    # ... rest of the function ... 