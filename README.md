# Sales Automation System

## Overview
This repository contains the implementation of a comprehensive Sales Automation System designed to streamline sales processes, manage customer relationships, track leads, and automate marketing campaigns.

## Authors
- Sadeq Obaid
- Abdallah Obaid

## Project Structure
- **backend/**: Backend API implementation using FastAPI
  - **config/**: Configuration files for database, settings, etc.
  - **src/**: Source code
    - **models/**: Database models
    - **repositories/**: Data access layer
    - **api/**: API endpoints
    - **services/**: Business logic
    - **utils/**: Utility functions
    - **auth/**: Authentication and authorization
  - **tests/**: Unit and integration tests
  - **scripts/**: Utility scripts

## Current Progress
- ✅ Development environment setup
- ✅ Database connection layer implementation
- ✅ Core models implementation
  - User and authentication models
  - Contact management models
  - Lead management models
  - Marketing campaign models
- ✅ Repository layer implementation
- 🔄 API endpoints (in progress)
- 🔄 Security features (in progress)
- 🔄 User interface (in progress)

## Technology Stack
- **Backend**: Python, FastAPI, SQLAlchemy
- **Database**: PostgreSQL
- **Authentication**: JWT
- **Frontend**: React.js (planned)

## Getting Started
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up the database: `python backend/scripts/init_db.py`
4. Run the application: `python backend/main.py`

## Features
- User authentication and authorization with role-based access control
- Contact and company management
- Lead tracking and opportunity management
- Marketing campaign automation
- Sales pipeline visualization
- Reporting and analytics
- Integration capabilities

## Documentation
Detailed documentation is available in the `docs/` directory.
