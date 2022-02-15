from flask.wrappers import Request
import google.cloud.storage
import google.cloud.workflows_v1beta
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions
import json
from os import remove
from uuid import uuid4
from pathlib import Path

# TODO: USE PYDANTIC TO TYPE CHECK THE INPUT

def function_warhall_report(request: Request):
    """Cloud function to handle when warhall game data is provide in a post request

    Args:
        request (Request): post request
    """

    game_data:dict = request.get_json(force=True)

    data = {}
    data["name"] = "warhall"
    data["file_name"] = store_data(game_data)

    project = "ninthage-data-analytics"
    location = "us-central1"
    workflow = "workflow_parse_lists"

    # Set up API clients.
    execution_client = executions_v1beta.ExecutionsClient()
    workflows_client = google.cloud.workflows_v1beta.WorkflowsClient()

    # Construct the fully qualified location path.
    parent = workflows_client.workflow_path(project, location, workflow)
    execution = executions.Execution(argument=json.dumps(data))
    print(f"{data=}")

    # Execute the workflow.
    response = execution_client.create_execution(parent=parent, execution=execution)
    print(f"Created execution: {response.name}")

    return 200


def upload_blob(bucket_name:str, file_path:str, destination_blob_name:str) -> None:
    """Uploads a file to the bucket."""
    storage_client = google.cloud.storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)

    print("File {} uploaded to {}.".format(destination_blob_name, bucket_name))


def write_report_to_json(file_path: Path, data: dict):
    with open(file_path, "w") as jsonFile:
        jsonFile.write(json.dumps(data))

def store_data(data:dict) -> str:
    file_name = Path(str(uuid4()) + ".json")
    local_file = "/tmp" / file_name
    write_report_to_json(file_path=local_file, data=data)

    bucket_name = "warhall"
    upload_blob(bucket_name=bucket_name, file_path=str(local_file), destination_blob_name=str(file_name))
    remove(local_file)
    return str(file_name)




if __name__ == "__main__":
    pass
