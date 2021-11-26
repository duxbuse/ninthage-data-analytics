from typing import List
from pathlib import Path
from parser_protocol import Parser
from new_recruit_parser import new_recruit_parser
from tourney_keeper import (
    find_tournament_by_name,
    get_games_for_tournament,
    get_active_players
)
from datetime import datetime, timezone
from data_classes import (
    ArmyEntry,
    Parsers,
    Event_types,
    Army_names,
    Round
)
from utility_functions import (
    Docx_to_line_list,
    DetectParser,
    Is_int,
    convert2_TKid_to_uuid,
    Write_army_lists_to_json_file
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

    parser_selected = DetectParser()
    if parser_selected == Parsers.NEW_RECRUIT:
        active_parser = new_recruit_parser()
    # elif parser_selected == Parsers.BATTLE_SCRIBE:
    #     pass #TODO: need to build a battel scribe parser
    else:
        active_parser = new_recruit_parser()

    # break file into blocks
    active_block = []
    armyblocks = []
    previousLine = str
    for line in lines:
        # look for list starting
        found_army_name = [
            army.value for army in Army_names if army.value in line]
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
            if Is_int(line) and 4480 < int(line) <= 4500:
                armyblocks.append(active_block)
                active_block = []

        previousLine = line

    return parse_army_blocks(active_parser, armyblocks, filename)


def parse_army_blocks(parser: Parser, armyblocks: List[List[str]], tournament_name: str) -> List[ArmyEntry]:
    ingest_date = datetime.now(timezone.utc)
    list_of_armies = []

    # Pull in data from tourney keeper
    tourney_keeper_info = find_tournament_by_name(tournament_name)
    if tourney_keeper_info:
        # set event type
        if tourney_keeper_info.Is_team_tournament:
            event_type = Event_types.TEAMS
        else:
            event_type = Event_types.SINGLES

        event_date = datetime.strptime(
            tourney_keeper_info.Start, '%Y-%m-%yT%H:%M:%S').replace(tzinfo=timezone.utc)
        tournament_games = get_games_for_tournament(tourney_keeper_info.Id)

        player_count = get_active_players(tourney_keeper_info.Id)
        # check to make sure player counts match on both the file and TK
        if player_count and player_count != len(armyblocks):
            raise ValueError(f"""
            TourneyKeeper player count:{player_count} != len(armyblocks):{len(armyblocks)}
            For file {tournament_name}
            """)

    else:  # defaults
        event_type = Event_types.SINGLES
        event_date = datetime(1970, 1, 1, tzinfo=timezone.utc)
        tournament_games = {}

    # extract core information
    for armylist in armyblocks:
        army = parser.parse_block(armylist)
        army.ingest_date = ingest_date
        army.event_size = len(armyblocks)
        army.player_name = armylist[0]
        army.tournament = tournament_name
        army.calculate_total_points()

        army.list_placing = -1  # TODO: actually figure this out
        army.event_date = event_date
        army.event_type = event_type
        army.tourney_keeper_id = -1  # TODO: actually figure this out
        list_of_armies.append(army)

    # extract TK game results if avaliable
    if tournament_games:
        for game in tournament_games:
            (player1_uuid, player2_uuid) = convert2_TKid_to_uuid(
                game.Player1Id, game.Player2Id, list_of_armies)

            round_number = int(game.get("Round"))

            player1_result = int(game.get("Player1Result"))
            player2_result = int(game.get("Player2Result"))

            player1_secondary = int(0)  # TODO: need to figure this out
            player2_secondary = int(0)  # TODO: need to figure this out

            player1_round = Round(opponent=player2_uuid, result=player1_result,
                                  secondary_points=player1_secondary, round_number=round_number)
            player2_round = Round(opponent=player1_uuid, result=player2_result,
                                  secondary_points=player2_secondary, round_number=round_number)

            for army in list_of_armies:
                if army.uuid == player1_uuid:
                    army.round_performance.append(player1_round)
                elif army.uuid == player2_uuid:
                    army.round_performance.append(player2_round)

    return list_of_armies

if __name__ == "__main__":
    """Used for testing locally
    """
    # range(1,6)
    # [2]
    for i in range(5, 6):

        filePath = Path(f"data/Round {i}.docx")

        print(f"Input filepath = {filePath}")
        list_of_armies = Convert_docx_to_list(filePath)
        new_path = filePath.parent / (filePath.stem + ".json")

        Write_army_lists_to_json_file(new_path, list_of_armies)
 