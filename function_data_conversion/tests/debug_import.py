import sys
import os
from unittest.mock import MagicMock

# Path setup identical to test
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print(f"Path added: {sys.path[-1]}")
try:
    print("Files in path:", os.listdir(sys.path[-1]))
except Exception as e:
    print(f"Error listing dir: {e}")

# Mock dependencies
import google.cloud.logging
import google.cloud.storage

mock_logging_client = MagicMock()
google.cloud.logging.Client = MagicMock(return_value=mock_logging_client)

mock_storage_client = MagicMock()
google.cloud.storage.Client = MagicMock(return_value=mock_storage_client)

# sys.modules['functions_framework'] = MagicMock() # Let it be real

try:
    import main
    print("Successfully imported main")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Exception: {e}")
