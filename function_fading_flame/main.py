import google.cloud.workflows_v1beta
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions
import google.cloud.storage
from flask.wrappers import Request
from datetime import datetime
from os import remove
from dateutil.relativedelta import relativedelta
import requests
import json

from os import getenv


http = requests.Session()

# name of the function in main.py must equal the trigger name as a default or be set explicitly
def function_fading_flame(request: Request):

    API_KEY = getenv("API_KEY")

    now = datetime.now()
    since_date = now + relativedelta(months=-1)
    formatted_since_date = since_date.isoformat(timespec="microseconds") + "Z"

    url = f"https://fading-flame.com/match-data?secret={API_KEY}&since={formatted_since_date}"
    
    try:
        
        response = http.get(
            url, headers={"Accept": "application/json", "User-Agent": "ninthage-data-analytics/1.1.0"}, timeout=10
        )
    except requests.exceptions.ReadTimeout as err:
        return "timeout", 400
    if response.status_code != 200:
        return "http status code: ", response.status_code
    
    r = response.json()
    
    
    data = {}
    data["games"] = r
    # add name so we can tell its fading flame data
    data["name"] = "fading flame"

    stored_data = store_data(data)

    project = "ninthage-data-analytics"
    location = "us-central1"
    workflow = "workflow_parse_lists"

    # Set up API clients.
    execution_client = executions_v1beta.ExecutionsClient()
    workflows_client = google.cloud.workflows_v1beta.WorkflowsClient()

    # Construct the fully qualified location path.
    parent = workflows_client.workflow_path(project, location, workflow)
    execution = executions.Execution(argument=json.dumps(stored_data))

    # Execute the workflow.
    response = execution_client.create_execution(parent=parent, execution=execution)
    print(f"Created execution: {response.name}")

    return f"Data from {since_date} to {now} loaded.", 200


def upload_blob(bucket_name:str, file_path:str, destination_blob_name:str) -> None:
    """Uploads a file to the bucket."""
    storage_client = google.cloud.storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)

    print("File {} uploaded to {}.".format(destination_blob_name, bucket_name))


def write_report_to_json(file_path: str, data: dict):
    with open(file_path, "w") as jsonFile:
        jsonFile.write(json.dumps(data))

def store_data(data:dict) -> dict:
    file_name = "fading_flame.json"
    local_file = "/tmp/" + file_name
    write_report_to_json(file_path=local_file, data=data)

    bucket_name = "fading-flame"
    upload_blob(bucket_name=bucket_name, file_path=local_file, destination_blob_name=file_name)
    remove(local_file)
    return {"name": file_name}

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # Load all data
    request_obj = Request.from_values(json={"date": "2008-10-31T17:04:32.0000000Z"})
    function_fading_flame(request_obj) # type: ignore
