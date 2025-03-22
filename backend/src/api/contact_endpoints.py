"""
Author Sadeq Obaid and Abdallah Obaid

Contact API endpoints for the Sales Automation System.
This module provides API endpoints for contact management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from src.auth.authentication import get_current_active_user
from src.models.user import User
from src.models.contact import Contact, Company, Tag
from src.repositories.contact_repository import contact_repository, company_repository, tag_repository
from src.utils.database_utils import get_db

# Create router
router = APIRouter(
    prefix="/contacts",
    tags=["contacts"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_contact(
    contact_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new contact.
    
    Args:
        contact_data: Contact data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created contact
        
    Raises:
        HTTPException: If validation fails
    """
    # Set created_by
    contact_data["created_by"] = current_user.id
    
    # Create contact
    contact = contact_repository.create(db, contact_data)
    
    return contact.to_dict()


@router.get("/", response_model=List[Dict[str, Any]])
async def read_contacts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all contacts with pagination and optional search.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search term
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of contacts
    """
    if search:
        contacts = contact_repository.search(db, search, skip=skip, limit=limit)
    else:
        contacts = contact_repository.get_multi(db, skip=skip, limit=limit)
    
    return [contact.to_dict() for contact in contacts]


@router.get("/{contact_id}", response_model=Dict[str, Any])
async def read_contact(
    contact_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get a specific contact by ID.
    
    Args:
        contact_id: Contact ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Contact data
        
    Raises:
        HTTPException: If contact not found
    """
    contact = contact_repository.get(db, contact_id)
    
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    return contact.to_dict()


@router.put("/{contact_id}", response_model=Dict[str, Any])
async def update_contact(
    contact_id: int = Path(..., gt=0),
    contact_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update a contact.
    
    Args:
        contact_id: Contact ID
        contact_data: Contact data to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated contact
        
    Raises:
        HTTPException: If contact not found
    """
    contact = contact_repository.get(db, contact_id)
    
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Set updated_by
    contact_data["updated_by"] = current_user.id
    
    # Update contact
    updated_contact = contact_repository.update(db, db_obj=contact, obj_in=contact_data)
    
    return updated_contact.to_dict()


@router.delete("/{contact_id}", response_model=Dict[str, Any])
async def delete_contact(
    contact_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Delete a contact.
    
    Args:
        contact_id: Contact ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Deleted contact
        
    Raises:
        HTTPException: If contact not found
    """
    contact = contact_repository.get(db, contact_id)
    
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact not found"
        )
    
    # Delete contact
    deleted_contact = contact_repository.delete(db, id=contact_id)
    
    return deleted_contact.to_dict()


@router.post("/{contact_id}/tags/{tag_id}", response_model=Dict[str, Any])
async def add_tag_to_contact(
    contact_id: int = Path(..., gt=0),
    tag_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Add a tag to a contact.
    
    Args:
        contact_id: Contact ID
        tag_id: Tag ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated contact
        
    Raises:
        HTTPException: If contact or tag not found
    """
    try:
        contact = contact_repository.add_tag_to_contact(db, contact_id, tag_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return contact.to_dict()


@router.delete("/{contact_id}/tags/{tag_id}", response_model=Dict[str, Any])
async def remove_tag_from_contact(
    contact_id: int = Path(..., gt=0),
    tag_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Remove a tag from a contact.
    
    Args:
        contact_id: Contact ID
        tag_id: Tag ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated contact
        
    Raises:
        HTTPException: If contact or tag not found
    """
    try:
        contact = contact_repository.remove_tag_from_contact(db, contact_id, tag_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return contact.to_dict()


# Company endpoints
@router.post("/companies/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new company.
    
    Args:
        company_data: Company data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created company
        
    Raises:
        HTTPException: If validation fails
    """
    # Set created_by
    company_data["created_by"] = current_user.id
    
    # Create company
    company = company_repository.create(db, company_data)
    
    return company.to_dict()


@router.get("/companies/", response_model=List[Dict[str, Any]])
async def read_companies(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all companies with pagination and optional search.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search term
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of companies
    """
    if search:
        companies = company_repository.search(db, search, skip=skip, limit=limit)
    else:
        companies = company_repository.get_multi(db, skip=skip, limit=limit)
    
    return [company.to_dict() for company in companies]


@router.get("/companies/{company_id}", response_model=Dict[str, Any])
async def read_company(
    company_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get a specific company by ID.
    
    Args:
        company_id: Company ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Company data
        
    Raises:
        HTTPException: If company not found
    """
    company = company_repository.get(db, company_id)
    
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return company.to_dict()


@router.put("/companies/{company_id}", response_model=Dict[str, Any])
async def update_company(
    company_id: int = Path(..., gt=0),
    company_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update a company.
    
    Args:
        company_id: Company ID
        company_data: Company data to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated company
        
    Raises:
        HTTPException: If company not found
    """
    company = company_repository.get(db, company_id)
    
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Set updated_by
    company_data["updated_by"] = current_user.id
    
    # Update company
    updated_company = company_repository.update(db, db_obj=company, obj_in=company_data)
    
    return updated_company.to_dict()


@router.delete("/companies/{company_id}", response_model=Dict[str, Any])
async def delete_company(
    company_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Delete a company.
    
    Args:
        company_id: Company ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Deleted company
        
    Raises:
        HTTPException: If company not found
    """
    company = company_repository.get(db, company_id)
    
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Delete company
    deleted_company = company_repository.delete(db, id=company_id)
    
    return deleted_company.to_dict()


# Tag endpoints
@router.post("/tags/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new tag.
    
    Args:
        tag_data: Tag data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created tag
        
    Raises:
        HTTPException: If validation fails
    """
    # Set created_by
    tag_data["created_by"] = current_user.id
    
    # Create tag
    tag = tag_repository.create(db, tag_data)
    
    return tag.to_dict()


@router.get("/tags/", response_model=List[Dict[str, Any]])
async def read_tags(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all tags with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of tags
    """
    tags = tag_repository.get_multi(db, skip=skip, limit=limit)
    
    return [tag.to_dict() for tag in tags]
