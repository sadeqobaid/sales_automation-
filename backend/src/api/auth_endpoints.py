"""
Author Sadeq Obaid and Abdallah Obaid

Authentication API endpoints for the Sales Automation System.
This module provides API endpoints for user authentication.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Dict, Any

from src.auth.authentication import authenticate_user, create_access_token, get_current_active_user
from src.models.user import User
from src.utils.database_utils import get_db
from config.settings import ACCESS_TOKEN_EXPIRE_MINUTES

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/token", response_model=Dict[str, Any])
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get an access token for authentication.
    
    Args:
        form_data: OAuth2 password request form
        db: Database session
        
    Returns:
        Dict[str, Any]: Access token and token type
        
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if user.is_locked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is locked due to too many failed login attempts",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active
    }


@router.get("/me", response_model=Dict[str, Any])
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get information about the current authenticated user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: User information
    """
    user_data = {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "last_login": current_user.last_login
    }
    
    # Add roles if available
    if current_user.roles:
        user_data["roles"] = [{"id": role.id, "name": role.name} for role in current_user.roles]
    
    return user_data
