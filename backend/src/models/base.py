"""
Author Sadeq Obaid and Abdallah Obaid

Base model module for the Sales Automation System.
This module provides the base model class for all models in the system.
"""

import datetime
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, Integer, String, Boolean, func
from sqlalchemy.ext.declarative import declared_attr

from config.database import Base

class BaseModel(Base):
    """
    Base model class for all models in the system.
    
    This class provides common fields and methods for all models.
    """
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate table name automatically based on class name.
        
        Returns:
            str: Table name
        """
        return cls.__name__.lower()
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary.
        
        Returns:
            Dict[str, Any]: Dictionary representation of the model
        """
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseModel':
        """
        Create model instance from dictionary.
        
        Args:
            data: Dictionary with model data
            
        Returns:
            BaseModel: Model instance
        """
        return cls(**data)
    
    def update(self, data: Dict[str, Any]) -> None:
        """
        Update model instance from dictionary.
        
        Args:
            data: Dictionary with model data
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # Update updated_at timestamp
        self.updated_at = datetime.datetime.now()
