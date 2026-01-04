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

def run_single_test(t_file, g_file):
    """Run pipeline for a single tournament/games pair"""
    t_id = t_file.stem.replace("tournament_", "")
    print(f"\n--- Testing Tournament ID: {t_id} ---")
    
    with open(t_file, "r", encoding="utf-8") as f:
        t_data = json.load(f)
        
    with open(g_file, "r", encoding="utf-8") as f:
        games_data = json.load(f)

    # 2. Simulate Data Construction 
    storage_data = {
        "name": t_data.get("name"),
        "games": games_data,
        "country_name": "",
        "country_flag": "",
        "participants_per_team": 0,
        "team_point_cap": 0,
        "team_point_min": 0,
        "type": t_data.get("type", 0), 
        "teams": t_data.get("teams", []),
        "rounds": len(t_data.get("rounds") or [])
    }
    
    print(f"Constructed Storage Payload. Games: {len(storage_data['games'])}, Teams: {len(storage_data['teams'])}")
    
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
        mock_bucket.get_blob.return_value = mock_blob 
        
        def side_effect_download(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(storage_data, f)
            # print(f"Mock download wrote to {filename}")
            
        mock_blob.download_to_filename.side_effect = side_effect_download
        upload_blob_mock = mock_bucket.blob.return_value
        
        with patch('function_data_conversion.main.remove'): 
            pass
        
        result, code = function_data_conversion(mock_request)
        
        if code != 200:
             print(f"FAILED: Code {code}. Message: {result.get('message')}")
             return False
        
        val_count = result.get('validation_count')
        print(f"Validation Count: {val_count}")
        
        parsing_errors = result.get('parsing_errors', [])
        if parsing_errors:
            print("PARSING ERRORS FOUND:")
            for e in parsing_errors:
                print(f"- {e}")
        
        if val_count == 0:
            print("FAILED: Zero validations.")
            return False
            
        return True

def test_pipeline_new_recruit_flow():
    # 1. Find Fixtures
    # Check fixtures dir AND integration dir (for legacy singular test support if needed)
    base_path = Path(__file__).parent.parent / "fixtures" / "new_recruit"
    if not base_path.exists():
         # Fallback to current dir if fixtures not generated, mostly for the specific case we just built
         # But the user asked for 5 samples loop.
         print(f"Fixture dir {base_path} not found. Running legacy single check in integration folder if exists.")
         base_path = Path(__file__).parent
    
    # Glob for tournaments
    tournament_files = list(base_path.glob("tournament_*.json"))
    # Also check sample_tournament_*.json (legacy name from previous step)
    tournament_files.extend(list(base_path.glob("sample_tournament_*.json")))
    
    if not tournament_files:
        print("No tournament samples found to test.")
        return

    print(f"Found {len(tournament_files)} samples.")
    failures = []
    
    for t_file in tournament_files:
        # Find matching games file
        # name pattern: tournament_ID.json -> games_ID.json
        # or sample_tournament_ID.json -> sample_games_ID.json
        id_part = t_file.name.replace("tournament_", "").replace("sample_", "") # result: ID.json
        prefix = "games_" if "sample_" not in t_file.name else "sample_games_"
        g_file = t_file.parent / (prefix + id_part)
        
        if not g_file.exists():
            print(f"Skipping {t_file.name}: missing {g_file.name}")
            continue
            
        try:
            success = run_single_test(t_file, g_file)
            if not success:
                failures.append(t_file.name)
        except Exception as e:
            print(f"EXCEPTION for {t_file.name}: {e}")
            import traceback
            traceback.print_exc()
            failures.append(t_file.name)

    if failures:
        raise AssertionError(f"Failures in {len(failures)} samples: {failures}")
    else:
        print("\nALL SAMPLES PASSED.")


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
