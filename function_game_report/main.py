from flask.wrappers import Request
from flask import render_template
from google.cloud import storage
from google.cloud import workflows_v1beta
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions
import json
from uuid import uuid4
from pathlib import Path


def upload_blob(bucket_name, file_path, destination_blob_name) -> None:
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)

    print("File {} uploaded to {}.".format(destination_blob_name, bucket_name))


def write_report_to_json(file_path: Path, report: dict):
    with open(file_path, "w") as jsonFile:
        jsonFile.write(json.dumps(report))

def store_raw_report(report:dict):
    file_name = Path(str(uuid4()))
    local_file = "tmp" / file_name
    write_report_to_json(file_path=local_file, report=report)

    bucket_name = "manual-game-reports"
    upload_blob(bucket_name=bucket_name, file_path=local_file, destination_blob_name=file_name)

def function_game_report(request: Request):
    form_data = request.form.to_dict(flat=False)
    # [('player1_name', 'sean'), ('player1_score', '3'), ('player1_vps', '123'), ('player1_army', 'abc'), ('player2_name', 'courtney'), ('player2_score', '17'), ('who_won', 'player2'), ('player2_vps', '456'), ('player2_army', 'def'), ('map_selected', 'Other'), ('deployment_selected', '1 Frontline Clash'), ('objective_selected', '1 Hold the Ground')]

    # adding the file name to the workflow input
    form_data[
        "name"
    ] = "manual game report"  # breaking the typing here but I dont want this last field to be a list but just a string
    print(f"{form_data=}")

    store_raw_report(form_data)

    project = "ninthage-data-analytics"
    location = "us-central1"
    workflow = "workflow_parse_lists"

    # Set up API clients.
    execution_client = executions_v1beta.ExecutionsClient()
    workflows_client = workflows_v1beta.WorkflowsClient()

    # Construct the fully qualified location path.
    parent = workflows_client.workflow_path(project, location, workflow)
    execution = executions.Execution(argument=json.dumps(form_data))

    # Execute the workflow.
    response = execution_client.create_execution(parent=parent, execution=execution)
    print(f"Created execution: {response.name}")

    return render_template("index.html")


if __name__ == "__main__":
    pass
