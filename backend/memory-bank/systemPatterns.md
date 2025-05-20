# System Patterns: Digital Gemba Root Cause Analysis

## Architecture
- FastAPI-based REST API architecture
- Modular design with separation of concerns:
  - `main.py`: API endpoints and request/response models
  - `ai.py`: AI model implementation for root cause analysis
  - `database.py`: Database connectivity and operations
  - `auth.py`: Authentication mechanisms

## Key Technical Decisions
- Using Pydantic models for request/response validation
- Dependency injection pattern for database and AI model access
- API key authentication for securing endpoints
- Structured error handling with graceful degradation

## Design Patterns
- Repository pattern for database access
- Factory pattern for AI model initialization
- Data Transfer Objects (DTOs) via Pydantic models
- Middleware for CORS and authentication

## Component Interactions
- API endpoints in main.py depend on AI model and database components
- Authentication middleware validates API keys before processing requests
- Database connector provides data persistence and retrieval
- AI model processes inputs to generate root causes, actions, and scores
