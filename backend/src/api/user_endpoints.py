"""
Author Sadeq Obaid and Abdallah Obaid

User API endpoints for the Sales Automation System.
This module provides API endpoints for user management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from src.auth.authentication import get_current_active_user, get_password_hash
from src.models.user import User, Role
from src.repositories.user_repository import user_repository, role_repository
from src.utils.database_utils import get_db

# Create router
router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new user.
    
    Args:
        user_data: User data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created user
        
    Raises:
        HTTPException: If user already exists or validation fails
    """
    # Check if user has permission to create users
    # This would be replaced with proper permission checking
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if username or email already exists
    if user_repository.get_by_username(db, user_data["username"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
        
    if user_repository.get_by_email(db, user_data["email"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash the password
    user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    
    # Set created_by
    user_data["created_by"] = current_user.id
    
    # Create user
    user = user_repository.create(db, user_data)
    
    # Add default role if specified
    if "role_id" in user_data:
        user_repository.add_role_to_user(db, user.id, user_data["role_id"])
        db.refresh(user)
    
    # Return user data without password
    user_dict = user.to_dict()
    user_dict.pop("hashed_password", None)
    
    return user_dict


@router.get("/", response_model=List[Dict[str, Any]])
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all users with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of users
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Check if user has permission to view users
    if not any(role.name in ["admin", "manager"] for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    users = user_repository.get_multi(db, skip=skip, limit=limit)
    
    # Return users without passwords
    return [
        {**user.to_dict(), "hashed_password": None}
        for user in users
    ]


@router.get("/{user_id}", response_model=Dict[str, Any])
async def read_user(
    user_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get a specific user by ID.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: User data
        
    Raises:
        HTTPException: If user not found or doesn't have permission
    """
    # Allow users to view their own profile or admins to view any profile
    if current_user.id != user_id and not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = user_repository.get(db, user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Return user without password
    user_dict = user.to_dict()
    user_dict.pop("hashed_password", None)
    
    # Add roles if available
    if user.roles:
        user_dict["roles"] = [{"id": role.id, "name": role.name} for role in user.roles]
    
    return user_dict


@router.put("/{user_id}", response_model=Dict[str, Any])
async def update_user(
    user_id: int = Path(..., gt=0),
    user_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update a user.
    
    Args:
        user_id: User ID
        user_data: User data to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated user
        
    Raises:
        HTTPException: If user not found or doesn't have permission
    """
    # Allow users to update their own profile or admins to update any profile
    if current_user.id != user_id and not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = user_repository.get(db, user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Handle password update
    if "password" in user_data:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
    
    # Set updated_by
    user_data["updated_by"] = current_user.id
    
    # Update user
    updated_user = user_repository.update(db, db_obj=user, obj_in=user_data)
    
    # Return user without password
    user_dict = updated_user.to_dict()
    user_dict.pop("hashed_password", None)
    
    return user_dict


@router.delete("/{user_id}", response_model=Dict[str, Any])
async def delete_user(
    user_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Delete a user.
    
    Args:
        user_id: User ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Deleted user
        
    Raises:
        HTTPException: If user not found or doesn't have permission
    """
    # Only admins can delete users
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = user_repository.get(db, user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    deleted_user = user_repository.delete(db, id=user_id)
    
    # Return user without password
    user_dict = deleted_user.to_dict()
    user_dict.pop("hashed_password", None)
    
    return user_dict


@router.post("/{user_id}/roles/{role_id}", response_model=Dict[str, Any])
async def add_role_to_user(
    user_id: int = Path(..., gt=0),
    role_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Add a role to a user.
    
    Args:
        user_id: User ID
        role_id: Role ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated user
        
    Raises:
        HTTPException: If user or role not found or doesn't have permission
    """
    # Only admins can add roles
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        user = user_repository.add_role_to_user(db, user_id, role_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Return user without password
    user_dict = user.to_dict()
    user_dict.pop("hashed_password", None)
    
    # Add roles
    user_dict["roles"] = [{"id": role.id, "name": role.name} for role in user.roles]
    
    return user_dict


@router.delete("/{user_id}/roles/{role_id}", response_model=Dict[str, Any])
async def remove_role_from_user(
    user_id: int = Path(..., gt=0),
    role_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Remove a role from a user.
    
    Args:
        user_id: User ID
        role_id: Role ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated user
        
    Raises:
        HTTPException: If user or role not found or doesn't have permission
    """
    # Only admins can remove roles
    if not any(role.name == "admin" for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    try:
        user = user_repository.remove_role_from_user(db, user_id, role_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    # Return user without password
    user_dict = user.to_dict()
    user_dict.pop("hashed_password", None)
    
    # Add roles
    user_dict["roles"] = [{"id": role.id, "name": role.name} for role in user.roles]
    
    return user_dict


@router.get("/roles/", response_model=List[Dict[str, Any]])
async def read_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all roles with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of roles
        
    Raises:
        HTTPException: If user doesn't have permission
    """
    # Check if user has permission to view roles
    if not any(role.name in ["admin", "manager"] for role in current_user.roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    roles = role_repository.get_multi(db, skip=skip, limit=limit)
    
    return [role.to_dict() for role in roles]
