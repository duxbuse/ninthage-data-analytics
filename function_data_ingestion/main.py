import time

from google.cloud import workflows_v1beta
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions

project = 'ninthage-data-analytics'
location = 'us-central1'
workflow = 'parse-lists'

if not project:
    raise Exception('GOOGLE_CLOUD_PROJECT env var is required.')

# Set up API clients.
execution_client = executions_v1beta.ExecutionsClient()
workflows_client = workflows_v1beta.WorkflowsClient()

# Construct the fully qualified location path.
parent = workflows_client.workflow_path(project, location, workflow)

# Execute the workflow.
response = execution_client.create_execution(request={"parent": parent})
print(f"Created execution: {response.name}")

# Wait for execution to finish, then print results.
execution_finished = False
backoff_delay = 1  # Start wait with delay of 1 second
print('Poll every second for result...')
while (not execution_finished):
    execution = execution_client.get_execution(request={"name": response.name})
    execution_finished = execution.state != executions.Execution.State.ACTIVE

    # If we haven't seen the result yet, wait a second.
    if not execution_finished:
        print('- Waiting for results...')
        time.sleep(backoff_delay)
        backoff_delay *= 2  # Double the delay to provide exponential backoff.
    else:
        print(f'Execution finished with state: {execution.state.name}')
        print(execution.result)
        return execution.result