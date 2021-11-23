from typing import List
import uuid
import jsons
from pathlib import Path
from parser_protocol import Parser
from new_recruit_parser import new_recruit_parser
from datetime import datetime
from data_classes import (
    ArmyEntry,
    Parsers,
    Event_types,
    Army_names
)
from utility_functions import (
    Docx_to_line_list,
    DetectParser,
    Is_int
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
    #     pass
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
    ingest_date = datetime.now()
    list_of_armies = []
    for armylist in armyblocks:
        army = parser.parse_block(armylist)
        army.ingest_date = ingest_date
        army.event_size = len(armyblocks)
        army.player_name = armylist[0]
        army.calculate_total_points()
        army.tournament = tournament_name

        # TODO: these are all being hardcoded until real ways of calculating them are found
        army.validated = False
        army.list_placing = -1  # Should be pulled from the info table
        # Should be pulled from the info table
        army.event_date = datetime(1970, 1, 1)# Should be pulled from the info table
        # Should be pulled from the info table
        army.event_type = Event_types.SINGLES  # Should be pulled from the info table

        list_of_armies.append(army)

    return list_of_armies


def Write_army_lists_to_json_file(file_path: Path, list_of_armies: List[ArmyEntry]) -> None:
    """Takes a list of army lists and a file path and writes the list of armies in json new line delimited to the filepath

    Args:
        file_path (string): path to write new file to
        list_of_armies (list[ArmyEntry]): list of ArmyEntry objects to be written to file
    """
    with open(file_path, "w") as jsonFile:

        for army in list_of_armies:
            army_as_string = jsons.dumps(army) + '\n'
            if "null" in army_as_string:
                jsonFile.close
                raise ValueError(
                    f"Invalid List for Player: {army.player_name}, playing: {army.army} for event: {file_path}")
            else:
                jsonFile.write(army_as_string)


if __name__ == "__main__":
    """Used for testing locally
    """
    for i in range(1, 6):

        filePath = Path(f"data/Round {i}.docx")

        print(f"Input filepath = {filePath}")
        list_of_armies = Convert_docx_to_list(filePath)
        new_path = filePath.parent / (filePath.stem + ".json")

        Write_army_lists_to_json_file(new_path, list_of_armies)
