from flask.wrappers import Request
from google.cloud import workflows_v1beta
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions
import json


def function_game_report(request: Request):
    form_data = request.form.to_dict()
    # [('player1_name', 'sean'), ('player1_score', '3'), ('player1_vps', '123'), ('player1_army', 'abc'), ('player2_name', 'courtney'), ('player2_score', '17'), ('who_won', 'player2'), ('player2_vps', '456'), ('player2_army', 'def'), ('map_selected', 'Other'), ('deployment_selected', '1 Frontline Clash'), ('objective_selected', '1 Hold the Ground')]
    print(f"{form_data=}")

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

    return f"{response=}\n{form_data=}", 200


if __name__ == "__main__":
    pass
