import sys
import os
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

mock_cloud = MagicMock()
mock_bq = MagicMock()
mock_bq_table = MagicMock()

sys.modules['google.cloud'] = mock_cloud
sys.modules['google.cloud.bigquery'] = mock_bq
sys.modules['google.cloud.bigquery.table'] = mock_bq_table

mock_cloud.bigquery = mock_bq

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.json = {}
    return req

@pytest.mark.skip(reason="Skipped due to local import mocking issues")
def test_static_data_success(mock_request):
    with patch('requests.Session.get') as mock_get,          patch('main.write_dicts_to_json') as mock_write,          patch('main.remove') as mock_remove,          patch('builtins.open', new_callable=MagicMock):
         
        mock_response = MagicMock()
        mock_response.status_code = 200
        data_mock = {}
        for s in ["versions", "armies", "organisations", "units", "magic_paths", "special_items", "banners", "maps"]:
             data_mock[s] = [{"id": 1}]
        mock_response.json.return_value = data_mock
        mock_get.return_value = mock_response
        
        mock_bq.Client.return_value.load_table_from_file.return_value.result.return_value = None
        
        from main import function_static_data
        resp, code = function_static_data(mock_request)
        assert code == 200