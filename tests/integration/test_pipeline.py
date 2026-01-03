import sys
import os
import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add paths to sys.path so we can import the functions
# Add ROOT to sys.path so we can import modules as packages or directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

# KEY: Insert function_data_conversion at index 0 LAST so it is checked FIRST
# We don't strictly need function_new_recruit_tournaments in path for this test since we mocked the logic
sys.path.insert(0, os.path.join(project_root, 'function_new_recruit_tournaments')) # 2nd priority
sys.path.insert(0, os.path.join(project_root, 'function_data_conversion'))      # 1st priority

# Import using direct module name if they are in path
# Now 'import main' should pick up function_data_conversion/main.py

# Mock google
mock_google = MagicMock()
mock_google.__path__ = []
sys.modules["google"] = mock_google

# Mock google.cloud
mock_cloud = MagicMock()
mock_cloud.__path__ = []
sys.modules["google.cloud"] = mock_cloud
mock_google.cloud = mock_cloud # Link parent

# Mock google.cloud.logging
mock_logging = MagicMock()
sys.modules["google.cloud.logging"] = mock_logging
# IMPORTANT: Attempting to access google.cloud.logging requires the attribute on the parent
mock_cloud.logging = mock_logging
# And the Client class
mock_logging.Client.return_value = MagicMock()

# Mock google.cloud.storage
mock_storage = MagicMock()
mock_storage.__path__ = [] 
sys.modules["google.cloud.storage"] = mock_storage
mock_cloud.storage = mock_storage # Link parent

# Mock google.cloud.storage.blob
mock_blob_module = MagicMock()
sys.modules["google.cloud.storage.blob"] = mock_blob_module

# Mock functions_framework with pass-through decorator
# Because @functions_framework.http wraps the function, we need it to return the function itself
mock_framework = MagicMock()
def pass_through(func):
    return func
mock_framework.http = pass_through
sys.modules["functions_framework"] = mock_framework 

# Mock google.cloud.logging_v2? Sometimes imported implicitly. Not strictly needed if logging is mocked.


from main import function_data_conversion

def test_pipeline_new_recruit_flow():
    """
    Integration test that simulates the flow:
    1.  New Recruit Data (from saved samples)
    2.  Transformed into storage format (logic from function_new_recruit_tournaments)
    3.  Processed by function_data_conversion
    """
    
    # 1. Load Samples
    base_path = Path(__file__).parent
    t_id = "677fc8a9e68eb714beeaa5fd" # The ID we investigated
    
    with open(base_path / f"sample_tournament_{t_id}.json", "r", encoding="utf-8") as f:
        t_data = json.load(f)
        
    with open(base_path / f"sample_games_{t_id}.json", "r", encoding="utf-8") as f:
        games_data = json.load(f)
        
    # 2. Simulate Data Construction (mirroring function_new_recruit_tournaments/main.py)
    # logic: name = event.name or event.short...
    # logic: type = tournament.type
    
    # Construct the JSON that is stored in the bucket
    storage_data = {
        "name": t_data.get("name"),
        "games": games_data,
        "country_name": "",
        "country_flag": "",
        "participants_per_team": 0,
        "team_point_cap": 0,
        "team_point_min": 0,
        "type": t_data.get("type", 0), # Default to 0 if missing (though we verified it's present in detail)
        "teams": t_data.get("teams", []),
        "rounds": len(t_data.get("rounds") or [])
    }
    
    print(f"Constructed Storage Payload. Games count: {len(storage_data['games'])}. Teams count: {len(storage_data['teams'])}")
    
    # 3. Invoke function_data_conversion
    # It expects: request.json["data"] = {"name": "newrecruit_tournament.json", "event_id": t_id}
    # It attempts to download: "newrecruit_tournaments", t_id
    
    mock_request = MagicMock()
    mock_request.json = {
        "data": {
            "name": "newrecruit_tournament.json",
            "event_id": t_id
        }
    }
    
    # We must mock google.cloud.storage to return our storage_data
    with patch('function_data_conversion.main.google.cloud.storage.Client') as mock_client:
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        
        mock_client.return_value.get_bucket.return_value = mock_bucket
        mock_bucket.get_blob.return_value = mock_blob # for download_blob call
        
        # When blob.download_to_filename is called, write our JSON to that file
        def side_effect_download(filename):
            with open(filename, 'w') as f:
                json.dump(storage_data, f)
            print(f"Mock download wrote to {filename}")
            
        mock_blob.download_to_filename.side_effect = side_effect_download
        
        # Also need to mock upload_blob because the function uploads the result
        # We can inspect what it tries to upload
        upload_blob_mock = mock_bucket.blob.return_value
        
        # Mock other dependencies that migth be called
        with patch('function_data_conversion.main.remove') as mock_remove: 
             # Mock remove to do nothing (except verify call) 
             pass
        
        # Execute
        print("Invoking function_data_conversion...")
        result, code = function_data_conversion(mock_request)
        
        print(f"Result Code: {code}")
        # print(f"Result Body: {result}")
        
        # Assertions
        assert code == 200, f"Conversion failed with code {code}. Message: {result.get('message')}"
        
        # Check validation stats
        val_count = result.get('validation_count')
        print(f"Validation Count: {val_count}")
        parsing_errors = result.get('parsing_errors', [])
        if parsing_errors:
            print("PARSING ERRORS FOUND:")
            for e in parsing_errors:
                print(f"- {e}")
        
        # Check validation errors details
        val_errors = result.get('validation_errors', [])
        if val_errors:
            print(f"Validation Errors (Business Logic): {len(val_errors)}")
            # print(val_errors)
            
        # We expect at least some successful conversions if data is valid
        # There are 31 games, multiple teams.
        assert val_count > 0, "No armies passed validation!"

if __name__ == "__main__":
    # Allow running directly
    try:
        test_pipeline_new_recruit_flow()
        print("Test Passed!")
    except AssertionError as e:
        print(f"Test Failed: {e}")
    except Exception as e:
        print(f"Test Error: {e}")
        import traceback
        traceback.print_exc()
