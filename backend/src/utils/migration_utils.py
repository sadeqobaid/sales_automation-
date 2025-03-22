"""
Author Sadeq Obaid and Abdallah Obaid

Database migration script for the Sales Automation System.
This module provides utilities for managing database migrations using Alembic.
"""

import logging
import os
import subprocess
from typing import List, Optional

# Configure logger
logger = logging.getLogger(__name__)

def create_migration(message: str) -> bool:
    """
    Create a new database migration.
    
    Args:
        message: The migration message/description
        
    Returns:
        bool: True if migration was created successfully, False otherwise
    """
    try:
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", message],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Migration created successfully: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error creating migration: {e.stderr}")
        return False

def apply_migrations(revision: str = "head") -> bool:
    """
    Apply database migrations.
    
    Args:
        revision: The target revision to migrate to (default: "head")
        
    Returns:
        bool: True if migrations were applied successfully, False otherwise
    """
    try:
        result = subprocess.run(
            ["alembic", "upgrade", revision],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Migrations applied successfully: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error applying migrations: {e.stderr}")
        return False

def rollback_migration(revision: str = "-1") -> bool:
    """
    Rollback database migrations.
    
    Args:
        revision: The target revision to rollback to (default: "-1" for one step back)
        
    Returns:
        bool: True if rollback was successful, False otherwise
    """
    try:
        result = subprocess.run(
            ["alembic", "downgrade", revision],
            capture_output=True,
            text=True,
            check=True
        )
        logger.info(f"Migration rollback successful: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error rolling back migration: {e.stderr}")
        return False

def get_migration_history() -> List[str]:
    """
    Get the migration history.
    
    Returns:
        List[str]: List of migration history entries
    """
    try:
        result = subprocess.run(
            ["alembic", "history"],
            capture_output=True,
            text=True,
            check=True
        )
        history = result.stdout.strip().split("\n")
        return history
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting migration history: {e.stderr}")
        return []

def get_current_revision() -> Optional[str]:
    """
    Get the current database revision.
    
    Returns:
        Optional[str]: Current revision or None if error
    """
    try:
        result = subprocess.run(
            ["alembic", "current"],
            capture_output=True,
            text=True,
            check=True
        )
        current = result.stdout.strip()
        return current
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting current revision: {e.stderr}")
        return None
