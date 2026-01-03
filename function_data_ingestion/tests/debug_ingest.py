import sys
import os
from unittest.mock import MagicMock

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mocking strategy replicating test_main.py
sys.modules['google.cloud'] = MagicMock()
sys.modules['google.cloud.workflows'] = MagicMock()
sys.modules['google.cloud.workflows_v1beta'] = MagicMock()
sys.modules['google.cloud.workflows.executions_v1beta'] = MagicMock()
sys.modules['google.cloud.workflows.executions_v1beta.types'] = MagicMock()
sys.modules['functions_framework'] = MagicMock()
sys.modules['google.cloud.storage'] = MagicMock()
sys.modules['google.cloud.storage.blob'] = MagicMock()
sys.modules['google.cloud.logging'] = MagicMock()

# Explicitly link v1beta to cloud
import google.cloud
google.cloud.workflows_v1beta = sys.modules['google.cloud.workflows_v1beta']

print("Mocks setup complete. Attempting import...")

try:
    import main
    print("Successfully imported main")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Exception: {e}")
