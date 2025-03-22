"""
Author Sadeq Obaid and Abdallah Obaid

Lead model module for the Sales Automation System.
This module provides the lead management models and related functionality.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Date, Text, Float, Enum
from sqlalchemy.orm import relationship
import enum

from src.models.base import BaseModel
from src.models.contact import Contact
from config.database import Base


class LeadStatus(enum.Enum):
    """Enumeration of possible lead statuses."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"


class LeadSource(enum.Enum):
    """Enumeration of possible lead sources."""
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL_CAMPAIGN = "email_campaign"
    TRADE_SHOW = "trade_show"
    COLD_CALL = "cold_call"
    OTHER = "other"


class Lead(BaseModel):
    """
    Lead model for the Sales Automation System.
    
    This class represents a sales lead in the system.
    """
    __tablename__ = 'lead'
    
    # Basic lead information
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Lead status and classification
    status = Column(Enum(LeadStatus), default=LeadStatus.NEW, nullable=False)
    source = Column(Enum(LeadSource), nullable=True)
    source_details = Column(String(255), nullable=True)
    
    # Lead scoring and qualification
    score = Column(Integer, default=0, nullable=False)
    is_qualified = Column(Boolean, default=False, nullable=False)
    qualification_notes = Column(Text, nullable=True)
    
    # Lead value
    estimated_value = Column(Float, nullable=True)
    estimated_close_date = Column(Date, nullable=True)
    
    # Conversion tracking
    converted_to_opportunity = Column(Boolean, default=False, nullable=False)
    conversion_date = Column(Date, nullable=True)
    opportunity_id = Column(Integer, ForeignKey('opportunity.id'), nullable=True)
    
    # Relationships
    contact_id = Column(Integer, ForeignKey('contact.id'), nullable=False)
    contact = relationship("Contact")
    
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    owner = relationship("User", foreign_keys=[owner_id])
    
    activities = relationship("LeadActivity", back_populates="lead")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the Lead model."""
        return f"<Lead {self.title} - {self.status.value}>"


class LeadActivity(BaseModel):
    """
    LeadActivity model for the Sales Automation System.
    
    This class represents an activity related to a lead.
    """
    __tablename__ = 'lead_activity'
    
    lead_id = Column(Integer, ForeignKey('lead.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # call, email, meeting, note, etc.
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    outcome = Column(String(100), nullable=True)
    
    # Relationships
    lead = relationship("Lead", back_populates="activities")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the LeadActivity model."""
        return f"<LeadActivity {self.activity_type} for lead {self.lead_id}>"


class OpportunityStage(enum.Enum):
    """Enumeration of possible opportunity stages."""
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    NEEDS_ANALYSIS = "needs_analysis"
    VALUE_PROPOSITION = "value_proposition"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Opportunity(BaseModel):
    """
    Opportunity model for the Sales Automation System.
    
    This class represents a sales opportunity in the system.
    """
    __tablename__ = 'opportunity'
    
    # Basic opportunity information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Opportunity stage and status
    stage = Column(Enum(OpportunityStage), default=OpportunityStage.PROSPECTING, nullable=False)
    probability = Column(Integer, default=0, nullable=False)  # Probability of closing (0-100)
    
    # Financial information
    amount = Column(Float, nullable=True)
    expected_revenue = Column(Float, nullable=True)
    
    # Timeline
    close_date = Column(Date, nullable=True)
    
    # Outcome tracking
    is_closed = Column(Boolean, default=False, nullable=False)
    is_won = Column(Boolean, default=False, nullable=False)
    loss_reason = Column(String(255), nullable=True)
    
    # Relationships
    contact_id = Column(Integer, ForeignKey('contact.id'), nullable=False)
    contact = relationship("Contact")
    
    company_id = Column(Integer, ForeignKey('company.id'), nullable=True)
    company = relationship("Company")
    
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    owner = relationship("User", foreign_keys=[owner_id])
    
    activities = relationship("OpportunityActivity", back_populates="opportunity")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the Opportunity model."""
        return f"<Opportunity {self.name} - {self.stage.value}>"


class OpportunityActivity(BaseModel):
    """
    OpportunityActivity model for the Sales Automation System.
    
    This class represents an activity related to an opportunity.
    """
    __tablename__ = 'opportunity_activity'
    
    opportunity_id = Column(Integer, ForeignKey('opportunity.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # call, email, meeting, note, etc.
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    outcome = Column(String(100), nullable=True)
    
    # Relationships
    opportunity = relationship("Opportunity", back_populates="activities")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the OpportunityActivity model."""
        return f"<OpportunityActivity {self.activity_type} for opportunity {self.opportunity_id}>"
