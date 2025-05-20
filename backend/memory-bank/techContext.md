# Technical Context: Digital Gemba Root Cause Analysis

## Technologies
- **Python**: Core programming language
- **FastAPI**: Web framework for building APIs
- **Pydantic**: Data validation and settings management
- **Uvicorn**: ASGI server for running the FastAPI application
- **AI/ML**: Appears to be using custom AI models for analysis

## Dependencies
Based on the project structure and files observed:
- FastAPI and related dependencies
- Database connectivity (specific database type to be determined)
- Authentication mechanisms
- AI/ML libraries (to be determined from ai.py)

## Setup
- The project uses a virtual environment (venv)
- Requirements are specified in requirements.txt
- The API can be run using run_api.py or directly from main.py
- Environment variables are managed via .env file (with .env.example provided)

## Constraints
- API key authentication is required for all endpoints
- Error handling is implemented to prevent API failures
- The system appears designed to handle partial results rather than failing completely

## APIs
The API provides several endpoints:
- Root cause suggestion: Generates potential root causes for a problem
- Action suggestion: Recommends temporary and preventive actions
- Root cause scoring: Evaluates root causes against benchmark criteria
- Root cause merging: Combines similar root causes while preserving user information
- Area retrieval: Gets all unique areas for dropdown selection in UI
