"""
Author Sadeq Obaid and Abdallah Obaid

Role-based access control module for the Sales Automation System.
This module provides functionality for RBAC implementation.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Set
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
import functools

from src.models.user import User, Role, Permission
from src.utils.database_utils import get_db
from src.auth.authentication import get_current_active_user


class ResourceType(str, Enum):
    """Enumeration of resource types for permission checking."""
    USER = "user"
    CONTACT = "contact"
    LEAD = "lead"
    OPPORTUNITY = "opportunity"
    CAMPAIGN = "campaign"
    REPORT = "report"
    SETTING = "setting"


class ActionType(str, Enum):
    """Enumeration of action types for permission checking."""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXPORT = "export"
    IMPORT = "import"
    ASSIGN = "assign"
    CONVERT = "convert"


class RBACHandler:
    """Role-based access control handler."""
    
    @staticmethod
    def has_permission(
        user: User,
        resource: ResourceType,
        action: ActionType
    ) -> bool:
        """
        Check if a user has permission to perform an action on a resource.
        
        Args:
            user: User to check
            resource: Resource type
            action: Action type
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Admin role has all permissions
        if any(role.name == "admin" for role in user.roles):
            return True
        
        # Check if user has the specific permission
        permission_name = f"{resource.value}:{action.value}"
        
        for role in user.roles:
            for permission in role.permissions:
                if permission.name == permission_name:
                    return True
        
        return False
    
    @staticmethod
    def has_object_permission(
        user: User,
        obj: Any,
        action: ActionType
    ) -> bool:
        """
        Check if a user has permission to perform an action on a specific object.
        
        Args:
            user: User to check
            obj: Object to check
            action: Action type
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Admin role has all permissions
        if any(role.name == "admin" for role in user.roles):
            return True
        
        # Owner can perform all actions on their objects
        if hasattr(obj, "owner_id") and obj.owner_id == user.id:
            return True
        
        # Creator can perform all actions on their objects
        if hasattr(obj, "created_by") and obj.created_by == user.id:
            return True
        
        # Manager role can perform most actions
        if any(role.name == "manager" for role in user.roles):
            # Managers can't delete certain objects
            if action == ActionType.DELETE and hasattr(obj, "protected"):
                return not obj.protected
            return True
        
        # For other roles, check specific permissions
        resource_type = ResourceType(obj.__tablename__)
        return RBACHandler.has_permission(user, resource_type, action)


def require_permission(resource: ResourceType, action: ActionType):
    """
    Decorator to require permission for an endpoint.
    
    Args:
        resource: Resource type
        action: Action type
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_active_user), **kwargs):
            if not RBACHandler.has_permission(current_user, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


def require_object_permission(action: ActionType, obj_param: str = "obj"):
    """
    Decorator to require permission for an object in an endpoint.
    
    Args:
        action: Action type
        obj_param: Parameter name for the object
        
    Returns:
        Callable: Decorator function
    """
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, current_user: User = Depends(get_current_active_user), **kwargs):
            obj = kwargs.get(obj_param)
            if obj is None:
                raise ValueError(f"Parameter '{obj_param}' not found")
            
            if not RBACHandler.has_object_permission(current_user, obj, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not enough permissions"
                )
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator


# Create RBAC handler instance
rbac_handler = RBACHandler()
