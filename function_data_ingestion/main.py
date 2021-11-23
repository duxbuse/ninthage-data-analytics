from google.cloud import workflows_v1beta
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions
import json

# name of the function in main.py must equal the trigger name as a default or be set explicitly


def function_data_ingestion(data: str= "{}", context: str="{}") -> None:

    print(f"data = {data}")
    print(f"context = {context}")

    project = "ninthage-data-analytics"
    location = "us-central1"
    workflow = "workflow_parse_lists"

    # Set up API clients.
    execution_client = executions_v1beta.ExecutionsClient()
    workflows_client = workflows_v1beta.WorkflowsClient()

    # Construct the fully qualified location path.
    parent = workflows_client.workflow_path(project, location, workflow)
    execution = executions.Execution(argument=json.dumps(data))

    # Execute the workflow.
    response = execution_client.create_execution(
        parent=parent, execution=execution)
    print(f"Created execution: {response.name}")


if __name__ == "__main__":
    function_data_ingestion()
