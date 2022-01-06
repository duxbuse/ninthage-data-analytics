import google.cloud.workflows_v1beta
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions
from flask.wrappers import Request
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta
import requests
import json

from os import getenv


http = requests.Session()

# name of the function in main.py must equal the trigger name as a default or be set explicitly
def function_fading_flame(request: Request) -> None:

    API_KEY = getenv("API_KEY")

    now = datetime.now()
    since_date = now + relativedelta(months=-1)
    formatted_since_date = since_date.isoformat(timespec="microseconds") + "Z"

    url = f"https://fading-flame.com/match-data?secret={API_KEY}&since={formatted_since_date}"
    response = requests.get(url, timeout=10)
    r = response.json()

    data = r
    # add name so we can tell its fading flame data
    data["name"] = "fading flame"

    project = "ninthage-data-analytics"
    location = "us-central1"
    workflow = "workflow_parse_lists"

    # Set up API clients.
    execution_client = executions_v1beta.ExecutionsClient()
    workflows_client = google.cloud.workflows_v1beta.WorkflowsClient()

    # Construct the fully qualified location path.
    parent = workflows_client.workflow_path(project, location, workflow)
    execution = executions.Execution(argument=json.dumps(r))

    # Execute the workflow.
    response = execution_client.create_execution(parent=parent, execution=execution)
    print(f"Created execution: {response.name}")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # Load all data
    request_obj = Request.from_values(json={"date": "2008-10-31T17:04:32.0000000Z"})
    function_fading_flame(request_obj) # type: ignore
