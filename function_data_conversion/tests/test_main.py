import sys
import os
import pytest
from unittest.mock import MagicMock, patch
import json

# Add the function directory to the path so we can import main
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock Clients before importing main which instantiates them
import google.cloud.logging
import google.cloud.storage
# google.cloud.workflows might not be installed in all envs, check requirements. 
# But conversion requirements doesn't list workflows?
# Checking requirements.txt: It lists python-docx, jsons, google-cloud-storage, logging, etc.
# But does main.py use workflows?
# main.py does NOT use workflows. Ingestion uses it.
# So conversion test doesn't need workflows.

mock_logging_client = MagicMock()
google.cloud.logging.Client = MagicMock(return_value=mock_logging_client)

mock_storage_client = MagicMock()
google.cloud.storage.Client = MagicMock(return_value=mock_storage_client)

# functions_framework is installed, let it be.


# Now import the function
from main import function_data_conversion, Multi_Error

@pytest.fixture
def mock_request():
    req = MagicMock()
    req.get_json.return_value = {}
    return req

@pytest.fixture
def mock_storage():
    with patch('main.download_blob') as mock_download, \
         patch('main.upload_blob') as mock_upload, \
         patch('main.remove') as mock_remove, \
         patch('builtins.open', new_callable=MagicMock) as mock_open:
        yield {
            'download_blob': mock_download,
            'upload_blob': mock_upload,
            'remove': mock_remove,
            'open': mock_open
        }

def test_new_recruit_tournament_valid(mock_request, mock_storage):
    """Test processing a valid New Recruit tournament JSON."""
    mock_request.json = {
        "data": {
            "name": "newrecruit_tournament.json",
            "event_id": "valid_event_id"
        }
    }
    
    # Mock file content
    mock_json_data = {
        "name": "Test Event",
        "results": [
            {
                "name": "Player 1",
                "list": "Valid List 1" # Simplified for this mock, actual parser expects detailed structure
            }
        ]
    }
    
    # We need to mock the parser result since we aren't testing the parser logic itself here,
    # but the error handling wrapper.
    # However, armies_from_NR_tournament is imported in main. 
    # Let's mock the converter functions to control the "Partial Success" testing.
    
    
    with patch('main.armies_from_NR_tournament') as mock_parser, \
         patch('main.Write_army_lists_to_json_file') as mock_writer:
        # Mock returning a list of army objects
        mock_army = MagicMock()
        mock_army.validated = True
        mock_army.validation_errors = []
        mock_parser.return_value = ([mock_army], [])
        
        # Mock json.load to return our data
        with patch('json.load', return_value=mock_json_data):
            response, status_code = function_data_conversion(mock_request)
            
            assert status_code == 200
            assert response['validation_count'] == 1
            assert len(response['validation_errors']) == 0

def test_partial_success(mock_request, mock_storage):
    """Test processing where some parsing succeeds and some fails."""
    mock_request.json = {
        "data": {
            "name": "newrecruit_tournament.json",
            "event_id": "mixed_event_id"
        }
    }
    
    # Mocking appropriate behavior once "Partial Success" logic is implemented in main.py
    # Currently main.py raises Multi_Error and fails 400.
    # This test expects the NEW behavior: 200 OK with error details.
    
    with patch('main.armies_from_NR_tournament') as mock_parser, \
         patch('main.Write_army_lists_to_json_file') as mock_writer:
        # Simulate Multi_Error but for only part of the data? 
        # Actually the current parser raises Multi_Error for the whole batch. 
        # We will be refactoring `armies_from_NR_tournament` or handling it in `main.py`.
        # Assuming we wrap the parser call or the parser itself returns partials.
        # For now, let's assume `main.py` catches Multi_Error and formats the partial response if possible,
        # OR `armies_from_NR_tournament` is updated to return (armies, errors).
        
        # If we stick to the plan: "Implement 'Partial Success' logic in main.py",
        # it implies main.py handles the exception and if *some* armies were generated, it returns them.
        
        # Let's mock a Multi_Error that HAS some partial results attached to it, 
        # OR we assume the parser will be changed to not raise but return mixed results.
        
        # Scenario: Parser raises Multi_Error, but maybe we can attach partial results to it?
        # Or more cleanly: we update main.py to expect a tuple (armies, errors) from parsers?
        # A simpler approach for the legacy parsers: try/except per item? 
        # Most parsers in this project (nr_recruit, warhall) parse the whole file at once.
        
        # If the parser fails completely, we can't do partial success.
        # So checking `main.py` logic again... 
        # We need to essentially allow the parser to return what it has.
        
        # For this test, let's assume we've refactored to handle "valid_armies" being returned even if there are errors.
        # I will mock the return value as having some valid armies despite potential internal errors if we change the parser contract.
        # BUT `main.py` calls `armies_from_NR_tournament(data)`.
        
        # Let's assume we expect `main.py` to catch Multi_Error and check if there are ANY valid armies processed inside it?
        # No, Multi_Error is raised when it gives up.
        
        # Strategy: The Refactor will probably wrap the parser call. 
        # If the parser is atomic (all or nothing), we can't do partial success without refactoring the parser.
        # Re-reading `warhall.py` (Step 19): it collects errors in a list and raises `Multi_Error(errors)` at the end if `errors` is not empty.
        # Code: 
        #   if errors: raise Multi_Error(errors)
        # It DOES create `list_of_armies`.
        # So, if we change `warhall.py` (and others) to RETURN `list_of_armies, errors` instead of raising, 
        # `main.py` can then decide what to do.
        
        # So the test here should expect `main.py` to handle a return of `(armies, errors)` or similar.
        # Let's mock that behavior.
        
        mock_army = MagicMock()
        mock_army.validated = True
        mock_army.player_name = "Good Player"
        
        mock_error = "Bad Player Failed"
        
        # We'll patch the parser to return a tuple (armies, errors) instead of raising
        mock_parser.return_value = ([mock_army], [mock_error]) 
        
        with patch('json.load', return_value={}):
            response, status_code = function_data_conversion(mock_request)
            
            # This asserts the NEW desired behavior
            # This asserts the NEW desired behavior
            if status_code != 200:
                print(f"DEBUG: Status {status_code}, Response: {response}")
            
            assert status_code == 200
            assert response['validation_count'] == 1
            assert "Bad Player Failed" in str(response['parsing_errors'])
            # We might need a new field for 'parsing_errors' vs 'validation_errors'
            # 'validation_errors' in the current code is for armies that parsed but failed rules (e.g. points).
            # We should probably merge them or have a separate field.
            
