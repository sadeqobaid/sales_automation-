"""
Author Sadeq Obaid and Abdallah Obaid

Repository module for marketing campaign models in the Sales Automation System.
This module provides repository classes for marketing-related models.
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date

from src.repositories.base import BaseRepository
from src.models.marketing import MarketingCampaign, CampaignActivity, CampaignMetric, CampaignStatus, CampaignType, MetricType


class MarketingCampaignRepository(BaseRepository[MarketingCampaign]):
    """Repository for MarketingCampaign model operations."""
    
    def __init__(self):
        super().__init__(MarketingCampaign)
    
    def get_by_status(self, db: Session, status: CampaignStatus, skip: int = 0, limit: int = 100) -> List[MarketingCampaign]:
        """
        Get campaigns by status.
        
        Args:
            db: Database session
            status: Campaign status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MarketingCampaign]: List of campaigns
        """
        return db.query(MarketingCampaign).filter(MarketingCampaign.status == status).offset(skip).limit(limit).all()
    
    def get_by_type(self, db: Session, campaign_type: CampaignType, skip: int = 0, limit: int = 100) -> List[MarketingCampaign]:
        """
        Get campaigns by type.
        
        Args:
            db: Database session
            campaign_type: Campaign type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MarketingCampaign]: List of campaigns
        """
        return db.query(MarketingCampaign).filter(MarketingCampaign.campaign_type == campaign_type).offset(skip).limit(limit).all()
    
    def get_active_campaigns(self, db: Session, skip: int = 0, limit: int = 100) -> List[MarketingCampaign]:
        """
        Get active campaigns.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MarketingCampaign]: List of active campaigns
        """
        today = date.today()
        return db.query(MarketingCampaign).filter(
            MarketingCampaign.status == CampaignStatus.ACTIVE,
            (MarketingCampaign.start_date <= today) | (MarketingCampaign.start_date == None),
            (MarketingCampaign.end_date >= today) | (MarketingCampaign.end_date == None)
        ).offset(skip).limit(limit).all()
    
    def get_by_owner(self, db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[MarketingCampaign]:
        """
        Get campaigns owned by a specific user.
        
        Args:
            db: Database session
            owner_id: Owner user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MarketingCampaign]: List of campaigns
        """
        return db.query(MarketingCampaign).filter(MarketingCampaign.owner_id == owner_id).offset(skip).limit(limit).all()
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 100) -> List[MarketingCampaign]:
        """
        Search campaigns by name or description.
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[MarketingCampaign]: List of matching campaigns
        """
        search_term = f"%{query}%"
        return db.query(MarketingCampaign).filter(
            or_(
                MarketingCampaign.name.ilike(search_term),
                MarketingCampaign.description.ilike(search_term)
            )
        ).offset(skip).limit(limit).all()
    
    def add_contact(self, db: Session, campaign_id: int, contact_id: int) -> MarketingCampaign:
        """
        Add a contact to a campaign.
        
        Args:
            db: Database session
            campaign_id: Campaign ID
            contact_id: Contact ID
            
        Returns:
            MarketingCampaign: Updated campaign
        """
        campaign = self.get(db, campaign_id)
        contact = db.query(Contact).get(contact_id)
        
        if campaign is None or contact is None:
            raise ValueError(f"Campaign with id {campaign_id} or Contact with id {contact_id} not found")
        
        campaign.contacts.append(contact)
        db.commit()
        db.refresh(campaign)
        return campaign
    
    def remove_contact(self, db: Session, campaign_id: int, contact_id: int) -> MarketingCampaign:
        """
        Remove a contact from a campaign.
        
        Args:
            db: Database session
            campaign_id: Campaign ID
            contact_id: Contact ID
            
        Returns:
            MarketingCampaign: Updated campaign
        """
        campaign = self.get(db, campaign_id)
        contact = db.query(Contact).get(contact_id)
        
        if campaign is None or contact is None:
            raise ValueError(f"Campaign with id {campaign_id} or Contact with id {contact_id} not found")
        
        campaign.contacts.remove(contact)
        db.commit()
        db.refresh(campaign)
        return campaign


class CampaignActivityRepository(BaseRepository[CampaignActivity]):
    """Repository for CampaignActivity model operations."""
    
    def __init__(self):
        super().__init__(CampaignActivity)
    
    def get_by_campaign(self, db: Session, campaign_id: int, skip: int = 0, limit: int = 100) -> List[CampaignActivity]:
        """
        Get activities for a specific campaign.
        
        Args:
            db: Database session
            campaign_id: Campaign ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[CampaignActivity]: List of campaign activities
        """
        return db.query(CampaignActivity).filter(
            CampaignActivity.campaign_id == campaign_id
        ).order_by(CampaignActivity.timestamp.desc()).offset(skip).limit(limit).all()
    
    def get_by_contact(self, db: Session, contact_id: int, skip: int = 0, limit: int = 100) -> List[CampaignActivity]:
        """
        Get activities for a specific contact.
        
        Args:
            db: Database session
            contact_id: Contact ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[CampaignActivity]: List of campaign activities
        """
        return db.query(CampaignActivity).filter(
            CampaignActivity.contact_id == contact_id
        ).order_by(CampaignActivity.timestamp.desc()).offset(skip).limit(limit).all()
    
    def get_by_activity_type(self, db: Session, activity_type: str, skip: int = 0, limit: int = 100) -> List[CampaignActivity]:
        """
        Get activities by type.
        
        Args:
            db: Database session
            activity_type: Activity type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[CampaignActivity]: List of campaign activities
        """
        return db.query(CampaignActivity).filter(
            CampaignActivity.activity_type == activity_type
        ).order_by(CampaignActivity.timestamp.desc()).offset(skip).limit(limit).all()


class CampaignMetricRepository(BaseRepository[CampaignMetric]):
    """Repository for CampaignMetric model operations."""
    
    def __init__(self):
        super().__init__(CampaignMetric)
    
    def get_by_campaign(self, db: Session, campaign_id: int, skip: int = 0, limit: int = 100) -> List[CampaignMetric]:
        """
        Get metrics for a specific campaign.
        
        Args:
            db: Database session
            campaign_id: Campaign ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[CampaignMetric]: List of campaign metrics
        """
        return db.query(CampaignMetric).filter(
            CampaignMetric.campaign_id == campaign_id
        ).order_by(CampaignMetric.date.desc()).offset(skip).limit(limit).all()
    
    def get_by_metric_type(self, db: Session, metric_type: MetricType, skip: int = 0, limit: int = 100) -> List[CampaignMetric]:
        """
        Get metrics by type.
        
        Args:
            db: Database session
            metric_type: Metric type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[CampaignMetric]: List of campaign metrics
        """
        return db.query(CampaignMetric).filter(
            CampaignMetric.metric_type == metric_type
        ).order_by(CampaignMetric.date.desc()).offset(skip).limit(limit).all()
    
    def get_campaign_performance(self, db: Session, campaign_id: int) -> Dict[str, Any]:
        """
        Get performance metrics for a campaign.
        
        Args:
            db: Database session
            campaign_id: Campaign ID
            
        Returns:
            Dict[str, Any]: Dictionary with performance metrics
        """
        campaign = db.query(MarketingCampaign).get(campaign_id)
        if campaign is None:
            raise ValueError(f"Campaign with id {campaign_id} not found")
        
        metrics = self.get_by_campaign(db, campaign_id)
        
        # Group metrics by type
        performance = {}
        for metric in metrics:
            metric_type = metric.metric_type.value
            if metric_type not in performance:
                performance[metric_type] = 0
            performance[metric_type] += metric.value
        
        # Add calculated metrics
        if 'sent' in performance and performance['sent'] > 0:
            if 'delivered' in performance:
                performance['delivery_rate'] = performance['delivered'] / performance['sent'] * 100
            if 'opened' in performance:
                performance['open_rate'] = performance['opened'] / performance['sent'] * 100
            if 'clicked' in performance:
                performance['click_rate'] = performance['clicked'] / performance['sent'] * 100
            if 'converted' in performance:
                performance['conversion_rate'] = performance['converted'] / performance['sent'] * 100
        
        # Add ROI if available
        if 'revenue' in performance and 'cost' in performance and performance['cost'] > 0:
            performance['roi'] = (performance['revenue'] - performance['cost']) / performance['cost'] * 100
        
        return performance
