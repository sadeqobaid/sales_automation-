"""
Author Sadeq Obaid and Abdallah Obaid

Refresh token module for the Sales Automation System.
This module provides functionality for refresh token management.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Session, relationship
import secrets

from src.models.base import BaseModel
from src.models.user import User
from config.database import Base
from config.settings import REFRESH_TOKEN_EXPIRE_DAYS


class RefreshToken(BaseModel):
    """
    RefreshToken model for the Sales Automation System.
    
    This class represents a refresh token in the system.
    """
    __tablename__ = 'refresh_token'
    
    token = Column(String(255), nullable=False, index=True, unique=True)
    user_id = Column(Integer, ForeignKey('user.id'), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        """String representation of the RefreshToken model."""
        return f"<RefreshToken {self.token[:10]}... for user {self.user_id}>"
    
    @property
    def is_expired(self) -> bool:
        """Check if the token is expired."""
        return datetime.utcnow() > self.expires_at


class RefreshTokenRepository:
    """Repository for RefreshToken model operations."""
    
    def create(self, db: Session, user_id: int) -> RefreshToken:
        """
        Create a new refresh token.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            RefreshToken: Created refresh token
        """
        # Generate a secure random token
        token = secrets.token_urlsafe(64)
        
        # Calculate expiration time
        expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        # Create token
        db_obj = RefreshToken(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get_by_token(self, db: Session, token: str) -> Optional[RefreshToken]:
        """
        Get a refresh token by token string.
        
        Args:
            db: Database session
            token: Token string
            
        Returns:
            Optional[RefreshToken]: Refresh token or None
        """
        return db.query(RefreshToken).filter(
            RefreshToken.token == token,
            RefreshToken.is_revoked == False
        ).first()
    
    def get_by_user(self, db: Session, user_id: int) -> List[RefreshToken]:
        """
        Get all refresh tokens for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            List[RefreshToken]: List of refresh tokens
        """
        return db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.is_revoked == False
        ).all()
    
    def revoke(self, db: Session, token: str) -> Optional[RefreshToken]:
        """
        Revoke a refresh token.
        
        Args:
            db: Database session
            token: Token string
            
        Returns:
            Optional[RefreshToken]: Revoked token or None
        """
        db_obj = self.get_by_token(db, token)
        
        if db_obj:
            db_obj.is_revoked = True
            db.commit()
            db.refresh(db_obj)
            
        return db_obj
    
    def revoke_all_for_user(self, db: Session, user_id: int) -> int:
        """
        Revoke all refresh tokens for a user.
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            int: Number of tokens revoked
        """
        tokens = self.get_by_user(db, user_id)
        
        for token in tokens:
            token.is_revoked = True
        
        db.commit()
        return len(tokens)
    
    def clean_expired_tokens(self, db: Session) -> int:
        """
        Remove expired tokens.
        
        Args:
            db: Database session
            
        Returns:
            int: Number of tokens removed
        """
        now = datetime.utcnow()
        expired_tokens = db.query(RefreshToken).filter(
            RefreshToken.expires_at < now
        ).all()
        
        count = len(expired_tokens)
        
        for token in expired_tokens:
            db.delete(token)
        
        db.commit()
        return count


# Create repository instance
refresh_token_repository = RefreshTokenRepository()
