import google.cloud.workflows_v1beta
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions
import json

# name of the function in main.py must equal the trigger name as a default or be set explicitly


import functions_framework

# name of the function in main.py must equal the trigger name as a default or be set explicitly
@functions_framework.cloud_event
def function_data_ingestion(cloud_event) -> None:
    data = cloud_event.data
    
    print(f"data = {data}")
    
    # CloudEvent data (google.cloud.storage.object.v1.finalized) has 'bucket' and 'name'
    # The workflow expects 'data' object with these fields or just passes them?
    # Original code: execution = executions.Execution(argument=json.dumps(data))
    # Original data was 'data' and 'context'. 
    # Cloud Storage gen 1 event 'data' is the object metadata.
    # CloudEvent data is also object metadata.
    
    # We pass 'data' to the workflow.
    # Ensure what we pass matches what workflow expects.
    # Workflow input: params: [input]
    # Ingestion passes 'data'.
    
    # Let's pass the whole event data payload.

    print(f"data = {data}")
    project = "ninthage-data-analytics"
    location = "us-central1"
    workflow = "workflow_parse_lists"

    # Set up API clients.
    execution_client = executions_v1beta.ExecutionsClient()
    workflows_client = google.cloud.workflows_v1beta.WorkflowsClient()

    # Construct the fully qualified location path.
    parent = workflows_client.workflow_path(project, location, workflow)
    execution = executions.Execution(argument=json.dumps(data))

    # Execute the workflow.
    response = execution_client.create_execution(parent=parent, execution=execution)
    print(f"Created execution: {response.name}")


if __name__ == "__main__":
    function_data_ingestion()
