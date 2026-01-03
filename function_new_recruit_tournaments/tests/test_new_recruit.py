import sys
import os
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.json = {"start": "2023-01-01", "end": "2023-01-31"}
    return req

def test_new_recruit_tournaments_success(mock_request):
    with patch.dict(sys.modules):
        mock_google = MagicMock()
        mock_cloud = MagicMock()
        mock_wf = MagicMock()
        
        sys.modules['google'] = mock_google
        sys.modules['google.cloud'] = mock_cloud
        sys.modules['google.cloud.workflows_v1beta'] = mock_wf
        
        mock_google.cloud = mock_cloud
        mock_cloud.workflows_v1beta = mock_wf
        
        mock_google.__path__ = []
        mock_cloud.__path__ = []
        mock_wf.__spec__ = None
        
        sys.modules['google.cloud.storage'] = MagicMock()
        sys.modules['google.cloud.workflows'] = MagicMock()
        sys.modules['google.cloud.workflows.executions_v1beta'] = MagicMock()
        sys.modules['google.cloud.workflows.executions_v1beta.types'] = MagicMock()
        sys.modules['backoff'] = MagicMock()
        
        with patch('requests.post') as mock_post,              patch('main.get_cred_config') as mock_creds,              patch('main.store_data') as mock_store,              patch('main.get_tournament_games') as mock_games:
                 
            mock_creds.return_value = {"NR_USER": "u", "NR_PASSWORD": "p"}
            mock_store.return_value = {"name": "file.json", "event_id": "t1"}
            
            # Returns list of games (valid for Pydantic)
            mock_games.return_value = [{"id": 1, "p1": "a", "p2": "b"}, {"id": 2}]
            
            response_mock = MagicMock()
            response_mock.json.side_effect = [
                {"tournaments": [{"_id": "t1", "name": "T1", "type": 0, "status": 3, "start": "2023-01-01", "end": "2023-01-02"}], "total": 1},
                {"_id": "t1", "name": "T1", "type": 0, "status": 3, "start": "2023-01-01", "end": "2023-01-02", "teams": [], "showlists": True, "visibility": 1, "rounds": []},
                [{"game_id": "g1"}],
                {"tournaments": [], "total": 1}
            ]
            mock_post.return_value = response_mock
            
            from main import function_new_recruit_tournaments
            resp, code = function_new_recruit_tournaments(mock_request)
            assert code == 200
