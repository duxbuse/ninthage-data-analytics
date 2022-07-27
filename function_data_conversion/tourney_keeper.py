import concurrent.futures
import json
import re
from datetime import datetime, timedelta, timezone
from functools import cache
from typing import Dict, List, Tuple, Union
from unicodedata import category
from urllib.parse import quote
from uuid import UUID, uuid4

import requests
from fuzzywuzzy import fuzz
from unidecode import unidecode

from converter import Convert_lines_to_army_list
from data_classes import (Army_names, ArmyEntry, Data_sources, Event_types,
                          Round, Tk_info)

http = requests.Session()

@cache
def get_recent_tournaments() -> List[dict]:
    output = []

    now = datetime.now(timezone.utc)
    year_ago = now - timedelta(days=3 * 365)

    now_str = quote(now.isoformat(timespec="seconds") + "Z", safe="")
    year_ago_str = quote(year_ago.isoformat(timespec="seconds") + "Z", safe="")

    url = f"https://tourneykeeper.net/WebAPI/Tournament/GetTournaments?from={year_ago_str}&to={now_str}"

    try:
        # need to blank the user agent as the default is automatically blocked
        response = http.get(
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
        response = http.post(
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


def Get_games_for_tournament(tourney_id: int) -> Union[list, None]:
    url = f"https://tourneykeeper.net/WebAPI/Game/GetGamesForTournament?tournamentId={tourney_id}"
    try:
        # need to blank the user agent as the default is automatically blocked
        response = http.get(
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
        # remove any games with dodgy results
        data = [game for game in data if result_validation(game)]
        return data
    return None

def result_validation(game: dict) -> bool:
    """Remove game data with either results out side 0-20 or with no playerID's

    Args:
        game (dict): individual game data from TK

    Returns:
        bool: if game is valid
    """
    if not 0 <= game["Player1Result"] <= 20:
        return False
    if not 0 <= game["Player2Result"] <= 20:
        return False
    if not game["Player1Result"] + game["Player2Result"] == 20:
        return False
    if not game.get("Player1Id", 0) > 0:
        return False
    if not game.get("Player2Id", 0) > 0:
        return False
    return True

def Get_tournament_by_name(tournament_name: str) -> Union[Dict, None]:
    recent_tournaments = get_recent_tournaments()
    name_no_punc:str = unidecode(''.join(ch for ch in tournament_name if not category(ch).startswith('P')))
    for tournament in recent_tournaments:
        # Clear punctuation
        tk_name_no_punc:str = unidecode(''.join(ch for ch in tournament.get("Name", "") if not category(ch).startswith('P')))

        # cant be to lax here otherwise "brisy battle 1" will match to "brisy battles 3"
        ratio = fuzz.token_sort_ratio(name_no_punc, tk_name_no_punc)
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
        response = http.get(
            url, headers={"Accept": "application/json", "User-Agent": "ninthage-data-analytics/1.1.0"}, timeout=5
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
    print(f"Failed to download player data for {tournamentPlayerId}")
    return None


def Get_players_names_from_games(games: dict) -> dict:
    """receives a list of Tourney keeper games it then returns a mapping of player name to tourneykeeper id

    Args:
        games (dict): list of tourney keeper games

    Returns:
        Key = tk_player_id
        dict: {1234: {TournamentPlayerId: 5678, Player_name: bob}}
    """
    # iterate over all games and produce list of unique player ids
    unique_player_tkIds = set()
    for game in games:
        unique_player_tkIds.add(game.get("Player1Id"))
        unique_player_tkIds.add(game.get("Player2Id"))

    # iterate over unique player ids and map them to player names
    output = {}


    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for Id in unique_player_tkIds:
            futures.append(
                executor.submit(
                    Get_Player_Army_Details, Id
                )
            )
        for future in concurrent.futures.as_completed(futures):
            details = future.result()
            if details:
                tournament_player_id = details.get("TournamentPlayerId")
                player_name:str = details.get("PlayerName")
                tk_player_id = details.get("PlayerId")
                team_name = details.get("TeamName")
                team_id = details.get("TeamId")
                active = details.get("Active")

                primary_codex = next((x.get("Player1PrimaryCodex") for x in games if x.get("Player1Id") == tournament_player_id), None)
                if primary_codex is None:
                    primary_codex = next((x.get("Player2PrimaryCodex") for x in games if x.get("Player2Id") == tournament_player_id), None)

                dummy_players = r"(player\d+|[Ss]tandin\dg* *|[Bb]ye ?\d+)"
                if re.fullmatch(dummy_players, player_name):
                    # Skip dummy players
                    print(f"Dummy player {player_name} skipped")
                    continue

                output[tk_player_id] = {"TournamentPlayerId": tournament_player_id, "Player_name": player_name, "Primary_Codex": primary_codex, "TeamName": team_name, "TeamId": team_id, "Active": active}
            else:
                raise ValueError(f"Tourney Keeper yielded no data for playerID:{Id}")

    return output


def Convert2_TKid_to_uuid(
    TKID_1: int, TKID_2: int, list_of_armies: List[ArmyEntry]
) -> Tuple[UUID, UUID]:
    army1_uuid = None
    army2_uuid = None

    for army in list_of_armies:
        if TKID_1 == army.tourney_keeper_TournamentPlayerId:
            army1_uuid = army.army_uuid
        if TKID_2 == army.tourney_keeper_TournamentPlayerId:
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

@cache
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
            tourney_keeper_info.get("Start"), "%Y-%m-%dT%H:%M:%S"
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
    tk_info: Tk_info, list_of_armies: List[ArmyEntry]
) -> None:
    if tk_info.game_list and tk_info.player_list:
        # extract TK game results if available
        for game in tk_info.game_list:
            player1 = next( (x for x in tk_info.player_list.values() if x.get("TournamentPlayerId") == game.get("Player1Id")), {})
            player2 = next( (x for x in tk_info.player_list.values() if x.get("TournamentPlayerId") == game.get("Player2Id")), {})

            # Check that non active players have lists. If not skip this game data since only 1 player from the round will be recorded and so averages will be thrown off.
            if not player1.get("Active") and not any(x.player_name == player1.get("Player_name") for x in list_of_armies):
                continue

            if not player2.get("Active") and not any(x.player_name == player2.get("Player_name") for x in list_of_armies):
                continue

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
                army.data_source = Data_sources.TOURNEY_KEEPER
                army.event_date = tk_info.event_date
                army.event_type = tk_info.event_type
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

        if any(e:=[x.player_name for x in list_of_armies if x.calculated_total_tournament_points is None]):
            raise ValueError(f"The following players do not have performance data\n {e}")

        # sort armies based on performance then set the placing based on that order
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

def match_player_to_tk_name(tk_info: Tk_info, army: ArmyEntry) -> None:
    """
    Match the player name to the TK name
    """
    if tk_info.player_list:
        # fuzzy match name from lists file and tourney keeper
        close_matches = [
            (
                item,
                ratio,
            )
            for item in tk_info.player_list.items()
            if (
                ratio := fuzz.token_sort_ratio(item[1]["Player_name"], army.player_name)
            )
            > 50
        ]
        if len(close_matches) > 0:
            sorted_by_fuzz_ratio = sorted(
                close_matches, key=lambda tup: tup[1], reverse=True
            )

            if (
                sorted_by_fuzz_ratio[0][1] != 100
            ):  # only report when there are a few options and the top pick isn't 100
                raise ValueError(
                    f"No perfect matches for '{army.player_name}' in {sorted_by_fuzz_ratio}"
                )

            top_picks = [x for x in sorted_by_fuzz_ratio if x[1] == 100]
            if len(top_picks) > 1:
                # reduce number of top picks down by army played
                top_picks = [
                    x
                    for x in top_picks
                    if Army_names[x[0][1].get("Primary_Codex", army.army).upper()] == army.army
                ]

                if len(top_picks) > 1:
                    raise ValueError(
                        f"These {len(top_picks)} players are indistinguishable: {top_picks}"
                    )
                elif len(top_picks) == 0:
                    raise ValueError(
                        f"None of the tk matches for {army.player_name} played {army.army} as found in the word docx."
                    )
            # set current army to be the top pick
            army.tourney_keeper_TournamentPlayerId = top_picks[0][0][1].get(
                "TournamentPlayerId"
            )
            army.tourney_keeper_PlayerId = top_picks[0][0][0]

        else:
            extra_info = "\n".join(army.list_as_str or "HELP")
            raise ValueError(
                f"""Player: "{army.player_name}" not on TK
                Extra info: {extra_info}"""
            )

def verify_tk_data(army_list: list[ArmyEntry], tk_info: Tk_info):
    if army_list:

        zipped = list(
            zip(
                *[
                    (x.player_name, x.tourney_keeper_TournamentPlayerId)
                    for x in army_list
                    if x.tourney_keeper_TournamentPlayerId
                ]
            )
        )
        if len(zipped) == 2:
            matched_player_names = zipped[0]
            matched_player_tkids = zipped[1]
            # check to make sure that all players are uniquely identified in tk
            if len(set(matched_player_tkids)) != len(matched_player_tkids):
                double_matches = set(
                    [
                        x
                        for x in matched_player_tkids
                        if matched_player_tkids.count(x) > 1
                    ]
                )
                doubles_with_name = set(
                    [
                        x
                        for x in zip(matched_player_names, matched_player_tkids)
                        if x[1] in double_matches
                    ]
                )

                raise(
                    ValueError(
                        f"""Players duplicated in word file and not uniquely mapped to tk:\n {doubles_with_name}"""
                    )
                )

            if (
                tk_info.player_list
                and len(tk_info.player_list) != len(matched_player_tkids)
            ):
                # If we have the player count from TK then we can check that the number of lists we read in are equal
                from_file = [x.player_name for x in army_list]
                from_tk = [x["Player_name"] for x in tk_info.player_list.values()]

                # difference doesn't work here because we are fuzz matching
                unique_from_file = from_file[:]
                unique_from_tk = from_tk[:]
                for x in from_file:
                    for y in from_tk:
                        if fuzz.token_sort_ratio(x, y) == 100:
                            try:
                                unique_from_file.remove(x)
                                unique_from_tk.remove(y)
                            except ValueError:
                                # This happens when there are 2 player names that are the same and so the value can not be removed.
                                # This is already handled above with the message of all duplicated players so does not need handling here
                                pass

                # if all the "missing" tk names are not active then ignore this error
                if any(missing_actives:=[y.get("Player_name") for x in unique_from_tk for y in tk_info.player_list.values() if y.get("Player_name") == x and y.get("Active")]):
                    raise(
                        ValueError(
                            f"Lists read: {len(army_list)}\nActive players on tourneykeeper: {tk_info.player_count}\nPlayers matched: {len(matched_player_tkids)}\nPlayers in file but not TK: {unique_from_file}\nPlayers in TK but not in file: {missing_actives}"
                        )
                    )
        # If we have tk data but zipping player id's failed
        elif tk_info.event_id:
            raise(ValueError(f"No tkdata was loaded into armies"))
    

def armies_from_docx(event_name: str, lines: list[str]) -> List[ArmyEntry]:
    armies = Convert_lines_to_army_list(event_name=event_name, lines=lines)
    tk_info = load_tk_info(event_name)
    if tk_info and tk_info.game_list and tk_info.player_list: #game was found on tk
        for army in armies:
            match_player_to_tk_name(tk_info=tk_info, army=army)
        append_tk_game_data(tk_info=tk_info, list_of_armies=armies)
        verify_tk_data(army_list=armies, tk_info=tk_info)
    return armies

if __name__ == "__main__":
    """Used for testing locally"""
    import os
    from pathlib import Path
    from time import perf_counter

    from utility_functions import Docx_to_line_list


    t1_start = perf_counter()

    path = Path("../data/list-files")

    os.makedirs(os.path.dirname(path / "json"), exist_ok=True)
    for file in os.listdir(path):
        if file.endswith(".docx") and not file.startswith("~$"):
            file_start = perf_counter()
            filePath = Path(os.path.join(path, file))
            event_name = Path(filePath).stem
            print(f"Input filepath = {filePath}")

            lines = Docx_to_line_list(filePath)
            list_of_armies = armies_from_docx(event_name, lines)
            file_stop = perf_counter()
            print(
                f"{len(list_of_armies)} army lists were found in {round(file_stop - file_start)} seconds"
            )
            print(f"Player Name list: {[army.player_name for army in list_of_armies]}")
            if all(x.tourney_keeper_PlayerId for x in list_of_armies):
                print(f"Tk Info loaded")
            else:
                print(f"TK Not loaded")
    t1_stop = perf_counter()
    print(f"Total Elapsed time: {round(t1_stop - t1_start)} seconds")
