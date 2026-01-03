import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add function path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Clients
import google.cloud.bigquery
import google.cloud.storage
import functions_framework

mock_bq_client = MagicMock()
google.cloud.bigquery.Client = MagicMock(return_value=mock_bq_client)


mock_storage_client = MagicMock()
google.cloud.storage.Client = MagicMock(return_value=mock_storage_client)

# Mock _EmptyRowIterator for delete check
class MockEmptyRowIterator:
    pass

google.cloud.bigquery.table = MagicMock()
google.cloud.bigquery.table._EmptyRowIterator = MockEmptyRowIterator


from main import function_upload_data_into_bigquery

@pytest.fixture
def mock_request():
    req = MagicMock()
    return req

def test_upload_valid_remote(mock_request):
    """Test upload logic with valid remote inputs."""
    mock_request.json = {
        "json_file": {
            "body": {
                "file_name": "test-event.json",
                "bucket_name": "test-bucket"
            }
        }
    }
    
    with patch('main.download_blob') as mock_download, \
         patch('main.google.cloud.bigquery.Client') as mock_bq_client, \
         patch('main.open', new_callable=MagicMock) as mock_open, \
         patch('main.remove') as mock_remove:
        
        # Setup mocks
        mock_blob = MagicMock()
        mock_download.return_value = mock_blob
        
        mock_bq = mock_bq_client.return_value
        mock_job = MagicMock()
        mock_job.output_rows = 100
        mock_job.errors = None
        mock_bq.load_table_from_file.return_value = mock_job
        mock_bq.load_table_from_file.return_value = mock_job
        # Return our mock iterator that passes isinstance check
        mock_bq.query.return_value.result.return_value = MockEmptyRowIterator()
        
        response, code = function_upload_data_into_bigquery(mock_request, is_remote=True)
        
        assert code == 200
        assert response['list_number'] == 100
        mock_bq.load_table_from_file.assert_called_once()
