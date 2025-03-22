"""
Author Sadeq Obaid and Abdallah Obaid

Repositories package initialization for the Sales Automation System.
This module imports and exposes all repositories.
"""

from src.repositories.base import BaseRepository
from src.repositories.user_repository import UserRepository, RoleRepository, PermissionRepository, AuditLogRepository
from src.repositories.contact_repository import ContactRepository, CompanyRepository, TagRepository, ContactActivityRepository
from src.repositories.lead_repository import LeadRepository, LeadActivityRepository, OpportunityRepository, OpportunityActivityRepository

# Create repository instances
user_repository = UserRepository()
role_repository = RoleRepository()
permission_repository = PermissionRepository()
audit_log_repository = AuditLogRepository()

contact_repository = ContactRepository()
company_repository = CompanyRepository()
tag_repository = TagRepository()
contact_activity_repository = ContactActivityRepository()

lead_repository = LeadRepository()
lead_activity_repository = LeadActivityRepository()
opportunity_repository = OpportunityRepository()
opportunity_activity_repository = OpportunityActivityRepository()

__all__ = [
    'BaseRepository',
    'user_repository',
    'role_repository',
    'permission_repository',
    'audit_log_repository',
    'contact_repository',
    'company_repository',
    'tag_repository',
    'contact_activity_repository',
    'lead_repository',
    'lead_activity_repository',
    'opportunity_repository',
    'opportunity_activity_repository'
]
