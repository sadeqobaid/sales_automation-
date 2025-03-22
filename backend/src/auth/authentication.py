"""
Author Sadeq Obaid and Abdallah Obaid

Enhanced authentication module for the Sales Automation System.
This module updates the authentication system with improved security features.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import uuid

from src.models.user import User
from src.repositories.user_repository import user_repository
from src.utils.database_utils import get_db
from src.auth.password_security import password_validator
from src.auth.token_blacklist import token_blacklist_repository
from src.auth.refresh_token import refresh_token_repository
from src.auth.audit_logging import audit_logger
from config.settings import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user with username and password.
    
    Args:
        db: Database session
        username: Username
        password: Password
        
    Returns:
        Optional[User]: Authenticated user or None
    """
    user = user_repository.get_by_username(db, username)
    
    if not user:
        return None
    
    if not password_validator.verify_password(password, user.hashed_password):
        # Log failed login attempt
        audit_logger.log_activity(
            db=db,
            user_id=user.id,
            action="login_failed",
            resource_type="user",
            resource_id=user.id,
            description="Failed login attempt"
        )
        return None
    
    # Log successful login
    audit_logger.log_activity(
        db=db,
        user_id=user.id,
        action="login",
        resource_type="user",
        resource_id=user.id,
        description="Successful login"
    )
    
    return user


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Token data
        expires_delta: Token expiration time
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current user from a JWT token.
    
    Args:
        token: JWT token
        db: Database session
        
    Returns:
        User: Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check if token is blacklisted
    if token_blacklist_repository.is_blacklisted(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = int(payload.get("sub"))
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = user_repository.get(db, user_id)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: Current user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def create_tokens_for_user(
    db: Session,
    user: User
) -> Dict[str, str]:
    """
    Create access and refresh tokens for a user.
    
    Args:
        db: Database session
        user: User
        
    Returns:
        Dict[str, str]: Access and refresh tokens
    """
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = refresh_token_repository.create(db, user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token.token,
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


def refresh_access_token(
    db: Session,
    refresh_token: str
) -> Dict[str, str]:
    """
    Refresh an access token using a refresh token.
    
    Args:
        db: Database session
        refresh_token: Refresh token
        
    Returns:
        Dict[str, str]: New access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Get refresh token from database
    db_token = refresh_token_repository.get_by_token(db, refresh_token)
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if token is expired
    if db_token.is_expired:
        # Revoke token
        refresh_token_repository.revoke(db, refresh_token)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user
    user = user_repository.get(db, db_token.user_id)
    
    if not user or not user.is_active:
        # Revoke token
        refresh_token_repository.revoke(db, refresh_token)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Revoke old refresh token (token rotation)
    refresh_token_repository.revoke(db, refresh_token)
    
    # Create new tokens
    return create_tokens_for_user(db, user)


def revoke_token(
    db: Session,
    token: str,
    token_type: str = "access",
    user_id: Optional[int] = None
) -> None:
    """
    Revoke a token.
    
    Args:
        db: Database session
        token: Token to revoke
        token_type: Token type (access or refresh)
        user_id: User ID (optional)
        
    Raises:
        HTTPException: If token type is invalid
    """
    if token_type == "access":
        try:
            # Decode token to get expiration time
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            expires_at = datetime.fromtimestamp(payload.get("exp"))
            
            # Add token to blacklist
            token_blacklist_repository.create(db, token, token_type, expires_at)
            
            # Log token revocation
            if user_id:
                audit_logger.log_activity(
                    db=db,
                    user_id=user_id,
                    action="token_revoked",
                    resource_type="token",
                    description=f"Access token revoked"
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token"
            )
    elif token_type == "refresh":
        # Revoke refresh token
        refresh_token_repository.revoke(db, token)
        
        # Log token revocation
        if user_id:
            audit_logger.log_activity(
                db=db,
                user_id=user_id,
                action="token_revoked",
                resource_type="token",
                description=f"Refresh token revoked"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type"
        )


def revoke_all_user_tokens(
    db: Session,
    user_id: int
) -> None:
    """
    Revoke all tokens for a user.
    
    Args:
        db: Database session
        user_id: User ID
    """
    # Revoke all refresh tokens
    refresh_token_repository.revoke_all_for_user(db, user_id)
    
    # Log token revocation
    audit_logger.log_activity(
        db=db,
        user_id=user_id,
        action="all_tokens_revoked",
        resource_type="token",
        description=f"All tokens revoked for user {user_id}"
    )
