"""
Author Sadeq Obaid and Abdallah Obaid

Base repository module for the Sales Automation System.
This module provides the base repository class for all repositories in the system.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
import logging

from src.models.base import BaseModel
from src.utils.database_utils import db_session

# Define a type variable for the model
T = TypeVar('T', bound=BaseModel)

# Configure logger
logger = logging.getLogger(__name__)

class BaseRepository(Generic[T]):
    """
    Base repository class for all repositories in the system.
    
    This class provides common CRUD operations for all repositories.
    """
    
    def __init__(self, model: Type[T]):
        """
        Initialize the repository with the model class.
        
        Args:
            model: The model class this repository handles
        """
        self.model = model
    
    def create(self, db: Session, obj_in: Union[Dict[str, Any], BaseModel]) -> T:
        """
        Create a new record.
        
        Args:
            db: Database session
            obj_in: Object data to create
            
        Returns:
            T: Created object
        """
        try:
            if isinstance(obj_in, dict):
                obj_data = obj_in
            else:
                obj_data = obj_in.to_dict()
                
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error creating {self.model.__name__}: {str(e)}")
            raise
    
    def get(self, db: Session, id: int) -> Optional[T]:
        """
        Get a record by ID.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            Optional[T]: Found object or None
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[T]:
        """
        Get multiple records with pagination.
        
        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List[T]: List of objects
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def update(
        self, db: Session, *, db_obj: T, obj_in: Union[Dict[str, Any], BaseModel]
    ) -> T:
        """
        Update a record.
        
        Args:
            db: Database session
            db_obj: Existing database object
            obj_in: New object data
            
        Returns:
            T: Updated object
        """
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.to_dict()
                
            for field in update_data:
                if hasattr(db_obj, field):
                    setattr(db_obj, field, update_data[field])
                    
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error updating {self.model.__name__}: {str(e)}")
            raise
    
    def delete(self, db: Session, *, id: int) -> T:
        """
        Delete a record.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            T: Deleted object
        """
        try:
            obj = db.query(self.model).get(id)
            if obj is None:
                raise ValueError(f"{self.model.__name__} with id {id} not found")
                
            db.delete(obj)
            db.commit()
            return obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting {self.model.__name__}: {str(e)}")
            raise
    
    def count(self, db: Session) -> int:
        """
        Count total records.
        
        Args:
            db: Database session
            
        Returns:
            int: Total count of records
        """
        return db.query(self.model).count()
    
    def exists(self, db: Session, id: int) -> bool:
        """
        Check if a record exists.
        
        Args:
            db: Database session
            id: Record ID
            
        Returns:
            bool: True if record exists, False otherwise
        """
        return db.query(self.model).filter(self.model.id == id).first() is not None
