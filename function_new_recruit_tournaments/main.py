from datetime import datetime
from os import remove
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

    def __len__(self):
        return 0 #some weird shit to make the serialisation work


class team(BaseModel):
    id: str = Field(..., alias="_id")  #'61f9392492696257cf835c85'
    name: str
    id_captain: Optional[str]  #'5de7603e29951610d11f7401'
    participants: list[str]
    extra_points: Optional[list[extra_points]]

    def __len__(self):
        return len(self.participants) #some weird shit to make the serialisation work


class tournaments_data(BaseModel):
    id: str = Field(..., alias="_id")  #'61f9392492696257cf835c85'
    name: str  #'Prueba 2'
    short: Optional[str]  #'Prueba 2'
    participants: int  # 32
    participants_per_team: Optional[int]  # 8
    team_proposals: Optional[int]  # 2
    team_point_cap: Optional[int]  # 100
    team_point_min: Optional[int]  # 60
    teams: Optional[list[team]]
    start: str  #'2022-02-01T10:45:49.578Z'
    end: str  #'2022-02-01T10:45:49.578Z'
    status: int  # 1=OPEN, 2=ONGOING, 3=CLOSED
    showlists: bool  # False
    discord_notify_reports: Optional[bool]  # False
    address: str  #'<p></p>'
    price: Optional[int]  # 15
    currency: str  #'EUR'
    description: str  #'<p></p>'
    rules: str  #'<p></p>'
    tables: int  # 8
    group_size: Optional[int]  # 3, this group data is for events that have group stages then finals
    group_winners: Optional[int]  # 1
    group_win_condition: Optional[int]  # 0
    group_letters: Optional[bool]  # False
    roundNumber: int  # 3
    confirmed_participants: Optional[int]  # 0
    type: int  # 0=singles, 1=teams
    currentRound: Optional[int]  # 1
    country: country_data
    id_game_system: int  # 5 = 9thage 2021, 6 = 9thage 2022
    id_owner: list[str]  # ['601d932bf5fdcf2f56534c4c']
    visibility: int  # 0
    version: int  # 0
    mod_date: str  #'2022-02-01T10:46:00.449Z'

    # If the price is empty it returns '', which is treated as a string, so we must convert back to None
    @validator("price", pre=True)
    def price_validator(cls, v):
        if isinstance(v, str):
            return None
        else:
            return v

    @validator("participants", pre=True)
    def participants_validator(cls, v):
        if isinstance(v, str):
            return 0
        else:
            return v


class get_tournaments_response(BaseModel):
    tournaments: list[tournaments_data]


def get_tournaments(start: str = "", end: str = "now") -> list[dict]:
    """Retrieve all tournaments from new recruit server between the inclusive dates

    Args:
        start (str, optional): Start date in the format of "2021-01-01". Defaults to 1 month before end date.
        end (str, optional): End date in the format of "2022-12-31". Defaults to datetime.now().

    Returns:
        dict: List of tournament data from the selected period
    """

    if end == "now":
        end = datetime.now().strftime("%Y-%m-%d")

    if start == "":
        start = (
            datetime.strptime(end, "%Y-%m-%d") + relativedelta(months=-1)
        ).strftime("%Y-%m-%d")

    body = {"start": start, "end": end}
    # {"start": "2021-01-01", "end": "2022-12-31"}

    url = f"https://api.newrecruit.eu/api/tournaments"
    response = requests.post(
        url,
        json=body,
        headers={
            "Accept": "application/json",
            "User-Agent": "ninthage-data-analytics/1.1.0",
        },
    )
    data = response.json()
    return data


def get_tournament_games(tournament_id: str) -> dict:
    """Retrieve all games from new recruit server for a tournament"""

    body = {"id_tournament": tournament_id}

    url = f"https://api.newrecruit.eu/api/reports"
    response = requests.post(
        url,
        json=body,
        headers={
            "Accept": "application/json",
            "User-Agent": "ninthage-data-analytics/1.1.0",
        },
    )
    data = response.json()
    return data


def function_new_recruit_tournaments(request: Request):
    start: str = "" #format - "2022-12-31"
    end: str = "now"

    if request.json:
        if "start" in request.json:
            start = request.json["start"]
        if "end" in request.json:
            end = request.json["end"]

    tournament_list = get_tournaments(start=start, end=end)
    all_events = get_tournaments_response(tournaments=tournament_list)
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
    print(f"Processing {len(all_events.tournaments)} tournaments")

    not_t9a = 0
    not_closed = 0
    no_games_played = 0

    for event in all_events.tournaments:
        if event.id_game_system not in [5, 6]: #Skip non 9th age events, hardcoded magic numbers for 9thage 2021 and 2022
            not_t9a += 1
            continue
        if event.status != 3: #Event is not closed and so not ready for ingestion, hardcoded magic number for closed
            not_closed += 1
            continue
        data = {
            "name": event.name
            or event.short
            or f"New Recruit Tournament - ${event.id}",
            "games": get_tournament_games(event.id),
            "country_name": event.country.name,
            "country_flag": event.country.flag,
            "participants_per_team": event.participants_per_team,
            "team_point_cap": event.team_point_cap,
            "team_point_min": event.team_point_min,
            "type": event.type,
            "teams": event.teams,
        }
        if not data["games"]: #Skip events that have no games played
            no_games_played += 1
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
        print(f"{not_t9a=}, {not_closed=}, {no_games_played=}, {events_proccessed=}, {start=}, {end=}, {errors=}")
        return f"{events_proccessed} events found with {len(errors)}\nErrors: {str(errors)}", 400

    print(f"{not_t9a=}, {not_closed=}, {no_games_played=}, {events_proccessed=}, {start=}, {end=}, {errors=}")
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
        jsonFile.write(jsons.dumps(data))


def store_data(data: dict, event_id: str) -> dict:
    local_file = "/tmp/" + event_id
    write_report_to_json(file_path=local_file, data=data)

    bucket_name = "newrecruit_tournaments"
    upload_blob(
        bucket_name=bucket_name, file_path=local_file, destination_blob_name=event_id
    )
    remove(local_file)
    return {"name": "newrecruit_tournament.json", "event_id": event_id}


if __name__ == "__main__":
    #first t9a game was 2021-07-10
    test_data = {"start": "2022-07-29", "end": "2022-07-31"}
    request_obj = Request.from_values(json=test_data)
    print(function_new_recruit_tournaments(request_obj))
