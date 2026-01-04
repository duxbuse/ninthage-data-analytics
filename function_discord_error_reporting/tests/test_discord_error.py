import sys
import os
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.json = {"error": {"message": "Test Error"}} # default
    req.headers = {"X-Signature-Ed25519": "sig", "X-Signature-Timestamp": "time"}
    return req

def test_error_reporting_success(mock_request):
    with patch('main.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        
        from main import function_discord_error_reporting
        
        mock_request.json = {
            "data": {"name": "TestFile"},
            "workflow_id": "wid",
            "error": {"message": "Test Error"}
        }
        
        resp, code = function_discord_error_reporting(mock_request)
        assert code == 200

def test_error_reporting_400(mock_request):
    # Add body to error payload to avoid KeyError in handle_400
    mock_request.json = {
        "data": {"name": "TestFile"},
        "workflow_id": "wid",
        "error": {
            "code": 400, 
            "message": "Bad Request",
            "body": {"message": "validation failed"} 
        }
    }
    
    with patch('main.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        
        from main import function_discord_error_reporting
        resp, code = function_discord_error_reporting(mock_request)
        assert code == 200
