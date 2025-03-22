"""
Author Sadeq Obaid and Abdallah Obaid

Marketing campaign model module for the Sales Automation System.
This module provides the marketing campaign models and related functionality.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Date, Text, Float, Enum, Table, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime

from src.models.base import BaseModel
from src.models.contact import Contact
from config.database import Base


# Many-to-many relationship between campaigns and contacts
campaign_contacts = Table(
    'campaign_contacts',
    Base.metadata,
    Column('campaign_id', Integer, ForeignKey('marketing_campaign.id'), primary_key=True),
    Column('contact_id', Integer, ForeignKey('contact.id'), primary_key=True)
)


class CampaignType(enum.Enum):
    """Enumeration of possible campaign types."""
    EMAIL = "email"
    SOCIAL_MEDIA = "social_media"
    EVENT = "event"
    WEBINAR = "webinar"
    DIRECT_MAIL = "direct_mail"
    PHONE = "phone"
    OTHER = "other"


class CampaignStatus(enum.Enum):
    """Enumeration of possible campaign statuses."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MarketingCampaign(BaseModel):
    """
    MarketingCampaign model for the Sales Automation System.
    
    This class represents a marketing campaign in the system.
    """
    __tablename__ = 'marketing_campaign'
    
    # Basic campaign information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    campaign_type = Column(Enum(CampaignType), nullable=False)
    status = Column(Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False)
    
    # Campaign timing
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Campaign metrics
    budget = Column(Float, nullable=True)
    expected_revenue = Column(Float, nullable=True)
    actual_cost = Column(Float, nullable=True)
    actual_revenue = Column(Float, nullable=True)
    roi = Column(Float, nullable=True)
    
    # Campaign content
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    template_id = Column(String(100), nullable=True)
    
    # Campaign tracking
    utm_source = Column(String(100), nullable=True)
    utm_medium = Column(String(100), nullable=True)
    utm_campaign = Column(String(100), nullable=True)
    
    # Relationships
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    owner = relationship("User", foreign_keys=[owner_id])
    
    contacts = relationship("Contact", secondary=campaign_contacts, backref="campaigns")
    activities = relationship("CampaignActivity", back_populates="campaign")
    metrics = relationship("CampaignMetric", back_populates="campaign")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the MarketingCampaign model."""
        return f"<MarketingCampaign {self.name} - {self.status.value}>"
    
    @property
    def is_active(self) -> bool:
        """Check if the campaign is currently active."""
        if self.status != CampaignStatus.ACTIVE:
            return False
        
        today = datetime.now().date()
        if self.start_date and self.start_date > today:
            return False
        
        if self.end_date and self.end_date < today:
            return False
        
        return True
    
    def calculate_roi(self) -> float:
        """Calculate the ROI for the campaign."""
        if not self.actual_cost or self.actual_cost == 0:
            return 0
        
        if not self.actual_revenue:
            return 0
        
        return (self.actual_revenue - self.actual_cost) / self.actual_cost * 100


class CampaignActivity(BaseModel):
    """
    CampaignActivity model for the Sales Automation System.
    
    This class represents an activity related to a marketing campaign.
    """
    __tablename__ = 'campaign_activity'
    
    campaign_id = Column(Integer, ForeignKey('marketing_campaign.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # send, open, click, bounce, etc.
    description = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.now, nullable=False)
    
    # For email campaigns
    contact_id = Column(Integer, ForeignKey('contact.id'), nullable=True)
    email = Column(String(100), nullable=True)
    subject = Column(String(255), nullable=True)
    
    # For tracking
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    link_clicked = Column(String(255), nullable=True)
    
    # Relationships
    campaign = relationship("MarketingCampaign", back_populates="activities")
    contact = relationship("Contact")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the CampaignActivity model."""
        return f"<CampaignActivity {self.activity_type} for campaign {self.campaign_id}>"


class MetricType(enum.Enum):
    """Enumeration of possible metric types."""
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    UNSUBSCRIBED = "unsubscribed"
    CONVERTED = "converted"
    REVENUE = "revenue"
    COST = "cost"
    ROI = "roi"
    OTHER = "other"


class CampaignMetric(BaseModel):
    """
    CampaignMetric model for the Sales Automation System.
    
    This class represents a metric for a marketing campaign.
    """
    __tablename__ = 'campaign_metric'
    
    campaign_id = Column(Integer, ForeignKey('marketing_campaign.id'), nullable=False)
    metric_type = Column(Enum(MetricType), nullable=False)
    value = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    
    # Relationships
    campaign = relationship("MarketingCampaign", back_populates="metrics")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the CampaignMetric model."""
        return f"<CampaignMetric {self.metric_type.value}:{self.value} for campaign {self.campaign_id}>"
