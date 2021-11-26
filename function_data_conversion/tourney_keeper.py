import datetime
from typing import List, Dict, Union
import requests
from urllib.parse import quote
import json

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
