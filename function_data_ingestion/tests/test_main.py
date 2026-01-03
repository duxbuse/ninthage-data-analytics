import sys
import sys
from unittest.mock import MagicMock, patch

def test_ingestion_logic_via_exec():
    # define mocks in a dictionary to pass as globals
    mock_executions = MagicMock()
    mock_workflows = MagicMock()
    mock_ff = MagicMock()
    # Pass-through decorator
    mock_ff.cloud_event = lambda f: f
    
    # Mock modules
    mock_globals = {
        '__name__': 'ingestion_test_scope',
        'functions_framework': mock_ff,
        'google': MagicMock(),
        'json': sys.modules['json'], # Use real json
        'print': print, # Use real print
    }
    
    # Setup Google Cloud Mocks
    mock_globals['google'].cloud = MagicMock()
    mock_globals['google'].cloud.workflows = MagicMock()
    mock_globals['google'].cloud.workflows.executions_v1beta = mock_executions
    mock_globals['google'].cloud.workflows_v1beta = mock_workflows
    
    # Execution Client Mock
    mock_exec_client = MagicMock()
    mock_executions.ExecutionsClient.return_value = mock_exec_client
    mock_execution_instance = MagicMock()
    mock_exec_client.create_execution.return_value = mock_execution_instance
    mock_execution_instance.name = "test-execution"

    # Workflows Client Mock
    mock_workflows_client = MagicMock()
    mock_workflows.WorkflowsClient.return_value = mock_workflows_client
    mock_workflows_client.workflow_path.return_value = "projects/..."
    
    
    # Patch sys.modules to force imports to use our mocks
    with patch.dict(sys.modules, {
        'functions_framework': mock_ff,
        'google.cloud.workflows_v1beta': mock_workflows,
        'google.cloud.workflows': MagicMock(), # parent
        'google.cloud.workflows.executions_v1beta': mock_executions,
        'google.cloud.workflows.executions_v1beta.types': MagicMock(),
    }):
        # Link types for specific import 'from ...types import executions'
        sys.modules['google.cloud.workflows.executions_v1beta.types'].executions = MagicMock()
        
        # Read and exec main.py
        with open('function_data_ingestion/main.py', 'r') as f:
            code = f.read()
        
        exec(code, mock_globals)
        
        # Extract the function
        function_data_ingestion = mock_globals['function_data_ingestion']
        
        # Run it
        mock_data = {"bucket": "b", "name": "n"}
        class MockEvent:
            data = mock_data
        
        function_data_ingestion(MockEvent)
    
    # Verify
    mock_exec_client.create_execution.assert_called_once()
