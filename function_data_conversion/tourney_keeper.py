import datetime
from typing import List, Dict
import requests
import json

from requests.api import head

def get_recent_tournaments() -> List:
    now = datetime.datetime.now(datetime.timezone.utc)
    year_ago = now - datetime.timedelta(days=1.5*365)

    now_str = now.isoformat(timespec='seconds') + 'Z'
    year_ago_str = year_ago.isoformat(timespec='seconds') + 'Z'

    url = f"https://tourneykeeper.net/WebAPI/Tournament/GetTournaments?from={year_ago_str}&to={now_str}"
    response = requests.get(url, headers={"Accept":"application/json", "User-Agent": ""}) #need to blank the user agent as the default is automatically blocked
    message = response.json()["Message"]
    data = json.loads(message)

    output = []
    # remove other game systems
    for tournament in data["Tournaments"]:
        if tournament.get("GameSystem") == "The 9th Age":
            output.append(tournament)
    return output

def get_active_players(tourney_id: int) -> int:
    url = f"https://tourneykeeper.net/WebAPI/Tournament/GetActivePlayers"
    headers={"Accept":"application/json", "User-Agent": "", "Content-Type": "application/json"} #need to blank the user agent as the default is automatically blocked
    response = requests.post(url, json={"Id": tourney_id}, headers=headers) 
    message = response.json()["Message"]
    data = int(message)
    return data

def get_games_for_tournament(tourney_id: int) -> Dict:
    url = f"https://tourneykeeper.net/WebAPI/Game/GetGamesForTournament?tournamentId={tourney_id}"
    response = requests.get(url, headers={"Accept":"application/json", "User-Agent": ""}) #need to blank the user agent as the default is automatically blocked
    message = response.json()["Message"]
    data = json.loads(message)
    return data


def find_tournament_by_name(tournament_name: str):
    recent_tournaments = get_recent_tournaments()
    for tournament in recent_tournaments:
        if tournament_name in tournament.get("Name"):
            #we have found the tournament
            return tournament
    return None
