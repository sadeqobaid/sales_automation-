"""
Author Sadeq Obaid and Abdallah Obaid

Main application module for the Sales Automation System.
This module initializes and runs the FastAPI application.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import APP_NAME, APP_VERSION, API_PREFIX, DEBUG, CORS_ORIGINS

# Create FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Sales Automation System API",
    docs_url=f"{API_PREFIX}/docs",
    redoc_url=f"{API_PREFIX}/redoc",
    openapi_url=f"{API_PREFIX}/openapi.json",
    debug=DEBUG
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint that returns basic application information.
    
    Returns:
        dict: Basic application information
    """
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "docs": f"{API_PREFIX}/docs"
    }

# Run the application
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
