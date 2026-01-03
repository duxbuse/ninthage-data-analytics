import pytest
from unittest.mock import MagicMock

import sys
import os
from unittest.mock import MagicMock, patch

# Add function path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock custom imports if strictly necessary, but better to use real if available.
# checking availability in next steps, assuming it's there.
# But for robustness, let's mock the keys.

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
    req.json = {
        "data": {
            "body": {
                "file_name": "test_list.json",
                "list_number": 2, # triggering the condition
                "output_table": "dataset:table"
            }
        },
        "army_info": {
            "body": {
                "loaded_tk_info": True,
                "validation_count": 2,
                "validation_errors": [],
                "possible_tk_names": ["Player1"]
            }
        }
    }
    return req

def test_discord_success_reports_triggered(mock_env, mock_request):
    """Test that the webhook is sent when list_number is 2 (as per current code logic)."""
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "OK"
        
        from main import function_discord_success_reporting
        
        resp, code = function_discord_success_reporting(mock_request)
        
        assert code == 200
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs['json']['embeds'][0]['title'] == "Success:"

def test_discord_success_skips_others(mock_env, mock_request):
    """Test that the webhook is SKIPPED when list_number is not 2."""
    mock_request.json["data"]["body"]["list_number"] = 5
    
    with patch('requests.post') as mock_post:
        from main import function_discord_success_reporting
        
        resp, code = function_discord_success_reporting(mock_request)
        
        assert code == 200
        assert "skipped" in resp
        mock_post.assert_not_called()
