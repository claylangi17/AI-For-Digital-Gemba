from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY_NAME = "X-API-KEY"
API_KEY = os.getenv("API_KEY")

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    if api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key"
    )
