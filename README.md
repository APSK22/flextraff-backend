# Flextraff ATCS Backend

A standalone FastAPI microservice that provides intelligent traffic management capabilities for the FlexTraff Admin Panel.

## Project Overview

**Flextraff ATCS Backend** is a Python FastAPI microservice that processes RFID FastTag vehicle detection data, calculates adaptive traffic light timings, and provides comprehensive APIs for the admin dashboard.

## Architecture

- **Backend Type**: Standalone FastAPI microservice with CORS-enabled APIs
- **Frontend Integration**: Designed for Django+React Admin Panel consumption
- **Database**: Supabase PostgreSQL for data persistence and authentication
- **Authentication**: Supabase Auth (manual user creation only)
- **API**: RESTful endpoints + WebSocket for real-time dashboard updates

## Project Structure

```
flextraff-backend/
├── app/                           # Main application code
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Configuration settings
│   ├── models/                    # Pydantic data models
│   ├── services/                  # Business logic services
│   ├── routers/                   # API route handlers
│   ├── middleware/                # Custom middleware
│   ├── database/                  # Database configuration
│   └── utils/                     # Utility functions
├── tests/                         # Test suite
├── deployment/                    # Deployment configurations
├── docs/                          # Documentation
└── requirements.txt               # Python dependencies
```

## Setup Instructions

1. Clone the repository
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate` (macOS/Linux) or `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Set up environment variables (copy `.env.example` to `.env`)
6. Run the application: `uvicorn app.main:app --reload`

## Development

This project is designed to integrate with the FlexTraff Admin Panel at:
https://github.com/MananBagga/Flextraff-Admin-Panel

## Documentation

- API documentation will be available at `/docs` when the server is running
- Additional documentation can be found in the `docs/` directory

## License

[Add your license information here]