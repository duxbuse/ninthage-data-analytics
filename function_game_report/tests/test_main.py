import pytest
from unittest.mock import MagicMock

import sys
import os
from unittest.mock import MagicMock, patch
import pytest
import json

# Add function path to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.form.to_dict.return_value = {
        "player1_name": "sean",
        "player1_score": "10",
        "player2_name": "courtney", 
        "player2_score": "10",
        "map_selected": "Map1",
        "deployment_selected": "Dep1",
        "objective_selected": "Obj1"
    }
    return req

def test_game_report_success(mock_request):
    """Test game report processing."""
    
    # Mock Flask render_template
    with patch('main.render_template') as mock_render, \
         patch('main.google.cloud.storage.Client') as mock_storage_cls, \
         patch('main.google.cloud.workflows_v1beta.WorkflowsClient') as mock_workflows_cls, \
         patch('main.executions_v1beta.ExecutionsClient') as mock_exec_cls, \
         patch('main.write_report_to_json') as mock_write, \
         patch('main.remove') as mock_remove:
         
        mock_render.return_value = "<html>Success</html>"
        
        # Setup Storage Mock
        mock_storage = mock_storage_cls.return_value
        mock_bucket = mock_storage.get_bucket.return_value
        mock_blob = mock_bucket.blob.return_value
        
        # Setup Workflow Mocks
        mock_workflows = mock_workflows_cls.return_value
        mock_workflows.workflow_path.return_value = "projects/p/locations/l/workflows/w"
        
        mock_exec = mock_exec_cls.return_value
        mock_exec.create_execution.return_value.name = "exec-123"
        
        from main import function_game_report
        
        resp = function_game_report(mock_request)
        
        assert resp == "<html>Success</html>"
        
        # Verify storage upload
        mock_bucket.blob.assert_called()
        mock_blob.upload_from_filename.assert_called()
        
        # Verify workflow execution
        mock_exec.create_execution.assert_called_once()
        call_args = mock_exec.create_execution.call_args
        execution_arg = call_args.kwargs['execution']
        # Check payload
        payload = json.loads(execution_arg.argument)
        assert payload['player1_name'] == 'sean'
        assert payload['name'] == 'manual_game_report'
