import concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import requests

from data_classes import Army_names, ArmyEntry
from multi_error import Multi_Error
from new_recruit_parser import new_recruit_parser
from ninth_builder import format_army_block
from utility_functions import (Write_army_lists_to_json_file,
                               clean_lines)


def Convert_lines_to_army_list(event_name: str, event_date: Optional[datetime], lines: List[str], session: Optional[requests.Session]=None) -> List[ArmyEntry]:
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
                    proccess_block, block, event_size, event_name, ingest_date, event_date, session
                )
            )
        for future in concurrent.futures.as_completed(futures):
            try:
                army_list.append(future.result())
            except ValueError as e:
                errors.append(e)

    if len(army_list) == 0:
        errors.append(ValueError(f"No Army lists were found in\n{lines}"))

    if b:=[x for x in army_list if not x.army]:
        errors.append(ValueError(f"armylist: {b}\n armylist.army was None"))

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

    if armyblocks == []:
        armyblocks.append(lines)
    return armyblocks


def parse_army_block(
    armyblock: List[str],
    tournament_name: str,
    event_size: int,
    ingest_date: datetime,
) -> ArmyEntry:
    
    army = new_recruit_parser().parse_block(lines=armyblock)
    army.ingest_date = ingest_date
    army.event_size = event_size
    army.player_name = armyblock[0].strip(" -–")
    army.tournament = tournament_name
    army.list_as_str = "\n".join(armyblock[1:]) #ignore player name
    army.calculate_total_points()
    return army

def proccess_block(
    armyblock: List[str],
    event_size: int,
    event_name: str,
    ingest_date: datetime,
    event_date: Optional[datetime],
    session: Optional[requests.Session]=None,
) -> ArmyEntry:
    formated_block = format_army_block(army_block=armyblock, filename=event_name, event_date=event_date, session=session)
    if formated_block and formated_block.formated:
        armyblock = formated_block.formated.split("\n")
    

    # parse block into army object
    army = parse_army_block(
        armyblock=armyblock,
        tournament_name=event_name,
        event_size=event_size,
        ingest_date=ingest_date,
    )
    # Adding in army version info
    if formated_block and formated_block.army and formated_block.army.army_version:
        army.army_version_id = formated_block.army.army_version.id
        army.army_version_name = formated_block.army.army_version.name

    # Adding in validation errors
    if formated_block:
        army.validated = not formated_block.validation.hasError
        if formated_block.validation.hasError:
            army.validation_errors = [x.message for x in formated_block.validation.errors]
    # save into army list
    return army

if __name__ == "__main__":
    """Used for testing locally"""
    lines = "\n<b>Daemon Legions</b><br>690 - Courtesan of Cibaresh, General (Greater Dominion), Wizard Apprentice, Witchcraft, Iron Husk, Hammer Hand, Roaming Hands<br>510 - Omen of Savar, Wizard Apprentice, Divination, Hammer Hand<br>510 - Omen of Savar, Wizard Apprentice, Thaumaturgy, Hammer Hand<br>554 - 23 Lemures, Stiff Upper Lip, Standard Bearer, Champion<br>531 - 22 Lemures, Stiff Upper Lip, Standard Bearer, Champion<br>415 - Possessed Giant, Iron Husk, Mark of the Eternal Champion, Big Brother<br>415 - Possessed Giant, Iron Husk, Mark of the Eternal Champion, Big Brother<br>375 - Blazing Glory, Fly<br>353 - 3 Hoarders, Mirrored Scales, Standard Bearer, Champion<br>4353<br>".split("\n")
    a = Convert_lines_to_army_list(event_name="testevent", event_date=None, lines=lines)

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
            list_of_armies = Convert_lines_to_army_list(event_name=event_name, event_date=None, lines=lines, session=None)
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
