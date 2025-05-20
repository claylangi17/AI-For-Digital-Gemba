from fastapi import FastAPI, HTTPException, Depends
from app.auth import get_api_key
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os

from app.database import DatabaseConnector
from app.ai import RootCauseAI

# Initialize FastAPI app
app = FastAPI(
    title="Gemba Digital with AI - Root Cause Suggestion",
    description="API for suggesting root causes based on historical data and AI reasoning",
    version="1.0.0"
)

# Add CORS middleware for web/mobile integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific frontend domains
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Define request and response models
class RootCauseRequest(BaseModel):
    area: str
    problem: str
    category: str

class RootCauseResponse(BaseModel):
    input_area: str
    input_problem: str
    suggested_root_causes: List[str]
    
# New models for the root cause merging API
class RootCauseItem(BaseModel):
    root_cause: str
    user_id: str

class MergeRootCauseRequest(BaseModel):
    root_causes: List[RootCauseItem]
    
class OriginalRootCauseItem(BaseModel):
    root_cause: str
    user_id: str
    
class MergedRootCauseGroup(BaseModel):
    merged_root_cause: str
    original_data: List[OriginalRootCauseItem]
    
class MergeRootCauseResponse(BaseModel):
    merged_root_causes: List[MergedRootCauseGroup]
    individual_root_causes: List[OriginalRootCauseItem]
    all_original_data: List[OriginalRootCauseItem]
    
# New models for the action suggestion API
class ActionSuggestionRequest(BaseModel):
    area: str
    problem: str
    root_cause: str
    category: str
    
class ActionSuggestionResponse(BaseModel):
    input_area: str
    input_problem: str
    input_root_cause: str
    temporary_actions: List[str]
    preventive_actions: List[str]

# New models for the root cause scoring API
class ScoreItem(BaseModel):
    root_cause: str
    spesifisitas: float
    relevansi: float
    kejelasan: float
    actionability: float
    total_score: float
    feedback: str

class RootCauseScoreRequest(BaseModel):
    area: str
    problem: str
    category: str
    root_causes: List[str]
    
class RootCauseScoreResponse(BaseModel):
    scores: List[ScoreItem]
    summary: str

# Dependency to get database connection
def get_db():
    db = DatabaseConnector()
    try:
        db.connect()
        yield db
    finally:
        db.disconnect()

# Dependency to get AI model
def get_ai_model():
    return RootCauseAI()

# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Gemba Digital with AI - Root Cause Suggestion API", "version": "1.0.0"}

# API endpoint for root cause suggestion
@app.post("/api/root-cause/suggest", response_model=RootCauseResponse)
def suggest_root_causes(
    request: RootCauseRequest,
    db: DatabaseConnector = Depends(get_db),
    ai_model: RootCauseAI = Depends(get_ai_model),
    api_key: str = Depends(get_api_key)
):
    # Validate request
    if not request.area or not request.problem or not request.category:
        raise HTTPException(status_code=400, detail="Area, problem, and category are required")

    # Get semantically relevant historical data for root cause suggestions
    historical_data = db.get_semantic_root_cause_data(
        problem=request.problem,
        area=request.area, 
        category=request.category
    )

    # Generate suggestions using AI model
    suggested_causes = ai_model.suggest_root_causes(
        area=request.area,
        problem=request.problem,
        category=request.category,
        historical_data=historical_data
    )

    # Return response dalam format RootCauseResponse
    return RootCauseResponse(
        input_area=request.area,
        input_problem=request.problem,
        suggested_root_causes=suggested_causes
    )

# API endpoint to get all unique areas for dropdown selection in UI
@app.get("/api/areas", response_model=List[str])
def get_areas(db: DatabaseConnector = Depends(get_db), api_key: str = Depends(get_api_key)):
    areas = db.get_all_areas()
    return areas

# New API endpoint for merging similar root causes while preserving user information
@app.post("/api/root-cause/merge", response_model=MergeRootCauseResponse)
def merge_root_causes(
    request: MergeRootCauseRequest,
    ai_model: RootCauseAI = Depends(get_ai_model),
    api_key: str = Depends(get_api_key)
):
    # Validate request
    if not request.root_causes or len(request.root_causes) < 1:
        raise HTTPException(status_code=400, detail="At least one root cause with user_id is required")
    
    # Validate each item has a root_cause and user_id
    for item in request.root_causes:
        if not item.root_cause or not item.user_id:
            raise HTTPException(status_code=400, detail="Each root cause item must have both 'root_cause' and 'user_id' values")
    
    # Convert Pydantic models to dictionaries for AI processing
    root_causes_data = [item.dict() for item in request.root_causes]
    
    # Use AI to analyze and merge similar root causes
    merge_result = ai_model.analyze_and_merge_root_causes(root_causes_data)
    
    # Return the merged and individual root causes
    return merge_result

# API endpoint for suggesting temporary and preventive actions
@app.post("/api/actions/suggest", response_model=ActionSuggestionResponse)
def suggest_actions(
    request: ActionSuggestionRequest,
    db: DatabaseConnector = Depends(get_db),
    ai_model: RootCauseAI = Depends(get_ai_model),
    api_key: str = Depends(get_api_key)
):
    # Validate request
    if not request.area or not request.problem or not request.root_cause or not request.category:
        raise HTTPException(status_code=400, detail="Area, problem, root cause, and category are required")

    # Get semantically relevant historical data for action suggestions
    historical_data = db.get_semantic_action_data(
        problem=request.problem,
        root_cause=request.root_cause,
        area=request.area, 
        category=request.category
    )

    # Generate action suggestions using AI model
    action_suggestions = ai_model.suggest_actions(
        area=request.area,
        problem=request.problem,
        root_cause=request.root_cause,
        category=request.category,
        historical_data=historical_data
    )

    # Return response in the expected format
    return ActionSuggestionResponse(
        input_area=request.area,
        input_problem=request.problem,
        input_root_cause=request.root_cause,
        temporary_actions=action_suggestions.get("temporary_actions", []),
        preventive_actions=action_suggestions.get("preventive_actions", [])
    )

# API endpoint for scoring root causes based on benchmark criteria
@app.post("/api/root-cause/score", response_model=RootCauseScoreResponse)
def score_root_causes(
    request: RootCauseScoreRequest,
    ai_model: RootCauseAI = Depends(get_ai_model),
    api_key: str = Depends(get_api_key)
):
    # Validate request
    if not request.area or not request.problem or not request.category or not request.root_causes:
        raise HTTPException(status_code=400, detail="Area, problem, category, and at least one root cause are required")
    
    if len(request.root_causes) < 1:
        raise HTTPException(status_code=400, detail="At least one root cause is required for scoring")
    
    # Use AI to score the root causes against benchmark criteria
    scoring_result = ai_model.score_root_causes(
        area=request.area,
        problem=request.problem,
        category=request.category,
        root_causes=request.root_causes
    )
    
    # Check if there was an error in the scoring process
    if "error" in scoring_result:
        error_message = scoring_result.get("error", "Unknown error during scoring process")
        print(f"Scoring error: {error_message}")
        # Don't fail the API, just return the partial result with scores of 0
    
    # Return the scoring results
    return scoring_result

if __name__ == "__main__":
    # Run the API server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
