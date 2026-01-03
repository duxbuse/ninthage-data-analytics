import pytest
from unittest.mock import MagicMock

import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# Add function path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_env():
    with patch.dict(os.environ, {
        "DISCORD_WEBHOOK_TOKEN": "mock_token",
        "DISCORD_WEBHOOK_ID": "mock_id"
    }):
        yield

@pytest.fixture
def mock_request():
    req = MagicMock()
    # Basic valid payload structure
    req.json = {
        "workflow_id": "wf-123",
        "data": {"name": "test_file.json"},
        "error": {"code": 500, "message": "Something went wrong"},
        "error_code": {"code": 500}
    }
    return req

def test_discord_error_reporting_default(mock_env, mock_request):
    """Test default error handling path."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"
        
        # We also need to mock the helper modules if we want to isolate main logic, 
        # or we rely on them being present. Assuming they are present.
        # However, they might process the message differently.
        
        from main import function_discord_error_reporting
        
        resp, code = function_discord_error_reporting(mock_request)
        
        assert code == 200
        mock_post.assert_called_once()
        # Verify default error logic was likely used (handling unknown error)

def test_discord_error_reporting_400(mock_env, mock_request):
    """Test 400 error handling."""
    mock_request.json["error_code"]["code"] = 400
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        
        from main import function_discord_error_reporting
        function_discord_error_reporting(mock_request)
        
        # Verify post called
        mock_post.assert_called_once()

def test_discord_error_reporting_no_payload(mock_env):
    """Test behavior with missing JSON payload."""
    req = MagicMock()
    req.json = None
    
    from main import function_discord_error_reporting
    resp, code = function_discord_error_reporting(req)
    
    assert code == 500
    assert "no json payload" in resp
