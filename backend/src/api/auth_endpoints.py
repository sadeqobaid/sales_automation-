"""
Author Sadeq Obaid and Abdallah Obaid

Updated authentication endpoints for the Sales Automation System.
This module provides enhanced API endpoints for authentication with improved security features.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from src.auth.authentication import (
    authenticate_user, 
    create_tokens_for_user, 
    refresh_access_token,
    revoke_token,
    revoke_all_user_tokens,
    get_current_active_user
)
from src.auth.password_security import password_validator
from src.auth.audit_logging import audit_logger
from src.models.user import User
from src.repositories.user_repository import user_repository
from src.utils.database_utils import get_db

# Create router
router = APIRouter(
    prefix="/auth",
    tags=["authentication"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/login", response_model=Dict[str, Any])
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Authenticate a user and return access and refresh tokens.
    
    Args:
        request: Request object
        form_data: OAuth2 password request form
        db: Database session
        
    Returns:
        Dict[str, Any]: Access and refresh tokens
        
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
    
    # Get client info for audit logging
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Log successful login with client info
    audit_logger.log_activity(
        db=db,
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=user.id,
        description="User logged in",
        ip_address=client_host,
        user_agent=user_agent
    )
    
    # Create tokens
    return create_tokens_for_user(db, user)


@router.post("/refresh", response_model=Dict[str, Any])
async def refresh_token(
    request: Request,
    refresh_token: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Refresh an access token using a refresh token.
    
    Args:
        request: Request object
        refresh_token: Refresh token
        db: Database session
        
    Returns:
        Dict[str, Any]: New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        tokens = refresh_access_token(db, refresh_token)
        
        # Get client info for audit logging
        client_host = request.client.host if request.client else None
        user_agent = request.headers.get("user-agent")
        
        # Log token refresh
        audit_logger.log_activity(
            db=db,
            user_id=None,  # We don't have user ID at this point
            action="token_refresh",
            resource_type="token",
            description="Token refreshed",
            ip_address=client_host,
            user_agent=user_agent
        )
        
        return tokens
    except HTTPException as e:
        # Re-raise the exception
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    access_token: str,
    refresh_token: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """
    Logout a user by revoking their tokens.
    
    Args:
        request: Request object
        response: Response object
        access_token: Access token to revoke
        refresh_token: Refresh token to revoke (optional)
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        None
    """
    # Revoke access token
    revoke_token(db, access_token, "access", current_user.id)
    
    # Revoke refresh token if provided
    if refresh_token:
        revoke_token(db, refresh_token, "refresh", current_user.id)
    
    # Get client info for audit logging
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Log logout
    audit_logger.log_activity(
        db=db,
        user_id=current_user.id,
        action="logout",
        resource_type="user",
        resource_id=current_user.id,
        description="User logged out",
        ip_address=client_host,
        user_agent=user_agent
    )
    
    # Clear cookies if they exist
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all_sessions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """
    Logout a user from all sessions by revoking all their tokens.
    
    Args:
        request: Request object
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        None
    """
    # Revoke all tokens for the user
    revoke_all_user_tokens(db, current_user.id)
    
    # Get client info for audit logging
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Log logout from all sessions
    audit_logger.log_activity(
        db=db,
        user_id=current_user.id,
        action="logout_all",
        resource_type="user",
        resource_id=current_user.id,
        description="User logged out from all sessions",
        ip_address=client_host,
        user_agent=user_agent
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    request: Request,
    current_password: str,
    new_password: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """
    Change a user's password.
    
    Args:
        request: Request object
        current_password: Current password
        new_password: New password
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        None
        
    Raises:
        HTTPException: If current password is incorrect or new password is invalid
    """
    # Verify current password
    if not password_validator.verify_password(current_password, current_user.hashed_password):
        # Log failed password change attempt
        audit_logger.log_activity(
            db=db,
            user_id=current_user.id,
            action="password_change_failed",
            resource_type="user",
            resource_id=current_user.id,
            description="Failed password change attempt: incorrect current password"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Validate new password
    is_valid, errors = password_validator.validate_password(new_password)
    
    if not is_valid:
        # Log failed password change attempt
        audit_logger.log_activity(
            db=db,
            user_id=current_user.id,
            action="password_change_failed",
            resource_type="user",
            resource_id=current_user.id,
            description=f"Failed password change attempt: invalid new password - {', '.join(errors)}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid password", "errors": errors}
        )
    
    # Hash new password
    hashed_password = password_validator.hash_password(new_password)
    
    # Update user
    user_repository.update(db, db_obj=current_user, obj_in={"hashed_password": hashed_password})
    
    # Revoke all tokens for the user
    revoke_all_user_tokens(db, current_user.id)
    
    # Get client info for audit logging
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Log password change
    audit_logger.log_activity(
        db=db,
        user_id=current_user.id,
        action="password_change",
        resource_type="user",
        resource_id=current_user.id,
        description="User changed password",
        ip_address=client_host,
        user_agent=user_agent
    )


@router.post("/request-password-reset", status_code=status.HTTP_204_NO_CONTENT)
async def request_password_reset(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
) -> None:
    """
    Request a password reset.
    
    Args:
        request: Request object
        email: User email
        db: Database session
        
    Returns:
        None
    """
    # Find user by email
    user = user_repository.get_by_email(db, email)
    
    # Always return success to prevent email enumeration
    if not user:
        return
    
    # Generate password reset token
    reset_token = user_repository.create_password_reset_token(db, user.id)
    
    # In a real application, send an email with the reset token
    # For now, just log it
    
    # Get client info for audit logging
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Log password reset request
    audit_logger.log_activity(
        db=db,
        user_id=user.id,
        action="password_reset_request",
        resource_type="user",
        resource_id=user.id,
        description="User requested password reset",
        ip_address=client_host,
        user_agent=user_agent
    )


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    request: Request,
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
) -> None:
    """
    Reset a user's password using a reset token.
    
    Args:
        request: Request object
        token: Password reset token
        new_password: New password
        db: Database session
        
    Returns:
        None
        
    Raises:
        HTTPException: If token is invalid or new password is invalid
    """
    # Verify token and get user
    user = user_repository.verify_password_reset_token(db, token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Validate new password
    is_valid, errors = password_validator.validate_password(new_password)
    
    if not is_valid:
        # Log failed password reset attempt
        audit_logger.log_activity(
            db=db,
            user_id=user.id,
            action="password_reset_failed",
            resource_type="user",
            resource_id=user.id,
            description=f"Failed password reset attempt: invalid new password - {', '.join(errors)}"
        )
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid password", "errors": errors}
        )
    
    # Hash new password
    hashed_password = password_validator.hash_password(new_password)
    
    # Update user
    user_repository.update(db, db_obj=user, obj_in={"hashed_password": hashed_password})
    
    # Revoke all tokens for the user
    revoke_all_user_tokens(db, user.id)
    
    # Get client info for audit logging
    client_host = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Log password reset
    audit_logger.log_activity(
        db=db,
        user_id=user.id,
        action="password_reset",
        resource_type="user",
        resource_id=user.id,
        description="User reset password",
        ip_address=client_host,
        user_agent=user_agent
    )


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get information about the current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: User information
    """
    return current_user.to_dict()
