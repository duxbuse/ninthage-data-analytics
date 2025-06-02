import json
from datetime import datetime
from os import remove, environ
from typing import Optional

import google.cloud.storage
import google.cloud.workflows_v1beta
import jsons
import requests
from dateutil.relativedelta import relativedelta
from flask.wrappers import Request
from google.cloud.workflows import executions_v1beta
from google.cloud.workflows.executions_v1beta.types import executions
from pydantic import BaseModel, Field, validator

http = requests.Session()

# -----------------
# Tournaments Data
# -----------------


class country_data(BaseModel):
    name: str  #'Online'
    id: str = Field(..., alias="_id")  #'616923ecad6fdb296244eff0'
    flag: str  #'🌍'

class extra_points(BaseModel):
    reason: str
    amount: int
    stage: Optional[int]
    pairings: Optional[bool]

class player(BaseModel):
    name: str
    lists: list[str]

class team(BaseModel):
    id: Optional[str] # = Field(..., alias="_id")  #'61f9392492696257cf835c85'
    name: str
    status: Optional[int]
    id_captain: Optional[str]  #'5de7603e29951610d11f7401'
    players: list[player]
    extra_points: Optional[list[extra_points]]


class tournaments_data(BaseModel):
    id: str #_id '61f9392492696257cf835c85'
    name: str  #'Prueba 2'
    short: Optional[str]  #'Prueba 2'
    participants_per_team: Optional[int]  # 8
    team_proposals: Optional[int]  # 2
    team_point_cap: Optional[int]  # 100
    team_point_min: Optional[int]  # 60
    teams: Optional[list[team]]
    rounds: Optional[list[dict]]
    showlists: bool  # False
    type: int  # 0=singles, 1=teams
    currentRound: Optional[int]  # 1
    country: Optional[country_data]
    visibility: int  # 0

class data_to_store(BaseModel):
    name: str
    games: list[dict]
    country_name: str
    country_flag: str
    participants_per_team: Optional[int]
    team_point_cap: Optional[int]
    team_point_min: Optional[int]
    type: int
    teams: Optional[list[team]]
    rounds: Optional[int]

class tournament(BaseModel):
    id: str = Field(..., alias="_id")  #'61f9392492696257cf835c85'
    name: str  #'Prueba 2'
    start: str  #'2022-02-01T10:45:49.578Z'
    end: str  #'2022-02-01T10:45:49.578Z'
    status: int  # 1=OPEN, 2=ONGOING, 3=CLOSED

class tournaments_response(BaseModel):
    tournaments: list[tournament]
    total: int

def get_cred_config() -> dict[str, str]:
    """Retrieve Cloud SQL credentials stored in Secret Manager
    or default to environment variables.

    Returns:
        A dictionary with Cloud SQL credential values
    """
    secret = environ.get("NR_CREDENTIALS_SECRET")
    if secret:
        print(f"NR_CREDENTIALS_SECRET a été chargé. Longueur : {len(secret)} caractères.")
        return json.loads(secret)
    else:
        print("Erreur : NR_CREDENTIALS_SECRET n'a PAS été chargé.")
        return {}


def get_tournaments(start: str = "", end: str = "now", page: int = 1) -> list[dict]:
    """Retrieve all tournaments from new recruit server between the inclusive dates

    Args:
        start (str, optional): Start date in the format of "2021-01-01". Defaults to 2 month before end date.
        end (str, optional): End date in the format of "2022-12-31". Defaults to datetime.now().
        page (int, optional): Page number to retrieve. Defaults to 1.

    Returns:
        dict: List of tournament data from the selected period
    """

    if end == "now":
        end = datetime.now().strftime("%Y-%m-%d")

    if start == "":
        start = (
            datetime.strptime(end, "%Y-%m-%d") + relativedelta(months=-2)
        ).strftime("%Y-%m-%d")

    body = {"start": start, "end": end, "page": page, "status": 3, "id_game_system": 6}
    # {"start": "2021-01-01", "end": "2022-12-31"}
    print(f"body: {body}")

    creds = get_cred_config()

    print(f"creds: {creds}")
    print(f"NR-User: {creds["NR_USER"]}")
    print(f"NR-Password: {creds["NR_PASSWORD"]}")
    url = f"https://www.newrecruit.eu/api/tournaments"
    response = requests.post(
        url,
        json=body,
        headers={
            "Accept": "application/json",
            "User-Agent": "ninthage-data-analytics/1.1.0",
            "NR-User": creds["NR_USER"],
            "NR-Password": creds["NR_PASSWORD"],
        },
    )
    data = response.json()
    return data

def get_tournament(id) -> tournaments_data:
    """Retrieve a tournament from new recruit server with the given id

    Args:
        id (str): Tournament identifier

    Returns:
        dict: tournament data with the given id
    """
    creds = get_cred_config()

    body = {"id": id}

    url = f"https://www.newrecruit.eu/api/tournament"
    response = requests.post(
        url,
        json=body,
        headers={
            "Accept": "application/json",
            "User-Agent": "ninthage-data-analytics/1.1.0",
            "NR-User": creds["NR_USER"],
            "NR-Password": creds["NR_PASSWORD"],
        },
    )
    data = response.json()
    print(f"tournament: {data}")

    return tournaments_data(id=id, name=data["name"], type=data["type"], teams=data["teams"], showlists=data["showlists"], visibility=data["visibility"])

def get_tournament_games(tournament_id: str) -> list[dict]:
    """Retrieve all games from new recruit server for a tournament"""

    creds = get_cred_config()

    body = {"id_tournament": tournament_id}
    url = f"https://www.newrecruit.eu/api/reports"
    response = requests.post(
        url,
        json=body,
        headers={
            "Accept": "application/json",
            "User-Agent": "ninthage-data-analytics/1.1.0",
            "NR-User": creds["NR_USER"],
            "NR-Password": creds["NR_PASSWORD"],
        },
    )
    data = response.json()
    return data


def function_new_recruit_tournaments(request: Request):
    # Example for testing on the console: # {"start": "2021-01-01", "end": "2022-12-31"}
    start: str = "" #format - "2022-12-31"
    end: str = "now"

    if request.json:
        if "start" in request.json:
            start = request.json["start"]
        if "end" in request.json:
            end = request.json["end"]

    page = 1
    all_events = []

    while True:
        tournament_list = get_tournaments(start=start, end=end, page=page)
        print(f"tournament_list: {tournament_list}")
        events = tournaments_response(tournaments=tournament_list['tournaments'], total=tournament_list['total'])
        print(f"Page {page}: {len(events.tournaments)} tournois trouvés / {events.total}.")

        all_events.extend(events.tournaments)

        # Check if all tournaments have been loaded
        if len(all_events) >= events.total:
            print(f"All tournaments have been loaded ({len(all_events)}/{events.total}).")
            break

        # If last page empty => Stop
        if not tournament_list or not any(events.tournaments):
            print("No Tournament to load.")
            break

        # Passer à la page suivante
        page += 1


    project = "ninthage-data-analytics"
    location = "us-central1"
    workflow = "workflow_parse_lists"

    # Set up API clients.
    execution_client = executions_v1beta.ExecutionsClient()
    workflows_client = google.cloud.workflows_v1beta.WorkflowsClient()

    # Construct the fully qualified location path.
    parent = workflows_client.workflow_path(project, location, workflow)

    errors = []
    events_proccessed = 0
    summary_of_events = [{x.id: x.name} for x in all_events]
    print(f"Processing {len(all_events)} tournaments\n{summary_of_events=}")

    no_games_played = 0

    for event in all_events:
        tournament = get_tournament(event.id)
        print(f"tournament: {tournament}")

        data = data_to_store(
            name=event.name
            or event.short
            or f"New Recruit Tournament - ${event.id}",
            games=get_tournament_games(event.id),
            country_name="", #tournament.country.name if tournament.country else "",
            country_flag="", #tournament.country.flag if tournament.country else "",
            participants_per_team=0, #tournament.participants_per_team,
            team_point_cap=0, #tournament.team_point_cap,
            team_point_min=0, #tournament.team_point_min,
            type=tournament.type,
            teams=tournament.teams,
            rounds=len(tournament.rounds or []),
            )
        
        if not data.games: #Skip events that have no games played
            no_games_played += 1
            print(f"Skipping {event.name} because it has no games played")
            continue
        try:
            stored_data = store_data(data=data, event_id=event.id)
        except jsons.exceptions.SerializationError as e:
            print(f"Error serializing data for event {event.id}\n{data=}")
            errors.append(e)
            continue
        execution = executions.Execution(argument=jsons.dumps(stored_data))

        # Execute the workflow.
        response = execution_client.create_execution(parent=parent, execution=execution)
        print(f"Event: {event.id}, Created execution: {response.name}")
        events_proccessed += 1

    if errors:
        print(f"{no_games_played=}, {events_proccessed=}, {start=}, {end=}, {errors=}")
        return f"{events_proccessed} events found with {len(errors)}\nErrors: {str(errors)}", 400

    print(f"{no_games_played=}, {events_proccessed=}, {start=}, {end=}, {errors=}")
    return f"{events_proccessed} events found from {start} to {end}.", 200


def upload_blob(bucket_name: str, file_path: str, destination_blob_name: str) -> None:
    """Uploads a file to the bucket."""
    storage_client = google.cloud.storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)

    print("File {} uploaded to {}.".format(destination_blob_name, bucket_name))


def write_report_to_json(file_path: str, data: dict):
    with open(file_path, "w") as jsonFile:
        sdata = jsons.dumps(data)
        jsonFile.write(sdata)


def store_data(data: data_to_store, event_id: str) -> dict:
    if __name__ == "__main__":
        local_file = "test-" + event_id
    else:
        local_file = "/tmp/" + event_id

    write_report_to_json(file_path=local_file, data=data.dict())

    bucket_name = "newrecruit_tournaments"
    upload_blob(
        bucket_name=bucket_name, file_path=local_file, destination_blob_name=event_id
    )
    remove(local_file)
    return {"name": "newrecruit_tournament.json", "event_id": event_id}


if __name__ == "__main__":
    #first t9a game was 2021-07-10.
    test_data = {"start": "2024-07-01", "end": "2024-10-01"}
    request_obj = Request.from_values(json=test_data)
    print(function_new_recruit_tournaments(request_obj))
