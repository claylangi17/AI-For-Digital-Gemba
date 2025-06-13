from fastapi import FastAPI, HTTPException, Depends
from app.auth import get_api_key
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from datetime import datetime

from app.database import DatabaseConnector
from app.ai import RootCauseAI
from app.attendance_db import AttendanceDB

# Initialize FastAPI app
app = FastAPI(
    title="Gemba Digital with AI - Root Cause Suggestion",
    description="API for suggesting root causes based on historical data and AI reasoning",
    version="1.0.0"
)

# Add CORS middleware for web/mobile integration
app.add_middleware(
    CORSMiddleware,
    # In production, replace with specific frontend domains
    allow_origins=["*"],
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
    user_id: str


class RootCauseScoreResponse(BaseModel):
    scores: List[ScoreItem]
    summary: str

# Models for attendance API


class AttendanceRequest(BaseModel):
    user_id: str
    qr_token: str


class AttendanceData(BaseModel):
    user_id: str
    timestamp: str
    status: str
    time_in: Optional[str] = None
    time_out: Optional[str] = None
    user_name: Optional[str] = None
    role: Optional[str] = None


class AttendanceResponse(BaseModel):
    status: str
    message: str
    data: Optional[AttendanceData] = None

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

# Dependency to get attendance database connection


def get_attendance_db():
    db = AttendanceDB()
    try:
        db.connect()
        yield db
    finally:
        db.disconnect()

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
        raise HTTPException(
            status_code=400, detail="Area, problem, and category are required")

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
        raise HTTPException(
            status_code=400, detail="At least one root cause with user_id is required")

    # Validate each item has a root_cause and user_id
    for item in request.root_causes:
        if not item.root_cause or not item.user_id:
            raise HTTPException(
                status_code=400, detail="Each root cause item must have both 'root_cause' and 'user_id' values")

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
        raise HTTPException(
            status_code=400, detail="Area, problem, root cause, and category are required")

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
    attendance_db: AttendanceDB = Depends(get_attendance_db),
    api_key: str = Depends(get_api_key)
):
    # Validate request
    if not request.area or not request.problem or not request.category or not request.root_causes or not request.user_id:
        raise HTTPException(
            status_code=400, detail="Area, problem, category, user_id, and at least one root cause are required")

    if len(request.root_causes) < 1:
        raise HTTPException(
            status_code=400, detail="At least one root cause is required for scoring")

    # Use AI to score the root causes against benchmark criteria
    scoring_result = ai_model.score_root_causes(
        area=request.area,
        problem=request.problem,
        category=request.category,
        root_causes=request.root_causes
    )

    # Check if there was an error in the scoring process
    if "error" in scoring_result:
        error_message = scoring_result.get(
            "error", "Unknown error during scoring process")
        print(f"Scoring error: {error_message}")
        # Don't fail the API, just return the partial result with scores of 0

    # Add points to the user based on the total score
    # Find the highest scoring root cause
    max_score = 0
    if "scores" in scoring_result and scoring_result["scores"]:
        for score_item in scoring_result["scores"]:
            if score_item.get("total_score", 0) > max_score:
                max_score = score_item.get("total_score", 0)
        
        # Add points to user based on the highest score
        if max_score > 0:
            # Get current user points
            try:
                # Connect to database if not connected
                if not attendance_db.connection or not attendance_db.connection.is_connected():
                    attendance_db.connect()

                # Get current user points
                user_query = "SELECT points FROM users WHERE id = %s"
                attendance_db.cursor.execute(user_query, (request.user_id,))
                user = attendance_db.cursor.fetchone()

                if user:
                    current_points = user['points'] or 0
                    
                    # Use the score directly (already in 1-100 range from AI)
                    points_to_add = max(1, min(100, int(max_score)))
                    new_points = current_points + points_to_add

                    # Update user points
                    update_query = "UPDATE users SET points = %s WHERE id = %s"
                    attendance_db.cursor.execute(update_query, (new_points, request.user_id))

                    # Use 'contribution' category from the dropdown menu
                    current_time = datetime.now()
                    print(f"Recording points with 'ROOT' category")
                    history_query = f"""
                    INSERT INTO point_histories 
                    (userid, type, category, point_before, point_earned, point_after, created_at, updated_at)
                    VALUES ('{request.user_id}', 'INC', 'ROOT', {current_points}, {points_to_add}, {new_points}, '{current_time}', '{current_time}')
                    """
                    
                    # Print the actual query for debugging
                    print(f"Executing SQL query: {history_query}")
                    
                    # Execute the raw SQL query with the category directly in the SQL
                    attendance_db.cursor.execute(history_query)

                    attendance_db.connection.commit()
                    print(f"Successfully recorded {points_to_add} points for user {request.user_id} with category 'ROOT'")
                    print(f"Note: Using 'ROOT' category instead of 'contribution'")
            except Exception as e:
                print(f"Error recording root cause points: {str(e)}")
    
    # Return the scoring results
    return scoring_result

# API endpoint for QR-based attendance


@app.post("/api/attendance/qr", response_model=AttendanceResponse)
def record_attendance(
    request: AttendanceRequest,
    attendance_db: AttendanceDB = Depends(get_attendance_db),
    api_key: str = Depends(get_api_key)
):
    # Validate request
    if not request.user_id or not request.qr_token:
        raise HTTPException(
            status_code=400, detail="User ID and QR token are required")

    # Validate QR token
    session = attendance_db.validate_qr_token(request.qr_token)
    if not session:
        raise HTTPException(
            status_code=400, detail="Invalid or expired QR token")

    # Record presence
    success, message, presence_data = attendance_db.record_presence(
        user_id=request.user_id,
        session_id=session['id']
    )

    if not success:
        raise HTTPException(status_code=400, detail=message)

    # Return response
    return AttendanceResponse(
        status="success",
        message=message,
        data=AttendanceData(**presence_data)
    )

# API endpoint to get session attendees


@app.get("/api/session/{session_id}/attendees", response_model=List[Dict[str, Any]])
def get_session_attendees(
    session_id: int,
    attendance_db: AttendanceDB = Depends(get_attendance_db),
    api_key: str = Depends(get_api_key)
):
    attendees = attendance_db.get_session_attendees(session_id)
    return attendees


if __name__ == "__main__":
    # Run the API server
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
