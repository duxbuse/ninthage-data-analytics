from typing import List
from pathlib import Path
from datetime import datetime, timezone
import concurrent.futures
import requests
from typing import Optional
from multi_error import Multi_Error
from utility_functions import (
    DetectParser,
    Write_army_lists_to_json_file,
    clean_lines,
)
from parser_protocol import Parser
from data_classes import ArmyEntry, Army_names, Tk_info
from ninth_builder import format_army_block
from new_recruit_parser import new_recruit_parser

def Convert_lines_to_army_list(event_name: str, lines: List[str], session: Optional[requests.Session]=None) -> List[ArmyEntry]:
    errors: List[Exception] = []

    army_list: List[ArmyEntry] = []

    cleaned_lines = clean_lines(lines)

    armyblocks = split_lines_into_blocks(cleaned_lines)
    event_size = len(armyblocks)
    ingest_date = datetime.now(timezone.utc)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for block in armyblocks:
            futures.append(
                executor.submit(
                    proccess_block, block, event_size, event_name, ingest_date, session
                )
            )
        for future in concurrent.futures.as_completed(futures):
            try:
                army_list.append(future.result())
            except ValueError as e:
                errors.append(e)

    if len(army_list) == 0:
        errors.append(ValueError(f"No Army lists were found in\n{lines}"))

    if errors:
        raise Multi_Error(errors)

    return army_list


def split_lines_into_blocks(lines: List[str]) -> List[List[str]]:
    """break file lines into army blocks which are still a list of lines

    Args:
        lines (List[str]): lines of a file
    """
    active_block: List[str] = []
    armyblocks = []
    previousLine = ""
    for i, line in enumerate(lines):
        # look for list starting
        found_army_name = Army_names.get(line.upper())
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
            total_points = new_recruit_parser.detect_total_points(line)
            if total_points:
                armyblocks.append(active_block)
                active_block = []
            elif i == len(lines) - 1:
                armyblocks.append(active_block)

        previousLine = line
    return armyblocks


def parse_army_block(
    parser: Parser,
    armyblock: List[str],
    tournament_name: str,
    event_size: int,
    ingest_date: datetime,
) -> ArmyEntry:
    army = parser.parse_block(armyblock)
    army.ingest_date = ingest_date
    army.event_size = event_size
    army.player_name = armyblock[0].strip(" -–")
    army.tournament = tournament_name
    army.list_as_str = "\n".join(armyblock)
    army.calculate_total_points()
    return army

def proccess_block(
    armyblock: List[str],
    event_size: int,
    event_name: str,
    ingest_date: datetime,
    session: Optional[requests.Session]=None,
) -> ArmyEntry:
    # format block TODO: event date is not only from TK how does NR set the date
    formated_block = format_army_block(army_block=armyblock, event_date=Tk_info.event_date, session=session)
    if formated_block and formated_block.formated:
        armyblock = formated_block.formated.split("\n")
    # Select which parser to use
    parser_selected = DetectParser(armyblock)
    # parse block into army object
    army = parse_army_block(
        parser=parser_selected,
        armyblock=armyblock,
        tournament_name=event_name,
        event_size=event_size,
        ingest_date=ingest_date,
    )
    if formated_block:
        army.validated = not formated_block.validation.hasError
        if formated_block.validation.hasError:
            army.validation_errors = [x.message for x in formated_block.validation.errors]
    # save into army list
    return army

if __name__ == "__main__":
    """Used for testing locally"""
    import os
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
            list_of_armies = Convert_lines_to_army_list(event_name, lines)
            new_path = filePath.parent / ("json/" + filePath.stem + ".json")

            Write_army_lists_to_json_file(new_path, list_of_armies)
            file_stop = perf_counter()
            print(
                f"{len(list_of_armies)} army lists written to {new_path} in {round(file_stop - file_start)} seconds"
            )
            print(f"Player Name list: {[army.player_name for army in list_of_armies]}")
            if all(x.tourney_keeper_PlayerId for x in list_of_armies):
                print(f"Tk Info loaded")
            else:
                print(f"TK Not loaded")
    t1_stop = perf_counter()
    print(f"Total Elapsed time: {round(t1_stop - t1_start)} seconds")
