"""
Author Sadeq Obaid and Abdallah Obaid

Contact model module for the Sales Automation System.
This module provides the contact management models and related functionality.
"""

from sqlalchemy import Column, String, Integer, ForeignKey, Boolean, Date, Text, Table
from sqlalchemy.orm import relationship

from src.models.base import BaseModel
from src.models.user import User
from config.database import Base

# Many-to-many relationship between contacts and tags
contact_tags = Table(
    'contact_tags',
    Base.metadata,
    Column('contact_id', Integer, ForeignKey('contact.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tag.id'), primary_key=True)
)

class Contact(BaseModel):
    """
    Contact model for the Sales Automation System.
    
    This class represents a contact in the system.
    """
    __tablename__ = 'contact'
    
    # Basic contact information
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=True)
    email = Column(String(100), index=True, nullable=True)
    phone = Column(String(20), nullable=True)
    mobile = Column(String(20), nullable=True)
    
    # Company information
    company_name = Column(String(100), nullable=True)
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Social media
    linkedin = Column(String(255), nullable=True)
    twitter = Column(String(255), nullable=True)
    facebook = Column(String(255), nullable=True)
    
    # Contact preferences
    preferred_contact_method = Column(String(20), nullable=True)  # email, phone, etc.
    do_not_contact = Column(Boolean, default=False, nullable=False)
    do_not_email = Column(Boolean, default=False, nullable=False)
    do_not_call = Column(Boolean, default=False, nullable=False)
    
    # Additional information
    notes = Column(Text, nullable=True)
    source = Column(String(100), nullable=True)  # Where the contact came from
    
    # Relationships
    owner_id = Column(Integer, ForeignKey('user.id'), nullable=True)
    owner = relationship("User", foreign_keys=[owner_id])
    
    company_id = Column(Integer, ForeignKey('company.id'), nullable=True)
    company = relationship("Company", back_populates="contacts")
    
    tags = relationship("Tag", secondary=contact_tags, back_populates="contacts")
    activities = relationship("ContactActivity", back_populates="contact")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the Contact model."""
        return f"<Contact {self.first_name} {self.last_name}>"
    
    @property
    def full_name(self) -> str:
        """Get the contact's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return "Unnamed Contact"


class Company(BaseModel):
    """
    Company model for the Sales Automation System.
    
    This class represents a company in the system.
    """
    __tablename__ = 'company'
    
    # Basic company information
    name = Column(String(100), nullable=False, index=True)
    website = Column(String(255), nullable=True)
    industry = Column(String(100), nullable=True)
    size = Column(String(50), nullable=True)  # Small, Medium, Large, Enterprise
    annual_revenue = Column(String(50), nullable=True)
    
    # Address information
    address_line1 = Column(String(255), nullable=True)
    address_line2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    
    # Additional information
    description = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    contacts = relationship("Contact", back_populates="company")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the Company model."""
        return f"<Company {self.name}>"


class Tag(BaseModel):
    """
    Tag model for the Sales Automation System.
    
    This class represents a tag for categorizing contacts.
    """
    __tablename__ = 'tag'
    
    name = Column(String(50), nullable=False, unique=True)
    color = Column(String(7), nullable=True)  # Hex color code
    description = Column(String(255), nullable=True)
    
    # Relationships
    contacts = relationship("Contact", secondary=contact_tags, back_populates="tags")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the Tag model."""
        return f"<Tag {self.name}>"


class ContactActivity(BaseModel):
    """
    ContactActivity model for the Sales Automation System.
    
    This class represents an activity related to a contact.
    """
    __tablename__ = 'contact_activity'
    
    contact_id = Column(Integer, ForeignKey('contact.id'), nullable=False)
    activity_type = Column(String(50), nullable=False)  # call, email, meeting, note, etc.
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(Date, nullable=False)
    duration = Column(Integer, nullable=True)  # Duration in minutes
    outcome = Column(String(100), nullable=True)
    
    # Relationships
    contact = relationship("Contact", back_populates="activities")
    
    # Audit information
    created_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    updated_by = Column(Integer, ForeignKey('user.id'), nullable=True)
    
    def __repr__(self) -> str:
        """String representation of the ContactActivity model."""
        return f"<ContactActivity {self.activity_type} for contact {self.contact_id}>"
