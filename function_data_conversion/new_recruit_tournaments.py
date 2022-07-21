from __future__ import annotations
from typing import Dict, Optional, NewType
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
    alias: Optional[str]  #'phillybyrd'
    id_participant: str
    id_list: Optional[str]
    id_book: Optional[int]  # 8
    id_participant: str  #'619b6074bf3fd75cf2fb9a54',
    exported_list: Optional[str]
    name: Optional[str]  #'Juan'
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
    stage: Optional[int]
    pairings: Optional[bool]


class team(BaseModel):
    def __init__(self, **data): #handle that the id might be "id" or "_id"
        super().__init__(
            id=data.pop("_id", None) or data.pop("id", None),
            **data,
        )
    id: str #'61f9392492696257cf835c85'
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
    rounds: Optional[list] #3
    type: int  # 0=singles, 1=teams


# class unique_players(dict):
#     players: dict[str, player]


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

def calculate_team_placing(data: dict[str, ArmyEntry], teams: list[team], rounds: int) -> None:
    """
    logic here is to loop over each team and calculate how the team performed given there are soft points and also points caps per round
    """
    for team in teams:
        if team.extra_points is not None:
            team_total_tournament_points = sum([x.amount for x in team.extra_points]) #add in soft points
        else:
            team_total_tournament_points = 0
        team_total_secondary_points = 0

        for round in range(len(rounds)):
            round_total_tournament_points = 0
            round_total_secondary_points = 0

            for player in team.participants:
                if player in data and data[player].round_performance and round <= len(data[player].round_performance)-1:
                    round_total_tournament_points += data[player].round_performance[round].result
                    round_total_tournament_points = clamp(round_total_tournament_points, data[player].team_point_cap_min, data[player].team_point_cap_max)
                    round_total_secondary_points += data[player].round_performance[round].secondary_points

            team_total_tournament_points += round_total_tournament_points
            team_total_secondary_points += round_total_secondary_points

        for player in team.participants:
            if player in data:
                data[player].team_total_tournament_points = team_total_tournament_points
                data[player].team_total_secondary_points = team_total_secondary_points

    if not (data and data.items()):
        raise Multi_Error(
                [ValueError(f"No games found for event ")]
            )

    sorted_data = sorted(data.items(), key=lambda x: (x[1].team_total_tournament_points, x[1].team_total_secondary_points), reverse=True)
    sorted_armies = list(list(zip(*sorted_data))[1])
    for army in sorted_armies:
        army.team_placing = sorted_armies.index(army) + 1


def calculate_individual_placing(data: dict[str, ArmyEntry]) -> list[ArmyEntry]:
    if not data:
        return []
    sorted_data = sorted(data.items(), key=lambda x: (x[1].calculated_total_tournament_points, x[1].calculated_total_tournament_secondary_points), reverse=True)
    sorted_armies:list[ArmyEntry] = list(list(zip(*sorted_data))[1])
    for army in sorted_armies:
        army.list_placing = sorted_armies.index(army) + 1
    return sorted_armies

def armies_from_NR_tournament(stored_data: dict) -> list[ArmyEntry]:
    event_data = single_event(**stored_data)


    # get list of unique players and their army lists {player_id: player}
    player_list:dict[str, player] = dict()
    for tournament_game in event_data.games:
        for player in tournament_game.players:
            player_list[player.id_participant] = player

    # create list of ArmyEntry objects for each player
    armies: list[ArmyEntry] = []

    army_dict:dict[str, ArmyEntry] = dict.fromkeys(player_list.keys(), None)

    for player in player_list.values():
        # Handle if no army list was provided
        if player.exported_list:
            try:
                armies = Convert_lines_to_army_list(
                    event_data.name, player.exported_list.split("/n"), http
                )
            except Multi_Error as e:
                # basically skipping the error for now casue we cant change the armylist
                # TODO: make this a validation error
                print(f"Error converting army list for {player.id_participant}: {e}")

            if len(armies) == 1:
                army = armies[0]
            else:
                raise Multi_Error(
                    [ValueError(f"0 or 2+ armies found for player {player.id_participant}")]
                )
        else:
            army = ArmyEntry()

        army.player_name = player.alias
        army.event_date = datetime.strptime(
            event_data.games[0].date, "%Y-%m-%dT%H:%M:%S.%fZ"
        )   
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

        

        army_dict[player.id_participant] = army

    # append round performance
    for tournament_game in event_data.games:
        library_data = get_NR_library(tournament_game.id_game_system)

        for i, player in enumerate(tournament_game.players):
            new_round = Round()
            # first turn?
            if i == tournament_game.first_turn:
                new_round.first_turn = True

            # Opponent, typing is all borked, cause dict is a copy but then we re write each value to be an armyEntry
            new_round.opponent = army_dict[
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
            round_performance = army_dict[player.id_participant].round_performance
            try:
                round_performance.append(
                    new_round
                )
            except AttributeError:
                round_performance = [
                    new_round
                ]

    for army in army_dict.values():
        army.calculate_total_tournament_points()

    if event_data.type == 1: #team event
        # list of all armyEntries from duplicate list that have round performance data
        assert event_data.teams is not None
        assert event_data.rounds is not None
        calculate_team_placing(data=army_dict, teams=event_data.teams, rounds=event_data.rounds)

    return calculate_individual_placing(army_dict)

if __name__ == "__main__":

    import json
    # '[WHTFR] Team - Tournoi Warhall France par equipe 1' - 628b1da77efb5e97e2242694
    # ordu onslaught singles - 6282df1f4485537e8fca47b7
    # Winter is Coming singles - 62341093dd9da21766c3ed48
    # Bighorn GT singles - 6202d66466a3ec2968f61b4b
    # Buckeye battles - singles - 6276dfa3f65a49d9a99ed245
    # The Alpine Grand Tournament - Austrian Singles - 628f71c8e93d8a55fec510a5
    # North American Team Championships 2021 - 61945055989a624fe73e77bc
    event_id = "62947cf2707f76f796db67ed"
    with open(f"../data/nr-test-data/{event_id}.json", "r") as f:
        stored_data =json.load(f)

    armies = armies_from_NR_tournament(stored_data)
    pass
