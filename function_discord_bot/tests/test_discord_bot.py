import sys
import os
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.headers = {"X-Signature-Ed25519": "sig", "X-Signature-Timestamp": "time"}
    req.json = {"type": 1, "data": {"name": "ping"}}
    return req

def test_discord_bot_ping(mock_request):
    with patch('main.check_security_headers') as mock_sec,          patch('main.jsonify') as mock_json:
        mock_json.side_effect = lambda x: x
        from main import function_discord_bot
        resp = function_discord_bot(mock_request)
        assert resp["type"] == 1

def test_discord_bot_command(mock_request):
    mock_request.json = {"type": 2, "data": {"name": "upload"}}
    with patch('main.check_security_headers') as mock_sec,          patch('main.jsonify') as mock_json,          patch.dict('main.registered_commands', {"upload": MagicMock(return_value="Output")}):
        mock_json.side_effect = lambda x: x
        from main import function_discord_bot
        resp = function_discord_bot(mock_request)
        assert resp["type"] == 4
