"""
Author Sadeq Obaid and Abdallah Obaid

Token blacklist module for the Sales Automation System.
This module provides functionality for blacklisting JWT tokens.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.orm import Session

from src.models.base import BaseModel
from config.database import Base


class TokenBlacklist(BaseModel):
    """
    TokenBlacklist model for the Sales Automation System.
    
    This class represents a blacklisted JWT token in the system.
    """
    __tablename__ = 'token_blacklist'
    
    token = Column(String(500), nullable=False, index=True)
    token_type = Column(String(50), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_revoked = Column(Boolean, default=True, nullable=False)
    
    def __repr__(self) -> str:
        """String representation of the TokenBlacklist model."""
        return f"<TokenBlacklist {self.token[:10]}...>"


class TokenBlacklistRepository:
    """Repository for TokenBlacklist model operations."""
    
    def create(self, db: Session, token: str, token_type: str, expires_at: datetime) -> TokenBlacklist:
        """
        Add a token to the blacklist.
        
        Args:
            db: Database session
            token: JWT token
            token_type: Token type (access or refresh)
            expires_at: Token expiration time
            
        Returns:
            TokenBlacklist: Created token blacklist entry
        """
        db_obj = TokenBlacklist(
            token=token,
            token_type=token_type,
            expires_at=expires_at,
            is_revoked=True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def is_blacklisted(self, db: Session, token: str) -> bool:
        """
        Check if a token is blacklisted.
        
        Args:
            db: Database session
            token: JWT token
            
        Returns:
            bool: True if token is blacklisted, False otherwise
        """
        return db.query(TokenBlacklist).filter(
            TokenBlacklist.token == token,
            TokenBlacklist.is_revoked == True
        ).first() is not None
    
    def clean_expired_tokens(self, db: Session) -> int:
        """
        Remove expired tokens from the blacklist.
        
        Args:
            db: Database session
            
        Returns:
            int: Number of tokens removed
        """
        now = datetime.utcnow()
        expired_tokens = db.query(TokenBlacklist).filter(
            TokenBlacklist.expires_at < now
        ).all()
        
        count = len(expired_tokens)
        
        for token in expired_tokens:
            db.delete(token)
        
        db.commit()
        return count


# Create repository instance
token_blacklist_repository = TokenBlacklistRepository()
