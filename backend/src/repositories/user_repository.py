"""
Author Sadeq Obaid and Abdallah Obaid

User repository module for the Sales Automation System.
This module provides repository classes for user-related models.
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.repositories.base import BaseRepository
from src.models.user import User, Role, Permission, RolePermission, AuditLog


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""
    
    def __init__(self):
        super().__init__(User)
    
    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """
        Get a user by email.
        
        Args:
            db: Database session
            email: User email
            
        Returns:
            Optional[User]: Found user or None
        """
        return db.query(User).filter(User.email == email).first()
    
    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: Username
            
        Returns:
            Optional[User]: Found user or None
        """
        return db.query(User).filter(User.username == username).first()
    
    def get_by_email_or_username(self, db: Session, identifier: str) -> Optional[User]:
        """
        Get a user by email or username.
        
        Args:
            db: Database session
            identifier: Email or username
            
        Returns:
            Optional[User]: Found user or None
        """
        return db.query(User).filter(
            or_(User.email == identifier, User.username == identifier)
        ).first()
    
    def get_active_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """
        Get active users with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[User]: List of active users
        """
        return db.query(User).filter(User.is_active == True).offset(skip).limit(limit).all()
    
    def add_role_to_user(self, db: Session, user_id: int, role_id: int) -> User:
        """
        Add a role to a user.
        
        Args:
            db: Database session
            user_id: User ID
            role_id: Role ID
            
        Returns:
            User: Updated user
        """
        user = self.get(db, user_id)
        role = db.query(Role).get(role_id)
        
        if user is None or role is None:
            raise ValueError(f"User with id {user_id} or Role with id {role_id} not found")
        
        user.roles.append(role)
        db.commit()
        db.refresh(user)
        return user
    
    def remove_role_from_user(self, db: Session, user_id: int, role_id: int) -> User:
        """
        Remove a role from a user.
        
        Args:
            db: Database session
            user_id: User ID
            role_id: Role ID
            
        Returns:
            User: Updated user
        """
        user = self.get(db, user_id)
        role = db.query(Role).get(role_id)
        
        if user is None or role is None:
            raise ValueError(f"User with id {user_id} or Role with id {role_id} not found")
        
        user.roles.remove(role)
        db.commit()
        db.refresh(user)
        return user


class RoleRepository(BaseRepository[Role]):
    """Repository for Role model operations."""
    
    def __init__(self):
        super().__init__(Role)
    
    def get_by_name(self, db: Session, name: str) -> Optional[Role]:
        """
        Get a role by name.
        
        Args:
            db: Database session
            name: Role name
            
        Returns:
            Optional[Role]: Found role or None
        """
        return db.query(Role).filter(Role.name == name).first()
    
    def get_users_with_role(self, db: Session, role_id: int) -> List[User]:
        """
        Get all users with a specific role.
        
        Args:
            db: Database session
            role_id: Role ID
            
        Returns:
            List[User]: List of users with the role
        """
        role = self.get(db, role_id)
        if role is None:
            raise ValueError(f"Role with id {role_id} not found")
        
        return role.users
    
    def add_permission_to_role(self, db: Session, role_id: int, permission_id: int) -> Role:
        """
        Add a permission to a role.
        
        Args:
            db: Database session
            role_id: Role ID
            permission_id: Permission ID
            
        Returns:
            Role: Updated role
        """
        role = self.get(db, role_id)
        permission = db.query(Permission).get(permission_id)
        
        if role is None or permission is None:
            raise ValueError(f"Role with id {role_id} or Permission with id {permission_id} not found")
        
        role_permission = RolePermission(role_id=role_id, permission_id=permission_id)
        db.add(role_permission)
        db.commit()
        db.refresh(role)
        return role


class PermissionRepository(BaseRepository[Permission]):
    """Repository for Permission model operations."""
    
    def __init__(self):
        super().__init__(Permission)
    
    def get_by_name(self, db: Session, name: str) -> Optional[Permission]:
        """
        Get a permission by name.
        
        Args:
            db: Database session
            name: Permission name
            
        Returns:
            Optional[Permission]: Found permission or None
        """
        return db.query(Permission).filter(Permission.name == name).first()
    
    def get_by_resource_and_action(self, db: Session, resource: str, action: str) -> Optional[Permission]:
        """
        Get a permission by resource and action.
        
        Args:
            db: Database session
            resource: Resource name
            action: Action name
            
        Returns:
            Optional[Permission]: Found permission or None
        """
        return db.query(Permission).filter(
            Permission.resource == resource,
            Permission.action == action
        ).first()
    
    def get_permissions_for_role(self, db: Session, role_id: int) -> List[Permission]:
        """
        Get all permissions for a specific role.
        
        Args:
            db: Database session
            role_id: Role ID
            
        Returns:
            List[Permission]: List of permissions for the role
        """
        role = db.query(Role).get(role_id)
        if role is None:
            raise ValueError(f"Role with id {role_id} not found")
        
        return [rp.permission for rp in role.permissions]


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository for AuditLog model operations."""
    
    def __init__(self):
        super().__init__(AuditLog)
    
    def get_logs_by_user(self, db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[AuditLog]:
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
        return db.query(AuditLog).filter(AuditLog.user_id == user_id).order_by(
            AuditLog.timestamp.desc()
        ).offset(skip).limit(limit).all()
    
    def get_logs_by_action(self, db: Session, action: str, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs for a specific action.
        
        Args:
            db: Database session
            action: Action name
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[AuditLog]: List of audit logs
        """
        return db.query(AuditLog).filter(AuditLog.action == action).order_by(
            AuditLog.timestamp.desc()
        ).offset(skip).limit(limit).all()
    
    def get_logs_by_resource(self, db: Session, resource_type: str, resource_id: Optional[str] = None, 
                            skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Get audit logs for a specific resource.
        
        Args:
            db: Database session
            resource_type: Resource type
            resource_id: Optional resource ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[AuditLog]: List of audit logs
        """
        query = db.query(AuditLog).filter(AuditLog.resource_type == resource_type)
        
        if resource_id is not None:
            query = query.filter(AuditLog.resource_id == resource_id)
            
        return query.order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit).all()
