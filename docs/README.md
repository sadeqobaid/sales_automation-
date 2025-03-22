# Sales Automation System

## Authors
Sadeq Obaid and Abdallah Obaid

## Project Overview
This is a comprehensive sales automation system designed to streamline and optimize sales processes through AI-driven insights, automated follow-ups, and integrated marketing capabilities.

## Features
- **Sales Process Automation**: Lead scoring, automated follow-ups, deal management, task scheduling
- **Sales Forecasting**: Predictive analytics, revenue projections, churn prediction, AI-driven pricing
- **Marketing Planning & Automation**: Campaign execution, budget allocation, funnel analysis, customer segmentation
- **Integrations & APIs**: CRM, ERP, Email & Messaging, Social Media & Ads

## Tech Stack
- **Backend**: Python (FastAPI), PostgreSQL, Redis, Celery + RabbitMQ, AI/ML Frameworks
- **Frontend**: React.js (Next.js), Tailwind CSS, Chart.js, JWT Authentication
- **DevOps**: AWS, Docker, Kubernetes, CI/CD (GitHub Actions)

## Project Structure
```
sales_automation_dev/
├── backend/                 # Backend API and services
│   ├── src/                 # Source code
│   │   ├── api/             # API endpoints
│   │   ├── models/          # Database models
│   │   ├── services/        # Business logic
│   │   ├── utils/           # Utility functions
│   │   └── auth/            # Authentication
│   ├── tests/               # Test cases
│   │   ├── unit/            # Unit tests
│   │   └── integration/     # Integration tests
│   ├── config/              # Configuration files
│   ├── venv/                # Python virtual environment
│   └── requirements.txt     # Python dependencies
├── frontend/                # Frontend application
│   ├── src/                 # Source code
│   │   ├── components/      # React components
│   │   ├── pages/           # Next.js pages
│   │   ├── services/        # API services
│   │   ├── utils/           # Utility functions
│   │   ├── hooks/           # Custom React hooks
│   │   ├── context/         # React context
│   │   ├── assets/          # Static assets
│   │   └── styles/          # CSS styles
│   ├── public/              # Public assets
│   ├── next.config.js       # Next.js configuration
│   └── tailwind.config.js   # Tailwind CSS configuration
├── database/                # Database scripts
│   ├── migrations/          # Database migrations
│   ├── scripts/             # Database scripts
│   └── seeds/               # Seed data
├── docs/                    # Documentation
└── infrastructure/          # Infrastructure as code
    ├── docker/              # Docker configuration
    ├── kubernetes/          # Kubernetes configuration
    └── terraform/           # Terraform scripts
```

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Docker (optional)

### Backend Setup
1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file based on `.env.example`

5. Start the development server:
   ```
   uvicorn src.main:app --reload
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Create a `.env` file based on `.env.example`

4. Start the development server:
   ```
   npm run dev
   ```

## Development Workflow
1. Create feature branches from `develop`
2. Make changes and commit with descriptive messages
3. Create pull requests to merge back to `develop`
4. Run tests before submitting pull requests
5. Code reviews are required before merging

## License
Proprietary - All rights reserved
