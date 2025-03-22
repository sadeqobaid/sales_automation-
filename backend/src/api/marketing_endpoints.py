"""
Author Sadeq Obaid and Abdallah Obaid

Marketing campaign API endpoints for the Sales Automation System.
This module provides API endpoints for marketing campaign management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from src.auth.authentication import get_current_active_user
from src.models.user import User
from src.models.marketing import MarketingCampaign, CampaignActivity, CampaignMetric, CampaignStatus, CampaignType, MetricType
from src.repositories.marketing_repository import MarketingCampaignRepository, CampaignActivityRepository, CampaignMetricRepository
from src.utils.database_utils import get_db

# Create repositories
campaign_repository = MarketingCampaignRepository()
campaign_activity_repository = CampaignActivityRepository()
campaign_metric_repository = CampaignMetricRepository()

# Create router
router = APIRouter(
    prefix="/marketing",
    tags=["marketing"],
    responses={401: {"description": "Unauthorized"}},
)


@router.post("/campaigns", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_campaign(
    campaign_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new marketing campaign.
    
    Args:
        campaign_data: Campaign data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created campaign
        
    Raises:
        HTTPException: If validation fails
    """
    # Set created_by
    campaign_data["created_by"] = current_user.id
    
    # Set owner_id if not provided
    if "owner_id" not in campaign_data:
        campaign_data["owner_id"] = current_user.id
    
    # Create campaign
    campaign = campaign_repository.create(db, campaign_data)
    
    return campaign.to_dict()


@router.get("/campaigns", response_model=List[Dict[str, Any]])
async def read_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    campaign_type: Optional[str] = None,
    owner_id: Optional[int] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all marketing campaigns with pagination and optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        status: Optional status filter
        campaign_type: Optional campaign type filter
        owner_id: Optional owner ID filter
        search: Optional search term
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of campaigns
    """
    # Apply filters
    if status:
        try:
            status_enum = CampaignStatus(status)
            campaigns = campaign_repository.get_by_status(db, status_enum, skip=skip, limit=limit)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    elif campaign_type:
        try:
            type_enum = CampaignType(campaign_type)
            campaigns = campaign_repository.get_by_type(db, type_enum, skip=skip, limit=limit)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid campaign type: {campaign_type}"
            )
    elif owner_id:
        campaigns = campaign_repository.get_by_owner(db, owner_id, skip=skip, limit=limit)
    elif search:
        campaigns = campaign_repository.search(db, search, skip=skip, limit=limit)
    else:
        campaigns = campaign_repository.get_multi(db, skip=skip, limit=limit)
    
    return [campaign.to_dict() for campaign in campaigns]


@router.get("/campaigns/active", response_model=List[Dict[str, Any]])
async def read_active_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all active marketing campaigns with pagination.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of active campaigns
    """
    campaigns = campaign_repository.get_active_campaigns(db, skip=skip, limit=limit)
    
    return [campaign.to_dict() for campaign in campaigns]


@router.get("/campaigns/{campaign_id}", response_model=Dict[str, Any])
async def read_campaign(
    campaign_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get a specific marketing campaign by ID.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Campaign data
        
    Raises:
        HTTPException: If campaign not found
    """
    campaign = campaign_repository.get(db, campaign_id)
    
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    return campaign.to_dict()


@router.put("/campaigns/{campaign_id}", response_model=Dict[str, Any])
async def update_campaign(
    campaign_id: int = Path(..., gt=0),
    campaign_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Update a marketing campaign.
    
    Args:
        campaign_id: Campaign ID
        campaign_data: Campaign data to update
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated campaign
        
    Raises:
        HTTPException: If campaign not found
    """
    campaign = campaign_repository.get(db, campaign_id)
    
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Set updated_by
    campaign_data["updated_by"] = current_user.id
    
    # Update campaign
    updated_campaign = campaign_repository.update(db, db_obj=campaign, obj_in=campaign_data)
    
    return updated_campaign.to_dict()


@router.delete("/campaigns/{campaign_id}", response_model=Dict[str, Any])
async def delete_campaign(
    campaign_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Delete a marketing campaign.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Deleted campaign
        
    Raises:
        HTTPException: If campaign not found
    """
    campaign = campaign_repository.get(db, campaign_id)
    
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Delete campaign
    deleted_campaign = campaign_repository.delete(db, id=campaign_id)
    
    return deleted_campaign.to_dict()


@router.post("/campaigns/{campaign_id}/contacts/{contact_id}", response_model=Dict[str, Any])
async def add_contact_to_campaign(
    campaign_id: int = Path(..., gt=0),
    contact_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Add a contact to a marketing campaign.
    
    Args:
        campaign_id: Campaign ID
        contact_id: Contact ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated campaign
        
    Raises:
        HTTPException: If campaign or contact not found
    """
    try:
        campaign = campaign_repository.add_contact(db, campaign_id, contact_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return campaign.to_dict()


@router.delete("/campaigns/{campaign_id}/contacts/{contact_id}", response_model=Dict[str, Any])
async def remove_contact_from_campaign(
    campaign_id: int = Path(..., gt=0),
    contact_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Remove a contact from a marketing campaign.
    
    Args:
        campaign_id: Campaign ID
        contact_id: Contact ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Updated campaign
        
    Raises:
        HTTPException: If campaign or contact not found
    """
    try:
        campaign = campaign_repository.remove_contact(db, campaign_id, contact_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return campaign.to_dict()


@router.post("/campaigns/{campaign_id}/activities", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_campaign_activity(
    campaign_id: int = Path(..., gt=0),
    activity_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new activity for a marketing campaign.
    
    Args:
        campaign_id: Campaign ID
        activity_data: Activity data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created activity
        
    Raises:
        HTTPException: If campaign not found
    """
    campaign = campaign_repository.get(db, campaign_id)
    
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Set campaign_id and created_by
    activity_data["campaign_id"] = campaign_id
    activity_data["created_by"] = current_user.id
    
    # Create activity
    activity = campaign_activity_repository.create(db, activity_data)
    
    return activity.to_dict()


@router.get("/campaigns/{campaign_id}/activities", response_model=List[Dict[str, Any]])
async def read_campaign_activities(
    campaign_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all activities for a marketing campaign with pagination.
    
    Args:
        campaign_id: Campaign ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of activities
        
    Raises:
        HTTPException: If campaign not found
    """
    campaign = campaign_repository.get(db, campaign_id)
    
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    activities = campaign_activity_repository.get_by_campaign(db, campaign_id, skip=skip, limit=limit)
    
    return [activity.to_dict() for activity in activities]


@router.post("/campaigns/{campaign_id}/metrics", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_campaign_metric(
    campaign_id: int = Path(..., gt=0),
    metric_data: Dict[str, Any] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Create a new metric for a marketing campaign.
    
    Args:
        campaign_id: Campaign ID
        metric_data: Metric data
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Created metric
        
    Raises:
        HTTPException: If campaign not found
    """
    campaign = campaign_repository.get(db, campaign_id)
    
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    # Set campaign_id and created_by
    metric_data["campaign_id"] = campaign_id
    metric_data["created_by"] = current_user.id
    
    # Create metric
    metric = campaign_metric_repository.create(db, metric_data)
    
    return metric.to_dict()


@router.get("/campaigns/{campaign_id}/metrics", response_model=List[Dict[str, Any]])
async def read_campaign_metrics(
    campaign_id: int = Path(..., gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get all metrics for a marketing campaign with pagination.
    
    Args:
        campaign_id: Campaign ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List[Dict[str, Any]]: List of metrics
        
    Raises:
        HTTPException: If campaign not found
    """
    campaign = campaign_repository.get(db, campaign_id)
    
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    metrics = campaign_metric_repository.get_by_campaign(db, campaign_id, skip=skip, limit=limit)
    
    return [metric.to_dict() for metric in metrics]


@router.get("/campaigns/{campaign_id}/performance", response_model=Dict[str, Any])
async def get_campaign_performance(
    campaign_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get performance metrics for a marketing campaign.
    
    Args:
        campaign_id: Campaign ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Dict[str, Any]: Performance metrics
        
    Raises:
        HTTPException: If campaign not found
    """
    campaign = campaign_repository.get(db, campaign_id)
    
    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    try:
        performance = campaign_metric_repository.get_campaign_performance(db, campaign_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    
    return performance
