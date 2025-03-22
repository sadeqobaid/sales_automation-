"""
Author Sadeq Obaid and Abdallah Obaid

Lead repository module for the Sales Automation System.
This module provides repository classes for lead-related models.
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import date

from src.repositories.base import BaseRepository
from src.models.lead import Lead, LeadActivity, Opportunity, OpportunityActivity, LeadStatus, OpportunityStage


class LeadRepository(BaseRepository[Lead]):
    """Repository for Lead model operations."""
    
    def __init__(self):
        super().__init__(Lead)
    
    def get_by_contact(self, db: Session, contact_id: int, skip: int = 0, limit: int = 100) -> List[Lead]:
        """
        Get leads for a specific contact.
        
        Args:
            db: Database session
            contact_id: Contact ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Lead]: List of leads
        """
        return db.query(Lead).filter(Lead.contact_id == contact_id).offset(skip).limit(limit).all()
    
    def get_by_owner(self, db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Lead]:
        """
        Get leads owned by a specific user.
        
        Args:
            db: Database session
            owner_id: Owner user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Lead]: List of leads
        """
        return db.query(Lead).filter(Lead.owner_id == owner_id).offset(skip).limit(limit).all()
    
    def get_by_status(self, db: Session, status: LeadStatus, skip: int = 0, limit: int = 100) -> List[Lead]:
        """
        Get leads by status.
        
        Args:
            db: Database session
            status: Lead status
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Lead]: List of leads
        """
        return db.query(Lead).filter(Lead.status == status).offset(skip).limit(limit).all()
    
    def get_by_source(self, db: Session, source: str, skip: int = 0, limit: int = 100) -> List[Lead]:
        """
        Get leads by source.
        
        Args:
            db: Database session
            source: Lead source
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Lead]: List of leads
        """
        return db.query(Lead).filter(Lead.source == source).offset(skip).limit(limit).all()
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Lead]:
        """
        Search leads by title or description.
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Lead]: List of matching leads
        """
        search_term = f"%{query}%"
        return db.query(Lead).filter(
            or_(
                Lead.title.ilike(search_term),
                Lead.description.ilike(search_term)
            )
        ).offset(skip).limit(limit).all()
    
    def convert_to_opportunity(self, db: Session, lead_id: int, opportunity_data: Dict[str, Any]) -> Opportunity:
        """
        Convert a lead to an opportunity.
        
        Args:
            db: Database session
            lead_id: Lead ID
            opportunity_data: Opportunity data
            
        Returns:
            Opportunity: Created opportunity
        """
        lead = self.get(db, lead_id)
        if lead is None:
            raise ValueError(f"Lead with id {lead_id} not found")
        
        # Create opportunity
        opportunity = Opportunity(
            name=opportunity_data.get("name", lead.title),
            description=opportunity_data.get("description", lead.description),
            contact_id=lead.contact_id,
            owner_id=lead.owner_id,
            amount=opportunity_data.get("amount"),
            expected_revenue=opportunity_data.get("expected_revenue"),
            close_date=opportunity_data.get("close_date"),
            stage=opportunity_data.get("stage", OpportunityStage.PROSPECTING),
            created_by=lead.created_by,
            updated_by=lead.updated_by
        )
        
        db.add(opportunity)
        
        # Update lead
        lead.converted_to_opportunity = True
        lead.conversion_date = date.today()
        lead.opportunity_id = opportunity.id
        lead.status = LeadStatus.CONVERTED
        
        db.commit()
        db.refresh(opportunity)
        db.refresh(lead)
        
        return opportunity


class LeadActivityRepository(BaseRepository[LeadActivity]):
    """Repository for LeadActivity model operations."""
    
    def __init__(self):
        super().__init__(LeadActivity)
    
    def get_by_lead(self, db: Session, lead_id: int, skip: int = 0, limit: int = 100) -> List[LeadActivity]:
        """
        Get activities for a specific lead.
        
        Args:
            db: Database session
            lead_id: Lead ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[LeadActivity]: List of lead activities
        """
        return db.query(LeadActivity).filter(
            LeadActivity.lead_id == lead_id
        ).order_by(LeadActivity.date.desc()).offset(skip).limit(limit).all()
    
    def get_by_activity_type(self, db: Session, activity_type: str, skip: int = 0, limit: int = 100) -> List[LeadActivity]:
        """
        Get activities by type.
        
        Args:
            db: Database session
            activity_type: Activity type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[LeadActivity]: List of lead activities
        """
        return db.query(LeadActivity).filter(
            LeadActivity.activity_type == activity_type
        ).order_by(LeadActivity.date.desc()).offset(skip).limit(limit).all()


class OpportunityRepository(BaseRepository[Opportunity]):
    """Repository for Opportunity model operations."""
    
    def __init__(self):
        super().__init__(Opportunity)
    
    def get_by_contact(self, db: Session, contact_id: int, skip: int = 0, limit: int = 100) -> List[Opportunity]:
        """
        Get opportunities for a specific contact.
        
        Args:
            db: Database session
            contact_id: Contact ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Opportunity]: List of opportunities
        """
        return db.query(Opportunity).filter(Opportunity.contact_id == contact_id).offset(skip).limit(limit).all()
    
    def get_by_company(self, db: Session, company_id: int, skip: int = 0, limit: int = 100) -> List[Opportunity]:
        """
        Get opportunities for a specific company.
        
        Args:
            db: Database session
            company_id: Company ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Opportunity]: List of opportunities
        """
        return db.query(Opportunity).filter(Opportunity.company_id == company_id).offset(skip).limit(limit).all()
    
    def get_by_owner(self, db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Opportunity]:
        """
        Get opportunities owned by a specific user.
        
        Args:
            db: Database session
            owner_id: Owner user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Opportunity]: List of opportunities
        """
        return db.query(Opportunity).filter(Opportunity.owner_id == owner_id).offset(skip).limit(limit).all()
    
    def get_by_stage(self, db: Session, stage: OpportunityStage, skip: int = 0, limit: int = 100) -> List[Opportunity]:
        """
        Get opportunities by stage.
        
        Args:
            db: Database session
            stage: Opportunity stage
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Opportunity]: List of opportunities
        """
        return db.query(Opportunity).filter(Opportunity.stage == stage).offset(skip).limit(limit).all()
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Opportunity]:
        """
        Search opportunities by name or description.
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Opportunity]: List of matching opportunities
        """
        search_term = f"%{query}%"
        return db.query(Opportunity).filter(
            or_(
                Opportunity.name.ilike(search_term),
                Opportunity.description.ilike(search_term)
            )
        ).offset(skip).limit(limit).all()
    
    def close_won(self, db: Session, opportunity_id: int, close_details: Dict[str, Any] = None) -> Opportunity:
        """
        Close an opportunity as won.
        
        Args:
            db: Database session
            opportunity_id: Opportunity ID
            close_details: Optional details about the close
            
        Returns:
            Opportunity: Updated opportunity
        """
        opportunity = self.get(db, opportunity_id)
        if opportunity is None:
            raise ValueError(f"Opportunity with id {opportunity_id} not found")
        
        opportunity.is_closed = True
        opportunity.is_won = True
        opportunity.stage = OpportunityStage.CLOSED_WON
        
        if close_details:
            if "amount" in close_details:
                opportunity.amount = close_details["amount"]
            if "close_date" in close_details:
                opportunity.close_date = close_details["close_date"]
        
        db.commit()
        db.refresh(opportunity)
        return opportunity
    
    def close_lost(self, db: Session, opportunity_id: int, loss_reason: str = None) -> Opportunity:
        """
        Close an opportunity as lost.
        
        Args:
            db: Database session
            opportunity_id: Opportunity ID
            loss_reason: Reason for loss
            
        Returns:
            Opportunity: Updated opportunity
        """
        opportunity = self.get(db, opportunity_id)
        if opportunity is None:
            raise ValueError(f"Opportunity with id {opportunity_id} not found")
        
        opportunity.is_closed = True
        opportunity.is_won = False
        opportunity.stage = OpportunityStage.CLOSED_LOST
        
        if loss_reason:
            opportunity.loss_reason = loss_reason
        
        db.commit()
        db.refresh(opportunity)
        return opportunity


class OpportunityActivityRepository(BaseRepository[OpportunityActivity]):
    """Repository for OpportunityActivity model operations."""
    
    def __init__(self):
        super().__init__(OpportunityActivity)
    
    def get_by_opportunity(self, db: Session, opportunity_id: int, skip: int = 0, limit: int = 100) -> List[OpportunityActivity]:
        """
        Get activities for a specific opportunity.
        
        Args:
            db: Database session
            opportunity_id: Opportunity ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[OpportunityActivity]: List of opportunity activities
        """
        return db.query(OpportunityActivity).filter(
            OpportunityActivity.opportunity_id == opportunity_id
        ).order_by(OpportunityActivity.date.desc()).offset(skip).limit(limit).all()
    
    def get_by_activity_type(self, db: Session, activity_type: str, skip: int = 0, limit: int = 100) -> List[OpportunityActivity]:
        """
        Get activities by type.
        
        Args:
            db: Database session
            activity_type: Activity type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[OpportunityActivity]: List of opportunity activities
        """
        return db.query(OpportunityActivity).filter(
            OpportunityActivity.activity_type == activity_type
        ).order_by(OpportunityActivity.date.desc()).offset(skip).limit(limit).all()
