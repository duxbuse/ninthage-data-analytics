from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import requests
from functools import cache
from multi_error import Multi_Error
from converter import Convert_lines_to_army_list
from data_classes import (
    Round,
    Event_types,
    Data_sources,
    ArmyEntry,
)


http = requests.Session()

# -----------------------
# Specific Tournament Data
# -----------------------


class elo(BaseModel):
    friendly: float  # 23.664319132398465
    tourny: float  # 23.664319132398465
    # legaueid: int #this league id is a hex string and represents a collection of tournaments, but basically you get 3 elo's


class player(BaseModel):
    alias: Optional[str]  #'Juan'
    id_member: str
    id_list: Optional[str]
    id_book: Optional[int]  # 8
    id_participant: str  #'619b6074bf3fd75cf2fb9a54',
    exported_list: str
    name: str
    elo: Optional[elo]  # Can be None if unknown


class setup(BaseModel):
    map: int
    deployment: int
    objective: int


class score(BaseModel):
    VP: int
    Diff: int
    Obj: Optional[int]
    Turns: Optional[int]
    BP: int
    BPObj: int


class tournament_game(BaseModel):
    id: str = Field(..., alias="_id")
    submitter_id: str  #'5de7603e29951610d11f7401'
    type: int  # 1
    date: str  #'2021-11-27T00:00:00.000Z'
    id_tourny: str  #'619224dbc77ccb1989c33cba'
    id_match: str  #'61a25160d7c66d711486cc19'
    setup: setup
    id_game_system: int  # 5
    players: list[player]
    score: list[score]
    confirmation_id: Optional[str]  #'5ec2c7e1085a32315343473a'
    first_turn: Optional[int]


class extra_points(BaseModel):
    reason: str
    amount: int
    stage: int
    pairings: bool


class team(BaseModel):
    id: str = Field(..., alias="_id")  #'61f9392492696257cf835c85'
    name: str
    id_captain: Optional[str]  #'5de7603e29951610d11f7401'
    participants: list[str]
    extra_points: Optional[list[extra_points]]


class single_event(BaseModel):
    name: str
    games: list[tournament_game]

    country_name: Optional[str]
    country_flag: Optional[str]
    participants_per_team: int
    team_point_cap: Optional[int]  # 100
    team_point_min: Optional[int]  # 60
    teams: Optional[list[team]]
    rounds: Optional[int] #3
    type: int  # 0=singles, 1=teams


class unique_players(dict):
    players: dict[str, player]


# ---------------------------
# NEW RECRUIT LIBRARY DATA
# ---------------------------

# Map Data
class nr_library_map_items(BaseModel):
    id: int
    ord: int
    name: str


class nr_library_map(BaseModel):
    id: str
    name: str
    id_game_system: str
    items: list[nr_library_map_items]


# Deployment Data
class nr_library_deployment_items(BaseModel):
    id: int
    ord: int
    name: str


class nr_library_deployment(BaseModel):
    id: str
    name: str
    id_game_system: str
    items: list[nr_library_deployment_items]


# Objective Data
class nr_library_objective_items(BaseModel):
    id: int
    ord: int
    name: str


class nr_library_objective(BaseModel):
    id: str
    name: str
    id_game_system: str
    items: list[nr_library_objective_items]


# Base Objects
class nr_library_setup_categories(BaseModel):
    map: nr_library_map
    deployment: nr_library_deployment
    objective: nr_library_objective


class nr_library_entry(BaseModel):
    id: int
    name: str
    version: Optional[str]
    setup_categories: Optional[nr_library_setup_categories]


class nr_library(BaseModel):
    __root__: list[nr_library_entry]


@cache
def get_NR_library(id_game_system: int) -> nr_library_entry:

    url = f"https://www.newrecruit.eu/api/rpc?m=get_library"
    response = requests.get(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ninthage-data-analytics/1.1.0",
        },
    )
    data = response.json()

    library = nr_library(__root__=data)

    for entry in library.__root__:
        if entry.id == id_game_system:
            return entry

    raise ValueError(f"No library entry found for id_game_system: {id_game_system}")

def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)

def calculate_placing(data: dict[ArmyEntry], teams: list[team], rounds: int) -> list[ArmyEntry]:
    """
    logic here is to loop over each team and calculate how the team performed given there are soft points and also points caps per round
    """
    for team in teams:
        if team.extra_points is not None:
            team_total_tournament_points = sum([x.amount for x in team.extra_points]) #add in soft points
        else:
            team_total_tournament_points = 0
        team_total_secondary_points = 0

        for round in range(rounds):
            round_total_tournament_points = 0
            round_total_secondary_points = 0

            for player in team.participants:
                if player in data and round <= len(data[player].round_performance)-1:
                    round_total_tournament_points += data[player].round_performance[round].result
                    round_total_tournament_points = clamp(round_total_tournament_points, data[player].team_point_cap_min, data[player].team_point_cap_max)
                    round_total_secondary_points += data[player].round_performance[round].secondary_points

            team_total_tournament_points += round_total_tournament_points
            team_total_secondary_points += round_total_secondary_points

        for player in team.participants:
            if player in data:
                data[player].team_total_tournament_points = team_total_tournament_points
                data[player].team_total_secondary_points = team_total_secondary_points
    sorted_armies = list(list(zip(*sorted(data.items(), key=lambda x: (x[1].team_total_tournament_points, x[1].team_total_secondary_points), reverse=True)))[1])
    for army in sorted_armies:
        army.team_placing = sorted_armies.index(army) + 1

    return sorted_armies


def armies_from_NR_tournament(stored_data: dict) -> list[ArmyEntry]:
    event_data = single_event(**stored_data)

    # get list of unique players and their army lists {player_id: player}
    player_list = unique_players()
    for tournament_game in event_data.games:
        for player in tournament_game.players:
            player_list[player.id_participant] = player

    # create list of ArmyEntry objects for each player
    armies: list[ArmyEntry] = []
    duplicate_player_list = (
        player_list.copy()
    )  # we copy the list so we have a unique list of players as the keys, and then we go through replacing the value with an ARMY Entry object
    for player in player_list.values():
        armies = Convert_lines_to_army_list(
            event_data.name, player.exported_list.split("/n"), http
        )
        if len(armies) == 1:
            army = armies[0]
        else:
            raise Multi_Error(
                [ValueError(f"0 or 2+ armies found for player {player.id_participant}")]
            )

        army.player_name = player.alias
        army.event_date = datetime.strptime(
            event_data.games[0].date, "%Y-%m-%dT%H:%M:%S.%fZ"
        )  # TODO: '2022-04-05T09:35:58.822Z' check this format is right
        if event_data.type == 1:
            army.event_type = Event_types.TEAMS
            army.participants_per_team = event_data.participants_per_team
            army.team_point_cap_max = event_data.team_point_cap
            army.team_point_cap_min = event_data.team_point_min
            # find which team the participant belongs to and save if the captain
            for team in event_data.teams if event_data.teams else []:
                for person in team.participants:
                    if person == player.id_participant:
                        army.team_id = team.id
                        if team.id_captain and team.id_captain == player.id_participant:
                            army.team_captain = True
                        break
                else:  # if 2nd loop runs without hitting the break then continue to the next team
                    continue
                break  # default case is to then call another break to get out of the outer loop
            else:
                raise ValueError(f"No team found for player {player.id_participant}")
        else:
            army.event_type = Event_types.SINGLES

        army.event_size = len(player_list)
        army.data_source = Data_sources.NEW_RECRUIT
        army.validated = True
        army.country_name = event_data.country_name
        army.country_flag = event_data.country_flag

        army.calculate_total_points()
        army.calculate_total_tournament_points()

        duplicate_player_list[player.id_participant] = army

    # append round performance
    for tournament_game in event_data.games:
        library_data = get_NR_library(tournament_game.id_game_system)

        for i, player in enumerate(tournament_game.players):
            new_round = Round()
            # first turn?
            if i == tournament_game.first_turn:
                new_round.first_turn = True

            # Opponent, typing is all borked, cause dict is a copy but then we re write each value to be an armyEntry
            new_round.opponent = duplicate_player_list[
                tournament_game.players[i - 1].id_participant
            ].army_uuid

            # Won secondary objective
            if tournament_game.score[i].BP <= tournament_game.score[i].BPObj:
                new_round.won_secondary = False
            elif tournament_game.score[i].BP > tournament_game.score[i].BPObj:
                new_round.won_secondary = True

            # Save result
            new_round.result = tournament_game.score[i].BPObj

            # Save points
            new_round.secondary_points = tournament_game.score[i].VP

            # Save setup data
            if library_data.setup_categories:
                new_round.map_selected = (
                    [
                        x.name
                        for x in library_data.setup_categories.map.items
                        if x.id == tournament_game.setup.map
                    ]
                    .pop()
                    .replace("map", "")
                    .strip()
                )
                new_round.deployment_selected = [
                    x.name
                    for x in library_data.setup_categories.deployment.items
                    if x.id == tournament_game.setup.deployment
                ].pop()
                new_round.objective_selected = [
                    x.name
                    for x in library_data.setup_categories.objective.items
                    if x.id == tournament_game.setup.objective
                ].pop()

            # Append round
            try:
                duplicate_player_list[player.id_participant].round_performance.append(
                    new_round
                )
            except AttributeError:
                duplicate_player_list[player.id_participant].round_performance = [
                    new_round
                ]

    # list of all armyEntries from duplicate list that have round performance data
    return calculate_placing(data=duplicate_player_list, teams=event_data.teams, rounds=event_data.rounds)


if __name__ == "__main__":

    body = {"id_tournament": "62606316c4babc7434f760c4"}

    url = f"https://api.newrecruit.eu/api/reports"
    response = requests.post(
        url,
        json=body,
        headers={
            "Accept": "application/json",
            "User-Agent": "ninthage-data-analytics/1.1.0",
        },
    )  # need to blank the user agent as the default is automatically blocked
    data = response.json()
    stored_data = {
        "name": "MAPM Mai 3 Player Team",
        "games": data,
        "country_name": "Germany",
        "country_flag": "🇩🇪",
        "participants_per_team": 3,
        "team_point_cap": 45,
        "team_point_min": 15,
        "type": 1,
        "rounds": 3,
        "teams": [
            {
                "_id": "626f988e1508e850435e3266",
                "name": "Jackass",
                "password": "43dd1740e939160d68573d1bbaf10d3c",
                "status": 0,
                "participants": [
                    "626f988e1508e850435e3265",
                    "62725c5e7d2b567931f5c3a7",
                    "627285ed7d2b567931f5c3d4",
                ],
            },
            {
                "_id": "62703bf11508e850435e335a",
                "name": "Munich Model Movement",
                "password": "a0c1b6bf7d3d9f6c2ce001dfeaa26fa8",
                "status": 0,
                "participants": [
                    "62703bf11508e850435e3359",
                    "627069d21508e850435e3378",
                    "6270def21508e850435e33ad",
                ],
                "extra_points": [
                    {
                        "reason": "Well Painted Army",
                        "amount": 15,
                        "stage": 0,
                        "pairings": False,
                    }
                ],
            },
            {
                "_id": "6270dd651508e850435e33aa",
                "name": "die Simulantenbande",
                "password": "e2fc714c4727ee9395f324cd2e7f331f",
                "status": 0,
                "participants": [
                    "6270dd651508e850435e33a9",
                    "6271619d4d22f9a677e1ebf7",
                    "62730642893b0e1632986cae",
                ],
                "id_captain": "6271619d4d22f9a677e1ebf7",
                "extra_points": [
                    {
                        "reason": "Well Painted Army",
                        "amount": 11,
                        "stage": 0,
                        "pairings": False,
                    }
                ],
            },
            {
                "_id": "627177074d22f9a677e1ec12",
                "name": "Holsteiner Hitzköpfe",
                "password": "5d1f8651864fb1068405fd70b5c67eca",
                "status": 0,
                "participants": [
                    "627177074d22f9a677e1ec11",
                    "6272360d7d2b567931f5c388",
                    "627293927d2b567931f5c3e1",
                ],
                "id_captain": "627177074d22f9a677e1ec11",
                "extra_points": [
                    {
                        "reason": "Well Painted Army",
                        "amount": 11,
                        "stage": 0,
                        "pairings": False,
                    }
                ],
            },
            {
                "_id": "62742da4ad0a874dcdc93804",
                "name": "Rengschburgs Gloria",
                "password": "48598ee283437e810f2f0eb1cf66e217",
                "status": 0,
                "participants": [
                    "62742da4ad0a874dcdc93803",
                    "62743523ad0a874dcdc9380d",
                    "6274c316ad0a874dcdc93850",
                ],
                "extra_points": [
                    {
                        "reason": "Well Painted Army",
                        "amount": 13,
                        "stage": 0,
                        "pairings": False,
                    }
                ],
            },
            {
                "_id": "6274fb61ad0a874dcdc9387b",
                "name": "Es eskaliert eh",
                "password": "9767adc9909f4d9363218e083e5e94d7",
                "status": 0,
                "participants": [
                    "6274fb61ad0a874dcdc9387a",
                    "6278103ff65a49d9a99ed3fa",
                    "627dcaae9c19a4d2e8347bd3",
                ],
            },
            {
                "_id": "62766497e83131cba5282c5b",
                "name": "Rise of the Last Rudi",
                "status": "0",
                "participants": [
                    "62702e0a1508e850435e3343",
                    "62703c941508e850435e335c",
                    "626118e2c4babc7434f760d2",
                ],
                "id_captain": "626118e2c4babc7434f760d2",
                "extra_points": [
                    {
                        "reason": "Well Painted Army",
                        "amount": 15,
                        "stage": 0,
                        "pairings": False,
                    }
                ],
            },
            {
                "_id": "627dbdc99c19a4d2e8347ba7",
                "name": "Placeholder",
                "status": 0,
                "participants": [
                    "627dbde79c19a4d2e8347ba8",
                    "627dbdf59c19a4d2e8347ba9",
                    "627dbdff9c19a4d2e8347baa",
                ],
            },
        ],
    }
    # event_data = single_event(**stored_data)
    armies = armies_from_NR_tournament(stored_data)
    pass
