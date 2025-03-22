"""
Author Sadeq Obaid and Abdallah Obaid

Lead API endpoints for the Sales Automation System.
This module provides API endpoints for lead management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from src.auth.authentication import get_current_active_user
from src.models.user import User
from src.models.lead import Lead, LeadActivity, Opportunity, OpportunityActivity
from src.repositories.lead_repository import lead_repository, opportunity_repository
from src.utils.database_utils import get_db

# Create router
router = APIRouter(
    prefix="/leads",
    tags=["leads"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_lead(
    lead_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new lead.
    
    Args:
        lead_data: Lead data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created lead
        
    Raises:
        HTTPException: If validation fails
    """
    # Set created_by
    lead_data["created_by"] = current_user.id
    
    # Set owner_id if not provided
    if "owner_id" not in lead_data:
        lead_data["owner_id"] = current_user.id
    
    # Create lead
    lead = lead_repository.create(db, lead_data)
    
    # Create initial activity
    activity_data = {
        "lead_id": lead.id,
        "activity_type": "created",
        "description": "Lead created",
        "created_by": current_user.id
    }
    lead_repository.add_activity(db, activity_data)
    
    return lead.to_dict()


@router.get("/", response_model=List[Dict[str, Any]])
async def read_leads(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    owner_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all leads with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional status filter
        owner_id: Optional owner ID filter
        search: Optional search term
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of leads
    """
    # Apply filters
    if status:
        leads = lead_repository.get_by_status(db, status, skip=skip, limit=limit)
    elif owner_id:
        leads = lead_repository.get_by_owner(db, owner_id, skip=skip, limit=limit)
    elif search:
        leads = lead_repository.search(db, search, skip=skip, limit=limit)
    else:
        leads = lead_repository.get_multi(db, skip=skip, limit=limit)
    
    return [lead.to_dict() for lead in leads]


@router.get("/{lead_id}", response_model=Dict[str, Any])
async def read_lead(
    lead_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get a specific lead by ID.
    
    Args:
        lead_id: Lead ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Lead data
        
    Raises:
        HTTPException: If lead not found
    """
    lead = lead_repository.get(db, lead_id)
    
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return lead.to_dict()


@router.put("/{lead_id}", response_model=Dict[str, Any])
async def update_lead(
    lead_id: int = Path(..., gt=0),
    lead_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update a lead.
    
    Args:
        lead_id: Lead ID
        lead_data: Lead data to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated lead
        
    Raises:
        HTTPException: If lead not found
    """
    lead = lead_repository.get(db, lead_id)
    
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Set updated_by
    lead_data["updated_by"] = current_user.id
    
    # Check if status is changing
    old_status = lead.status
    new_status = lead_data.get("status", old_status)
    
    # Update lead
    updated_lead = lead_repository.update(db, db_obj=lead, obj_in=lead_data)
    
    # Create activity for status change
    if old_status != new_status:
        activity_data = {
            "lead_id": lead.id,
            "activity_type": "status_change",
            "description": f"Status changed from {old_status} to {new_status}",
            "created_by": current_user.id
        }
        lead_repository.add_activity(db, activity_data)
    
    return updated_lead.to_dict()


@router.delete("/{lead_id}", response_model=Dict[str, Any])
async def delete_lead(
    lead_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Delete a lead.
    
    Args:
        lead_id: Lead ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Deleted lead
        
    Raises:
        HTTPException: If lead not found
    """
    lead = lead_repository.get(db, lead_id)
    
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Delete lead
    deleted_lead = lead_repository.delete(db, id=lead_id)
    
    return deleted_lead.to_dict()


@router.post("/{lead_id}/activities", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_lead_activity(
    lead_id: int = Path(..., gt=0),
    activity_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new activity for a lead.
    
    Args:
        lead_id: Lead ID
        activity_data: Activity data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created activity
        
    Raises:
        HTTPException: If lead not found
    """
    lead = lead_repository.get(db, lead_id)
    
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    # Set lead_id and created_by
    activity_data["lead_id"] = lead_id
    activity_data["created_by"] = current_user.id
    
    # Create activity
    activity = lead_repository.add_activity(db, activity_data)
    
    return activity.to_dict()


@router.get("/{lead_id}/activities", response_model=List[Dict[str, Any]])
async def read_lead_activities(
    lead_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all activities for a lead with pagination.
    
    Args:
        lead_id: Lead ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of activities
        
    Raises:
        HTTPException: If lead not found
    """
    lead = lead_repository.get(db, lead_id)
    
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    activities = lead_repository.get_activities(db, lead_id, skip=skip, limit=limit)
    
    return [activity.to_dict() for activity in activities]


@router.post("/{lead_id}/convert", response_model=Dict[str, Any])
async def convert_lead_to_opportunity(
    lead_id: int = Path(..., gt=0),
    opportunity_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Convert a lead to an opportunity.
    
    Args:
        lead_id: Lead ID
        opportunity_data: Opportunity data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created opportunity
        
    Raises:
        HTTPException: If lead not found or already converted
    """
    lead = lead_repository.get(db, lead_id)
    
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    if lead.status == "converted":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead already converted"
        )
    
    # Set created_by
    opportunity_data["created_by"] = current_user.id
    
    # Set owner_id if not provided
    if "owner_id" not in opportunity_data:
        opportunity_data["owner_id"] = lead.owner_id
    
    # Convert lead
    try:
        opportunity = lead_repository.convert_to_opportunity(db, lead_id, opportunity_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return opportunity.to_dict()


# Opportunity endpoints
@router.get("/opportunities/", response_model=List[Dict[str, Any]])
async def read_opportunities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    owner_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all opportunities with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional status filter
        owner_id: Optional owner ID filter
        search: Optional search term
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of opportunities
    """
    # Apply filters
    if status:
        opportunities = opportunity_repository.get_by_status(db, status, skip=skip, limit=limit)
    elif owner_id:
        opportunities = opportunity_repository.get_by_owner(db, owner_id, skip=skip, limit=limit)
    elif search:
        opportunities = opportunity_repository.search(db, search, skip=skip, limit=limit)
    else:
        opportunities = opportunity_repository.get_multi(db, skip=skip, limit=limit)
    
    return [opportunity.to_dict() for opportunity in opportunities]


@router.get("/opportunities/{opportunity_id}", response_model=Dict[str, Any])
async def read_opportunity(
    opportunity_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get a specific opportunity by ID.
    
    Args:
        opportunity_id: Opportunity ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Opportunity data
        
    Raises:
        HTTPException: If opportunity not found
    """
    opportunity = opportunity_repository.get(db, opportunity_id)
    
    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    return opportunity.to_dict()


@router.put("/opportunities/{opportunity_id}", response_model=Dict[str, Any])
async def update_opportunity(
    opportunity_id: int = Path(..., gt=0),
    opportunity_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update an opportunity.
    
    Args:
        opportunity_id: Opportunity ID
        opportunity_data: Opportunity data to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated opportunity
        
    Raises:
        HTTPException: If opportunity not found
    """
    opportunity = opportunity_repository.get(db, opportunity_id)
    
    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    # Set updated_by
    opportunity_data["updated_by"] = current_user.id
    
    # Check if status is changing
    old_status = opportunity.status
    new_status = opportunity_data.get("status", old_status)
    
    # Update opportunity
    updated_opportunity = opportunity_repository.update(db, db_obj=opportunity, obj_in=opportunity_data)
    
    # Create activity for status change
    if old_status != new_status:
        activity_data = {
            "opportunity_id": opportunity.id,
            "activity_type": "status_change",
            "description": f"Status changed from {old_status} to {new_status}",
            "created_by": current_user.id
        }
        opportunity_repository.add_activity(db, activity_data)
    
    return updated_opportunity.to_dict()


@router.post("/opportunities/{opportunity_id}/activities", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_opportunity_activity(
    opportunity_id: int = Path(..., gt=0),
    activity_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new activity for an opportunity.
    
    Args:
        opportunity_id: Opportunity ID
        activity_data: Activity data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created activity
        
    Raises:
        HTTPException: If opportunity not found
    """
    opportunity = opportunity_repository.get(db, opportunity_id)
    
    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    # Set opportunity_id and created_by
    activity_data["opportunity_id"] = opportunity_id
    activity_data["created_by"] = current_user.id
    
    # Create activity
    activity = opportunity_repository.add_activity(db, activity_data)
    
    return activity.to_dict()


@router.get("/opportunities/{opportunity_id}/activities", response_model=List[Dict[str, Any]])
async def read_opportunity_activities(
    opportunity_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all activities for an opportunity with pagination.
    
    Args:
        opportunity_id: Opportunity ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of activities
        
    Raises:
        HTTPException: If opportunity not found
    """
    opportunity = opportunity_repository.get(db, opportunity_id)
    
    if opportunity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Opportunity not found"
        )
    
    activities = opportunity_repository.get_activities(db, opportunity_id, skip=skip, limit=limit)
    
    return [activity.to_dict() for activity in activities]
