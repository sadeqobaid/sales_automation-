"""
Author Sadeq Obaid and Abdallah Obaid

Main API router for the Sales Automation System.
This module configures and includes all API endpoints.
"""

from fastapi import APIRouter, FastAPI

from src.api import auth_endpoints, user_endpoints, contact_endpoints, lead_endpoints, marketing_endpoints

# Create main API router
api_router = APIRouter(prefix="/api/v1")

# Include all endpoint routers
api_router.include_router(auth_endpoints.router)
api_router.include_router(user_endpoints.router)
api_router.include_router(contact_endpoints.router)
api_router.include_router(lead_endpoints.router)
api_router.include_router(marketing_endpoints.router)

# Function to configure the FastAPI app with all routes
def configure_api_routes(app: FastAPI) -> None:
    """
    Configure all API routes for the FastAPI application.
    
    Args:
        app: FastAPI application
    """
    app.include_router(api_router)
