import datetime
from typing import List, Dict, Union, Tuple
import requests
from urllib.parse import quote
import json
from uuid import UUID
from data_classes import (
    ArmyEntry
)

def get_recent_tournaments() -> List:
    output = []
    
    now = datetime.datetime.now(datetime.timezone.utc)
    year_ago = now - datetime.timedelta(days=1.5*365) #hard coded to look a year and half backwards

    now_str = quote(now.isoformat(timespec='seconds') + 'Z', safe='')
    year_ago_str = quote(year_ago.isoformat(timespec='seconds') + 'Z', safe='')

    url = f"https://tourneykeeper.net/WebAPI/Tournament/GetTournaments?from={year_ago_str}&to={now_str}"

    try:
        response = requests.get(url, headers={"Accept":"application/json", "User-Agent": ""}, timeout=2) #need to blank the user agent as the default is automatically blocked
    except requests.exceptions.ReadTimeout as err:
        return []
    if response.status_code != 200:
        return []
    message = response.json()["Message"]
    data = json.loads(message)

    # remove other game systems
    for tournament in data["Tournaments"]:
        if tournament.get("GameSystem") == "The 9th Age":
            output.append(tournament)
    return output

def Get_active_players(tourney_id: int) -> Union[int, None]:
    url = f"https://tourneykeeper.net/WebAPI/Tournament/GetActivePlayers"
    headers={"Accept":"application/json", "User-Agent": "", "Content-Type": "application/json"} #need to blank the user agent as the default is automatically blocked
    
    try:
        response = requests.post(url, json={"Id": tourney_id}, headers=headers) 
    except requests.exceptions.ReadTimeout as err:
        return None
    if response.status_code != 200:
        return None
    message = response.json()["Message"]
    data = int(message)
    return data

def Get_games_for_tournament(tourney_id: int) -> Union[Dict, None]:
    url = f"https://tourneykeeper.net/WebAPI/Game/GetGamesForTournament?tournamentId={tourney_id}"
    try:
        response = requests.get(url, headers={"Accept":"application/json", "User-Agent": ""}) #need to blank the user agent as the default is automatically blocked
    except requests.exceptions.ReadTimeout as err:
        return None
    if response.status_code != 200:
        return None
    message = response.json()["Message"]
    data = json.loads(message)["Games"]
    return data


def Get_tournament_by_name(tournament_name: str):
    recent_tournaments = get_recent_tournaments()
    for tournament in recent_tournaments:
        if tournament_name in tournament.get("Name"):
            #we have found the tournament
            return tournament
    return None

def Get_Player_Army_Details(tournamentPlayerId: int) -> Union[Dict, None]:
    url = f"https://tourneykeeper.net/WebAPI/TournamentPlayer/GetPlayerArmyDetails?tournamentPlayerId={tournamentPlayerId}"
    try:
        response = requests.get(url, headers={"Accept":"application/json", "User-Agent": ""}) #need to blank the user agent as the default is automatically blocked
    except requests.exceptions.ReadTimeout as err:
        return None
    if response.status_code != 200:
        return None
    message = response.json()["Message"]
    data = json.loads(message)
    return data


def Get_players_names_from_games(games: dict) -> dict:
    # interate over all games and produce list of unique player ids
    unique_player_tkIds = set()
    for game in games:
        unique_player_tkIds.add(game.get("Player1Id"))
        unique_player_tkIds.add(game.get("Player2Id"))

    # iterate over unique player ids and map them to player names
    output = {}
    for Id in unique_player_tkIds:
        player_details = Get_Player_Army_Details(Id)
        player_name = player_details.get("PlayerName")
        output[player_name] = Id

    return output
        

# def Convert2_TKid_to_uuid(TKID_1: int, TKID_2: int, list_of_armies: List[ArmyEntry]) -> Tuple[UUID, UUID]:
#     army1_uuid = None
#     army2_uuid = None

#     player1_details = Get_Player_Army_Details(TKID_1)
#     player1_name = player1_details.get("PlayerName")
#     player2_details = Get_Player_Army_Details(TKID_2)
#     player2_name = player2_details.get("PlayerName")

#     for army in list_of_armies:
#         if player1_name == army.player_name:
#             army1_uuid = army.army_uuid
#         elif player2_name == army.player_name:
#             army2_uuid = army.army_uuid

#     if not army1_uuid:
#         raise ValueError(f"""
#             TK_player_name:{player1_name} could not be found in file {list_of_armies[0].tournament}
#         """)
#     if not army2_uuid:
#         raise ValueError(f"""
#             TK_player_name:{player2_name} could not be found in file {list_of_armies[0].tournament}
#         """)
#     return (army1_uuid, army2_uuid)