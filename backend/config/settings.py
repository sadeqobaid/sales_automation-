"""
Author Sadeq Obaid and Abdallah Obaid

Environment configuration module for the Sales Automation System.
This module loads and provides access to environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Application settings
APP_NAME = os.getenv("APP_NAME", "Sales Automation System")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
API_PREFIX = os.getenv("API_PREFIX", "/api/v1")
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development-only")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")

# Security settings
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "your-encryption-key-for-development-only")
PASSWORD_HASH_ALGORITHM = os.getenv("PASSWORD_HASH_ALGORITHM", "bcrypt")
