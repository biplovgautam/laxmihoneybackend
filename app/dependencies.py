"""
FastAPI Dependencies for Authentication and Authorization
Provides reusable dependency functions for securing endpoints
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.firebase_config import verify_firebase_token

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Validate Firebase ID token and extract user ID
    
    This dependency function validates the Firebase authentication token
    and returns the user's UID if valid. Raises HTTPException if invalid.
    
    Args:
        credentials: HTTP Authorization header with Bearer token
        
    Returns:
        User ID (UID) from Firebase token
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # Verify the Firebase ID token
        decoded_token = verify_firebase_token(token)
        
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract user ID from token
        user_id = decoded_token.get("uid")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user_id
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Catch any other errors during token verification
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(
        HTTPBearer(auto_error=False)
    )
) -> Optional[str]:
    """
    Optional authentication - returns user ID if token is valid, None otherwise
    
    This dependency allows endpoints to work for both authenticated and
    non-authenticated users.
    
    Args:
        credentials: Optional HTTP Authorization header with Bearer token
        
    Returns:
        User ID if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        decoded_token = verify_firebase_token(token)
        
        if decoded_token and "uid" in decoded_token:
            return decoded_token["uid"]
        
        return None
        
    except Exception as e:
        # If token verification fails, just return None (don't raise error)
        print(f"Optional auth failed: {e}")
        return None
