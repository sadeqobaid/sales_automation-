"""
Author Sadeq Obaid and Abdallah Obaid

Audit logging module for the Sales Automation System.
This module provides functionality for comprehensive audit logging.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import Session, relationship
import json
import socket
import uuid

from src.models.base import BaseModel
from config.database import Base


class AuditLog(BaseModel):
    """
    AuditLog model for the Sales Automation System.
    
    This class represents an audit log entry in the system.
    """
    __tablename__ = 'audit_log'
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True, index=True)
    description = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    event_id = Column(String(36), nullable=False, unique=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    
    def __repr__(self) -> str:
        """String representation of the AuditLog model."""
        return f"<AuditLog {self.action} on {self.resource_type}:{self.resource_id} by user {self.user_id}>"


class AuditLogger:
    """Audit logging handler for system activities."""
    
    @staticmethod
    def log_activity(
        db: Session,
        user_id: Optional[int],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        description: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        """
        Log an activity in the audit log.
        
        Args:
            db: Database session
            user_id: User ID (can be None for system actions)
            action: Action performed (e.g., create, update, delete)
            resource_type: Type of resource (e.g., user, contact, lead)
            resource_id: ID of the resource (optional)
            description: Description of the activity (optional)
            ip_address: IP address of the user (optional)
            user_agent: User agent of the user (optional)
            old_values: Old values before the action (optional)
            new_values: New values after the action (optional)
            
        Returns:
            AuditLog: Created audit log entry
        """
        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            old_values=old_values,
            new_values=new_values,
            event_id=str(uuid.uuid4())
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    def get_logs_for_resource(
        db: Session,
        resource_type: str,
        resource_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific resource.
        
        Args:
            db: Database session
            resource_type: Type of resource
            resource_id: ID of the resource
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[AuditLog]: List of audit logs
        """
        return db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_logs_for_user(
        db: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific user.
        
        Args:
            db: Database session
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[AuditLog]: List of audit logs
        """
        return db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_logs_by_action(
        db: Session,
        action: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific action.
        
        Args:
            db: Database session
            action: Action type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[AuditLog]: List of audit logs
        """
        return db.query(AuditLog).filter(
            AuditLog.action == action
        ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_logs_by_date_range(
        db: Session,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0,
        limit: int = 100
    ) -> List[AuditLog]:
        """
        Get audit logs for a specific date range.
        
        Args:
            db: Database session
            start_date: Start date
            end_date: End date
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[AuditLog]: List of audit logs
        """
        return db.query(AuditLog).filter(
            AuditLog.created_at >= start_date,
            AuditLog.created_at <= end_date
        ).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()


# Create audit logger instance
audit_logger = AuditLogger()
