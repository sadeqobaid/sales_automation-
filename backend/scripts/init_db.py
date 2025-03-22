"""
Author Sadeq Obaid and Abdallah Obaid

Database initialization script for the Sales Automation System.
This script initializes the database and applies migrations.
"""

import logging
import sys
from pathlib import Path

# Add the parent directory to sys.path to allow imports
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.database_utils import init_db, check_database_connection
from src.utils.migration_utils import apply_migrations

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/db_init.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """
    Main function to initialize the database.
    """
    logger.info("Starting database initialization")
    
    # Check database connection
    if not check_database_connection():
        logger.error("Failed to connect to the database. Aborting initialization.")
        return False
    
    logger.info("Database connection successful")
    
    # Initialize database tables
    try:
        init_db()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        return False
    
    # Apply migrations
    if not apply_migrations():
        logger.error("Failed to apply migrations")
        return False
    
    logger.info("Database initialization completed successfully")
    return True

if __name__ == "__main__":
    # Create logs directory if it doesn't exist
    Path("logs").mkdir(exist_ok=True)
    
    success = main()
    sys.exit(0 if success else 1)
