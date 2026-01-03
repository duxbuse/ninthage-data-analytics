import sys
import os
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.headers = {"X-Signature-Ed25519": "sig", "X-Signature-Timestamp": "time"}
    return req

def test_success_reporting_success(mock_request):
    mock_request.json = {
        "data": {
            "name": "Test Workflow", 
            "argument": "{}", 
            "body": {
                "file_name": "test_file.json",
                "list_number": 2, # MUST be 2 to trigger post
                "output_table": "dataset.table"
            }
        }, 
        "army_info": {
            "body": {
                "loaded_tk_info": "TK Info",
                "validation_count": 10,
                "validation_errors": [{"player_name": "P1", "validation_errors": ["Error"]}]
            }
        },
        "source": "workflow"
    }
    
    with patch('main.requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        from main import function_discord_success_reporting
        resp, code = function_discord_success_reporting(mock_request)
        assert code == 200
        mock_post.assert_called()
