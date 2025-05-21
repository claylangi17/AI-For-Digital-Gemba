import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
# For testing, always use localhost regardless of what's in .env
# 0.0.0.0 is for server binding, not for client connections
API_PORT = os.getenv('API_PORT', '8000')
API_KEY = os.getenv('API_KEY', 'gemba-digital-api-3d9f8e7a1b2c')
BASE_URL = f"http://localhost:{API_PORT}"


def test_record_attendance():
    """
    Test the attendance recording API endpoint
    """
    # Test URL and headers
    url = f"{BASE_URL}/api/attendance/qr"
    headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

    # Sample valid request
    valid_request = {
        "user_id": "1",  # John Smith from test data
        "qr_token": "SESSION_2025_05_21_T1"  # Morning Inspection session
    }

    # Send request
    print("\n--- Testing Attendance API with valid data ---")
    response = requests.post(url, headers=headers, json=valid_request)

    # Print response
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test with invalid QR token
    invalid_token_request = {
        "user_id": "1",
        "qr_token": "INVALID_TOKEN"
    }

    # Send request with invalid token
    print("\n--- Testing Attendance API with invalid token ---")
    response = requests.post(url, headers=headers, json=invalid_token_request)

    # Print response
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    # Test with missing fields
    missing_fields_request = {
        "user_id": "1"
        # Missing qr_token
    }

    # Send request with missing fields
    print("\n--- Testing Attendance API with missing fields ---")
    response = requests.post(url, headers=headers, json=missing_fields_request)

    # Print response
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


def test_get_session_attendees():
    """
    Test the get session attendees API endpoint
    """
    # Test URL and headers
    url = f"{BASE_URL}/api/session/1/attendees"  # Session ID 1
    headers = {"X-API-Key": API_KEY}

    # Send request
    print("\n--- Testing Get Session Attendees API ---")
    response = requests.get(url, headers=headers)

    # Print response
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")


if __name__ == "__main__":
    test_record_attendance()
    test_get_session_attendees()
