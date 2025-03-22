"""
Author Sadeq Obaid and Abdallah Obaid

Models package initialization for the Sales Automation System.
This module imports and exposes all models.
"""

from src.models.base import BaseModel
from src.models.user import User, Role, Permission, RolePermission, AuditLog
from src.models.contact import Contact, Company, Tag, ContactActivity
from src.models.lead import Lead, LeadActivity, Opportunity, OpportunityActivity, LeadStatus, LeadSource, OpportunityStage

__all__ = [
    'BaseModel',
    'User',
    'Role',
    'Permission',
    'RolePermission',
    'AuditLog',
    'Contact',
    'Company',
    'Tag',
    'ContactActivity',
    'Lead',
    'LeadActivity',
    'LeadStatus',
    'LeadSource',
    'Opportunity',
    'OpportunityActivity',
    'OpportunityStage'
]
