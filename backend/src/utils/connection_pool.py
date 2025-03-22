"""
Author Sadeq Obaid and Abdallah Obaid

Database connection pool configuration for the Sales Automation System.
This module configures the SQLAlchemy connection pool for optimal performance.
"""

import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from config.database import engine
from config.settings import DEBUG

# Configure logger
logger = logging.getLogger(__name__)

# Configure connection pool
def configure_connection_pool():
    """
    Configure the SQLAlchemy connection pool.
    
    This function sets up the connection pool with optimal settings
    for the Sales Automation System.
    """
    # Set pool size based on expected concurrent users
    engine.pool_size = 10
    engine.max_overflow = 20
    
    # Set pool recycle time to avoid stale connections
    engine.pool_recycle = 3600  # Recycle connections after 1 hour
    
    # Set pool timeout
    engine.pool_timeout = 30  # 30 seconds timeout
    
    # Set pool pre-ping to detect disconnections
    engine.pool_pre_ping = True
    
    logger.info("Database connection pool configured successfully")

# Add event listeners for connection debugging if in debug mode
if DEBUG:
    @event.listens_for(Engine, "connect")
    def connect(dbapi_connection, connection_record):
        logger.debug("Connection created")

    @event.listens_for(Engine, "checkout")
    def checkout(dbapi_connection, connection_record, connection_proxy):
        logger.debug("Connection checked out")

    @event.listens_for(Engine, "checkin")
    def checkin(dbapi_connection, connection_record):
        logger.debug("Connection checked in")

# Configure connection pool on module import
configure_connection_pool()
