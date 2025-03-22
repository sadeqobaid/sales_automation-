"""
Author Sadeq Obaid and Abdallah Obaid

Contact repository module for the Sales Automation System.
This module provides repository classes for contact-related models.
"""

from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.repositories.base import BaseRepository
from src.models.contact import Contact, Company, Tag, ContactActivity


class ContactRepository(BaseRepository[Contact]):
    """Repository for Contact model operations."""
    
    def __init__(self):
        super().__init__(Contact)
    
    def get_by_email(self, db: Session, email: str) -> Optional[Contact]:
        """
        Get a contact by email.
        
        Args:
            db: Database session
            email: Contact email
            
        Returns:
            Optional[Contact]: Found contact or None
        """
        return db.query(Contact).filter(Contact.email == email).first()
    
    def get_by_company(self, db: Session, company_id: int, skip: int = 0, limit: int = 100) -> List[Contact]:
        """
        Get contacts for a specific company.
        
        Args:
            db: Database session
            company_id: Company ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Contact]: List of contacts
        """
        return db.query(Contact).filter(Contact.company_id == company_id).offset(skip).limit(limit).all()
    
    def get_by_owner(self, db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Contact]:
        """
        Get contacts owned by a specific user.
        
        Args:
            db: Database session
            owner_id: Owner user ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Contact]: List of contacts
        """
        return db.query(Contact).filter(Contact.owner_id == owner_id).offset(skip).limit(limit).all()
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Contact]:
        """
        Search contacts by name, email, or company name.
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Contact]: List of matching contacts
        """
        search_term = f"%{query}%"
        return db.query(Contact).filter(
            or_(
                Contact.first_name.ilike(search_term),
                Contact.last_name.ilike(search_term),
                Contact.email.ilike(search_term),
                Contact.company_name.ilike(search_term)
            )
        ).offset(skip).limit(limit).all()
    
    def add_tag(self, db: Session, contact_id: int, tag_id: int) -> Contact:
        """
        Add a tag to a contact.
        
        Args:
            db: Database session
            contact_id: Contact ID
            tag_id: Tag ID
            
        Returns:
            Contact: Updated contact
        """
        contact = self.get(db, contact_id)
        tag = db.query(Tag).get(tag_id)
        
        if contact is None or tag is None:
            raise ValueError(f"Contact with id {contact_id} or Tag with id {tag_id} not found")
        
        contact.tags.append(tag)
        db.commit()
        db.refresh(contact)
        return contact
    
    def remove_tag(self, db: Session, contact_id: int, tag_id: int) -> Contact:
        """
        Remove a tag from a contact.
        
        Args:
            db: Database session
            contact_id: Contact ID
            tag_id: Tag ID
            
        Returns:
            Contact: Updated contact
        """
        contact = self.get(db, contact_id)
        tag = db.query(Tag).get(tag_id)
        
        if contact is None or tag is None:
            raise ValueError(f"Contact with id {contact_id} or Tag with id {tag_id} not found")
        
        contact.tags.remove(tag)
        db.commit()
        db.refresh(contact)
        return contact


class CompanyRepository(BaseRepository[Company]):
    """Repository for Company model operations."""
    
    def __init__(self):
        super().__init__(Company)
    
    def get_by_name(self, db: Session, name: str) -> Optional[Company]:
        """
        Get a company by name.
        
        Args:
            db: Database session
            name: Company name
            
        Returns:
            Optional[Company]: Found company or None
        """
        return db.query(Company).filter(Company.name == name).first()
    
    def search(self, db: Session, query: str, skip: int = 0, limit: int = 100) -> List[Company]:
        """
        Search companies by name or industry.
        
        Args:
            db: Database session
            query: Search query
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Company]: List of matching companies
        """
        search_term = f"%{query}%"
        return db.query(Company).filter(
            or_(
                Company.name.ilike(search_term),
                Company.industry.ilike(search_term)
            )
        ).offset(skip).limit(limit).all()
    
    def get_by_industry(self, db: Session, industry: str, skip: int = 0, limit: int = 100) -> List[Company]:
        """
        Get companies by industry.
        
        Args:
            db: Database session
            industry: Industry name
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Company]: List of companies
        """
        return db.query(Company).filter(Company.industry == industry).offset(skip).limit(limit).all()


class TagRepository(BaseRepository[Tag]):
    """Repository for Tag model operations."""
    
    def __init__(self):
        super().__init__(Tag)
    
    def get_by_name(self, db: Session, name: str) -> Optional[Tag]:
        """
        Get a tag by name.
        
        Args:
            db: Database session
            name: Tag name
            
        Returns:
            Optional[Tag]: Found tag or None
        """
        return db.query(Tag).filter(Tag.name == name).first()
    
    def get_contacts_with_tag(self, db: Session, tag_id: int, skip: int = 0, limit: int = 100) -> List[Contact]:
        """
        Get all contacts with a specific tag.
        
        Args:
            db: Database session
            tag_id: Tag ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[Contact]: List of contacts with the tag
        """
        tag = self.get(db, tag_id)
        if tag is None:
            raise ValueError(f"Tag with id {tag_id} not found")
        
        return tag.contacts[skip:skip+limit]


class ContactActivityRepository(BaseRepository[ContactActivity]):
    """Repository for ContactActivity model operations."""
    
    def __init__(self):
        super().__init__(ContactActivity)
    
    def get_by_contact(self, db: Session, contact_id: int, skip: int = 0, limit: int = 100) -> List[ContactActivity]:
        """
        Get activities for a specific contact.
        
        Args:
            db: Database session
            contact_id: Contact ID
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ContactActivity]: List of contact activities
        """
        return db.query(ContactActivity).filter(
            ContactActivity.contact_id == contact_id
        ).order_by(ContactActivity.date.desc()).offset(skip).limit(limit).all()
    
    def get_by_activity_type(self, db: Session, activity_type: str, skip: int = 0, limit: int = 100) -> List[ContactActivity]:
        """
        Get activities by type.
        
        Args:
            db: Database session
            activity_type: Activity type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[ContactActivity]: List of contact activities
        """
        return db.query(ContactActivity).filter(
            ContactActivity.activity_type == activity_type
        ).order_by(ContactActivity.date.desc()).offset(skip).limit(limit).all()
