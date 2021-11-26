from typing import List
from pathlib import Path
from datetime import datetime, timezone

from utility_functions import(
    Docx_to_line_list,
    DetectParser,
    Convert2_TKid_to_uuid,
    Is_int,
    Write_army_lists_to_json_file
)
from parser_protocol import Parser
from tourney_keeper import (
    Get_tournament_by_name,
    Get_games_for_tournament,
    Get_active_players,
    Get_players_names_from_games
)
from data_classes import (
    ArmyEntry,
    Event_types,
    Army_names,
    Round,
    Tk_info
)


def Convert_docx_to_list(docxFilePath) -> List[ArmyEntry]:
    """Read in a .docx file reading in multiple army lists and saving them into a list object

    Args:
        docxFilePath (str): path to .docx file

    Returns:
        List: list of ArmyEntry objects representing all lists in the .docx file
    """
    lines = Docx_to_line_list(docxFilePath)
    filename = Path(docxFilePath).stem

    army_list: List[ArmyEntry] = []

    armyblocks = split_lines_into_blocks(lines)
    tk_info = load_tk_info(filename)
    ingest_date = datetime.now(timezone.utc)

    for armyblock in armyblocks:
        # Select which parser to use
        parser_selected = DetectParser(armyblock)
        # parse block into army object
        army = parse_army_block(parser=parser_selected, armyblock=armyblock, tournament_name=filename, event_size=len(
            armyblocks), ingest_date=ingest_date, tk_info=tk_info)
        # save into army list
        army_list.append(army)

    if tk_info.game_list:
        append_tk_game_data(tk_info.game_list, army_list)

    return army_list


def split_lines_into_blocks(lines: List[str]) -> List[List[str]]:
    """break file lines into army blocks which are still a list of lines

    Args:
        lines (List[str]): lines of a file
    """
    active_block = []
    armyblocks = []
    previousLine = str
    for line in lines:
        # look for list starting
        found_army_name = [
            army.value for army in Army_names if army.value == line]
        if found_army_name:
            if active_block:  # found a new list but haven't ended the old list yet.
                # remove the last line from the old block as its the player name of the new active_block
                previousLine = active_block.pop()
                # end the old block
                armyblocks.append(active_block)

            # start new block including previous lines
            # using previous line as the player name usual precedes the army name
            active_block = [previousLine]

        # storing lines from an active block
        if active_block:
            active_block.append(line)

            # look for list ending
            if Is_int(line) and 2000 <= int(line) <= 4500:
                armyblocks.append(active_block)
                active_block = []

        previousLine = line
    return armyblocks


def parse_army_block(parser: Parser, armyblock: List[str], tournament_name: str, event_size: int, ingest_date: datetime, tk_info: Tk_info) -> ArmyEntry:
    army = parser.parse_block(armyblock)
    army.ingest_date = ingest_date
    army.event_size = event_size
    army.player_name = armyblock[0]
    army.tournament = tournament_name
    army.calculate_total_points()

    army.list_placing = -1  # TODO: actually figure this out  
    army.event_date = tk_info.event_date
    army.event_type = tk_info.event_type
    army.tourney_keeper_id = tk_info.player_list[army.player_name]
    return army


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
            tourney_keeper_info.get("Start"), '%Y-%m-%yT%H:%M:%S').replace(tzinfo=timezone.utc)
        tournament_games = Get_games_for_tournament(tourney_keeper_info.get("Id"))
        player_list = Get_players_names_from_games(tournament_games)

        player_count = Get_active_players(tourney_keeper_info.get("Id"))

        # # check to make sure player counts match on both the file and TK
        # if player_count and player_count != len(armyblocks):
        #     raise ValueError(f"""
        #     TourneyKeeper player count:{player_count} != len(armyblocks):{len(armyblocks)}
        #     For file {tournament_name}
        #     """)

        return Tk_info(event_date=event_date, event_type=event_type, game_list=tournament_games, player_list=player_list, player_count=player_count)
    return Tk_info()


def append_tk_game_data(tournament_games: dict, list_of_armies: List[ArmyEntry]) -> None:
    # extract TK game results if avaliable
    for game in tournament_games:
        (player1_uuid, player2_uuid) = Convert2_TKid_to_uuid(
            game.get("Player1Id"), game.get("Player2Id"), list_of_armies)

        round_number = int(game.get("Round"))

        player1_result = int(game.get("Player1Result"))
        player2_result = int(game.get("Player2Result"))

        player1_secondary = int(game.get("Player1SecondaryResult"))
        player2_secondary = int(game.get("Player2SecondaryResult"))

        player1_round = Round(opponent=player2_uuid, result=player1_result,
                              secondary_points=player1_secondary, round_number=round_number)
        player2_round = Round(opponent=player1_uuid, result=player2_result,
                              secondary_points=player2_secondary, round_number=round_number)

        for army in list_of_armies:
            if army.army_uuid == player1_uuid:
                army.round_performance.append(player1_round)
            elif army.army_uuid == player2_uuid:
                army.round_performance.append(player2_round)


if __name__ == "__main__":
    """Used for testing locally
    """
    # range(1,6)
    # [2]
    for i in [2]:

        filePath = Path(f"data/Brisvegas Battles 3.docx")

        print(f"Input filepath = {filePath}")
        list_of_armies = Convert_docx_to_list(filePath)
        new_path = filePath.parent / (filePath.stem + ".json")

        Write_army_lists_to_json_file(new_path, list_of_armies)
        print(f"Data written to {new_path}")
