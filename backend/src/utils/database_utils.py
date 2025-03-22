"""
Author Sadeq Obaid and Abdallah Obaid

Database connection module for the Sales Automation System.
This module provides database connection utilities and pooling.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config.database import SessionLocal, engine, Base

# Configure logger
logger = logging.getLogger(__name__)

def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function creates all tables defined in the models.
    It should be called during application startup.
    """
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise

@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    This function provides a context manager for database sessions,
    ensuring that sessions are properly closed and exceptions are handled.
    
    Yields:
        Session: SQLAlchemy database session
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        session.close()

def check_database_connection() -> bool:
    """
    Check if the database connection is working.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    try:
        # Try to connect to the database
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection error: {str(e)}")
        return False
