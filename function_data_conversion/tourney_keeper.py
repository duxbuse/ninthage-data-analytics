from datetime import datetime, timezone, timedelta
from typing import List, Dict, Union, Tuple
import requests
from urllib.parse import quote
import json
from uuid import UUID, uuid4
from fuzzywuzzy import fuzz
from data_classes import ArmyEntry, Tk_info, Event_types, Round


def get_recent_tournaments() -> List:
    output = []

    now = datetime.now(timezone.utc)
    year_ago = now - timedelta(days=3 * 365)

    now_str = quote(now.isoformat(timespec="seconds") + "Z", safe="")
    year_ago_str = quote(year_ago.isoformat(timespec="seconds") + "Z", safe="")

    url = f"https://tourneykeeper.net/WebAPI/Tournament/GetTournaments?from={year_ago_str}&to={now_str}"

    try:
        # need to blank the user agent as the default is automatically blocked
        response = requests.get(
            url, headers={"Accept": "application/json", "User-Agent": "ninthage-data-analytics/1.1.0"}, timeout=2
        )
    except requests.exceptions.ReadTimeout as err:
        return []
    if response.status_code != 200:
        return []
    message = response.json()["Message"]
    success = response.json()["Success"]
    if success:
        data = json.loads(message)

        # remove other game systems
        for tournament in data["Tournaments"]:
            if tournament.get("GameSystem") == "The 9th Age":
                output.append(tournament)
        return output
    return []


def Get_active_players(tourney_id: int) -> Union[int, None]:
    url = f"https://tourneykeeper.net/WebAPI/Tournament/GetActivePlayers"
    # need to blank the user agent as the default is automatically blocked
    headers = {
        "Accept": "application/json",
        "User-Agent": "ninthage-data-analytics/1.1.0",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url, json={"Id": tourney_id}, headers=headers, timeout=2
        )
    except requests.exceptions.ReadTimeout as err:
        return None
    if response.status_code != 200:
        return None
    message = response.json()["Message"]
    success = response.json()["Success"]
    if success:
        data = int(message)
        return data
    return None


def Get_games_for_tournament(tourney_id: int) -> Union[Dict, None]:
    url = f"https://tourneykeeper.net/WebAPI/Game/GetGamesForTournament?tournamentId={tourney_id}"
    try:
        # need to blank the user agent as the default is automatically blocked
        response = requests.get(
            url, headers={"Accept": "application/json", "User-Agent": "ninthage-data-analytics/1.1.0"}, timeout=2
        )
    except requests.exceptions.ReadTimeout as err:
        print("This is timing out")
        return None
    if response.status_code != 200:
        return None
    message = response.json()["Message"]
    success = response.json()["Success"]
    if success:
        data = json.loads(message)["Games"]
        return data
    return None


def Get_tournament_by_name(tournament_name: str) -> Union[Dict, None]:
    recent_tournaments = get_recent_tournaments()
    for tournament in recent_tournaments:
        # cant be to lax here otherwise "brisy battle 1" will match to "brisy battles 3"
        ratio = fuzz.token_sort_ratio(tournament_name, tournament.get("Name"))
        if ratio == 100:
            # we have found the tournament
            return tournament
        elif tournament_name in tournament.get("Name"):
            raise ValueError(
                f"Found very similar TK event named: '{tournament.get('Name')}'"
            )
    return None


def Get_Player_Army_Details(tournamentPlayerId: int) -> Union[Dict, None]:
    url = f"https://tourneykeeper.net/WebAPI/TournamentPlayer/GetPlayerArmyDetails?tournamentPlayerId={tournamentPlayerId}"
    try:
        # need to blank the user agent as the default is automatically blocked
        response = requests.get(
            url, headers={"Accept": "application/json", "User-Agent": "ninthage-data-analytics/1.1.0"}, timeout=2
        )
    except requests.exceptions.ReadTimeout as err:
        return None
    if response.status_code != 200:
        return None
    success = response.json()["Success"]
    if success:
        message = response.json()["Message"]
        data = json.loads(message)
        return data
    return None


def Get_players_names_from_games(games: dict) -> dict:
    """receives a list of Tourney keeper games it then returns a mapping of player name to tourneykeeper id

    Args:
        games (dict): list of tourney keeper games

    Returns:
        Key = tk_player_id
        dict: {1234: {TournamentPlayerId: 5678, Player_name: bob}}
    """
    # interate over all games and produce list of unique player ids
    unique_player_tkIds = set()
    for game in games:
        unique_player_tkIds.add(game.get("Player1Id"))
        unique_player_tkIds.add(game.get("Player2Id"))

    # iterate over unique player ids and map them to player names
    output = {}
    for Id in unique_player_tkIds:
        player_details = Get_Player_Army_Details(Id)
        if player_details:
            player_name = player_details.get("PlayerName")
            tk_player_id = player_details.get("PlayerId")
            primary_codex = player_details.get("PrimaryCodex")
            team_name = player_details.get("TeamName")
            team_id = player_details.get("TeamId")

            output[tk_player_id] = {"TournamentPlayerId": Id, "Player_name": player_name, "Primary_Codex": primary_codex, "TeamName": team_name, "TeamId": team_id}
        else:
            print(
                f"Id: {Id} from {unique_player_tkIds}, is not found on TK"
            )  # TODO: there is always a 0 id for some reason

    if len(output) != len(unique_player_tkIds):
        print(f"I think this is fucked")
        # raise ValueError(f"Some TK players have been lost due to similar tkIds")

    return output


def Convert2_TKid_to_uuid(
    TKID_1: int, TKID_2: int, list_of_armies: List[ArmyEntry]
) -> Tuple[UUID, UUID]:
    army1_uuid = None
    army2_uuid = None

    for army in list_of_armies:
        if TKID_1 == army.tourney_keeper_TournamentPlayerId:
            army1_uuid = army.army_uuid
        elif TKID_2 == army.tourney_keeper_TournamentPlayerId:
            army2_uuid = army.army_uuid

    if not army1_uuid:
        player_data = Get_Player_Army_Details(TKID_1)
        raise ValueError(
            f"""
            TK player {player_data.get("PlayerName")}, TKID:{TKID_1}, could not be found in the word doc.
        """
        )
    if not army2_uuid:
        player_data = Get_Player_Army_Details(TKID_2)
        raise ValueError(
            f"""
            TK player {player_data.get("PlayerName")}, TKID:{TKID_2}, could not be found in the word doc.
        """
        )
    return (army1_uuid, army2_uuid)

def load_tk_info(tournament_name: str) -> Tk_info:
    # Pull in data from tourney keeper
    tourney_keeper_info = Get_tournament_by_name(tournament_name)
    if tourney_keeper_info:
        # set event type
        if tourney_keeper_info.get("IsTeamTournament"):
            event_type = Event_types.TEAMS
        else:
            event_type = Event_types.SINGLES

        event_date = datetime.strptime(
            tourney_keeper_info.get("Start"), "%Y-%m-%yT%H:%M:%S"
        ).replace(tzinfo=timezone.utc)
        tournament_games = Get_games_for_tournament(tourney_keeper_info.get("Id"))
        player_list = Get_players_names_from_games(tournament_games)

        player_count = Get_active_players(tourney_keeper_info.get("Id"))

        event_id = tourney_keeper_info.get("Id")
        players_per_team = tourney_keeper_info.get("PlayersPrTeam")

        return Tk_info(
            event_date=event_date,
            event_type=event_type,
            event_id=event_id,
            game_list=tournament_games,
            player_list=player_list,
            player_count=player_count,
            players_per_team=players_per_team,
        )
    return Tk_info()


def append_tk_game_data(
    tournament_games: dict, list_of_armies: List[ArmyEntry]
) -> None:
    # extract TK game results if avaliable
    for game in tournament_games:
        (player1_uuid, player2_uuid) = Convert2_TKid_to_uuid(
            game.get("Player1Id"), game.get("Player2Id"), list_of_armies
        )

        round_number = int(game.get("Round"))
        game_uuid = uuid4()

        player1_result = int(game.get("Player1Result"))
        player2_result = int(game.get("Player2Result"))

        player1_secondary = int(game.get("Player1SecondaryResult"))
        player2_secondary = int(game.get("Player2SecondaryResult"))

        player1_round = Round(
            opponent=player2_uuid,
            result=player1_result,
            secondary_points=player1_secondary,
            round_number=round_number,
            game_uuid=game_uuid,
        )
        player2_round = Round(
            opponent=player1_uuid,
            result=player2_result,
            secondary_points=player2_secondary,
            round_number=round_number,
            game_uuid=game_uuid,
        )

        for army in list_of_armies:
            # TODO: instead of list of armies it should be a dict of armies with the uuid as the key
            if army.army_uuid == player1_uuid:
                if not army.round_performance:
                    army.round_performance = []
                army.round_performance.append(player1_round)
            elif army.army_uuid == player2_uuid:
                if not army.round_performance:
                    army.round_performance = []
                army.round_performance.append(player2_round)

    # Calculate who won
    for army in list_of_armies:
        army.calculate_total_tournament_points()

    # sort armies based on performace then set the placing based on that order
    if all([x.calculated_total_tournament_secondary_points for x in list_of_armies]):
        list_of_armies.sort(
            key=lambda x: (
                x.calculated_total_tournament_points,
                x.calculated_total_tournament_secondary_points,
            ),
            reverse=True,
        )
    else:
        # sometimes secondary points are not recorded and so we can not sort on that field
        list_of_armies.sort(
            key=lambda x: (x.calculated_total_tournament_points,),
            reverse=True,
        )
    for index, army in enumerate(list_of_armies):
        army.list_placing = index + 1  # have to account for 0 index lists
