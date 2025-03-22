"""
Author Sadeq Obaid and Abdallah Obaid

User model module for the Sales Automation System.
This module provides the user model and related functionality.
"""

from typing import Optional
import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from src.models.base import BaseModel
from config.database import Base

# Many-to-many relationship between users and roles
user_roles = Table(
    'user_roles',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('user.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('role.id'), primary_key=True)
)

class User(BaseModel):
    """
    User model for the Sales Automation System.
    
    This class represents a user in the system with authentication
    and authorization information.
    """
    __tablename__ = 'user'
    
    # User identification and authentication
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # User profile information
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    phone_number = Column(String(20), nullable=True)
    profile_picture = Column(String(255), nullable=True)
    
    # Account status and security
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Account activity tracking
    last_login = Column(DateTime, nullable=True)
    login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    
    # Relationships
    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the User model."""
        return f"<User {self.username}>"
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username
    
    @property
    def is_locked(self) -> bool:
        """Check if the user account is locked."""
        if not self.locked_until:
            return False
        return self.locked_until > datetime.datetime.now()
    
    def increment_login_attempts(self) -> None:
        """Increment the login attempts counter."""
        self.login_attempts += 1
        # Lock account after 5 failed attempts for 30 minutes
        if self.login_attempts >= 5:
            self.locked_until = datetime.datetime.now() + datetime.timedelta(minutes=30)
    
    def reset_login_attempts(self) -> None:
        """Reset the login attempts counter."""
        self.login_attempts = 0
        self.locked_until = None
    
    def record_login(self) -> None:
        """Record a successful login."""
        self.last_login = datetime.datetime.now()
        self.reset_login_attempts()


class Role(BaseModel):
    """
    Role model for the Sales Automation System.
    
    This class represents a role in the system for authorization purposes.
    """
    __tablename__ = 'role'
    
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    
    # Relationships
    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("RolePermission", back_populates="role")
    
    def __repr__(self) -> str:
        """String representation of the Role model."""
        return f"<Role {self.name}>"


class Permission(BaseModel):
    """
    Permission model for the Sales Automation System.
    
    This class represents a permission in the system for fine-grained access control.
    """
    __tablename__ = 'permission'
    
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    resource = Column(String(50), nullable=False)  # The resource this permission applies to
    action = Column(String(50), nullable=False)    # The action allowed on the resource
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")
    
    def __repr__(self) -> str:
        """String representation of the Permission model."""
        return f"<Permission {self.name}>"


class RolePermission(BaseModel):
    """
    RolePermission model for the Sales Automation System.
    
    This class represents the many-to-many relationship between roles and permissions.
    """
    __tablename__ = 'role_permission'
    
    role_id = Column(Integer, ForeignKey('role.id'), nullable=False)
    permission_id = Column(Integer, ForeignKey('permission.id'), nullable=False)
    
    # Relationships
    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_permissions")
    
    def __repr__(self) -> str:
        """String representation of the RolePermission model."""
        return f"<RolePermission {self.role_id}:{self.permission_id}>"


class AuditLog(BaseModel):
    """
    AuditLog model for the Sales Automation System.
    
    This class represents an audit log entry for tracking security-relevant events.
    """
    __tablename__ = 'audit_log'
    
    user_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    action = Column(String(50), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(50), nullable=True)
    details = Column(String(1000), nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    timestamp = Column(DateTime, default=func.now(), nullable=False)
    
    def __repr__(self) -> str:
        """String representation of the AuditLog model."""
        return f"<AuditLog {self.action} on {self.resource_type}:{self.resource_id}>"
