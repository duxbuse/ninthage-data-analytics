from typing import List
from pathlib import Path
from datetime import datetime, timezone
from fuzzywuzzy import fuzz
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
from tourney_keeper import load_tk_info, append_tk_game_data
from data_classes import ArmyEntry, Army_names, Tk_info
from ninth_builder import format_army_block
from new_recruit_parser import new_recruit_parser

def Convert_lines_to_army_list(event_name: str, lines: List[str], session: Optional[requests.Session]=None) -> List[ArmyEntry]:
    errors: List[Exception] = []

    army_list: List[ArmyEntry] = []
    # TODO: skip this for obviously non tk events like warhall/NR
    try:
        tk_info = load_tk_info(event_name)
    except ValueError as e:
        errors.append(e)
        tk_info = Tk_info()

    cleaned_lines = clean_lines(lines)

    armyblocks = split_lines_into_blocks(cleaned_lines)
    event_size = len(armyblocks)
    ingest_date = datetime.now(timezone.utc)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for block in armyblocks:
            futures.append(
                executor.submit(
                    proccess_block, block, event_size, event_name, ingest_date, tk_info, session
                )
            )
        for future in concurrent.futures.as_completed(futures):
            try:
                army_list.append(future.result())
            except ValueError as e:
                errors.append(e)

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

                errors.append(
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
                                # This is already handeled above with the message of all duplicated players so does not need handeling here
                                pass

                # if all the "missing" tk names are not active then ignore this error
                if any(missing_actives:=[y.get("Player_name") for x in unique_from_tk for y in tk_info.player_list.values() if y.get("Player_name") == x and y.get("Active")]):
                    errors.append(
                        ValueError(
                            f"Lists read: {len(army_list)}\nActive players on tourneykeeper: {tk_info.player_count}\nPlayers matched: {len(matched_player_tkids)}\nPlayers in file but not TK: {unique_from_file}\nPlayers in TK but not in file: {missing_actives}"
                        )
                    )
        # If we have tk data but zipping player id's failed
        elif tk_info.event_id:
            errors.append(ValueError(f"No tkdata was loaded into armies"))
    else:
        errors.append(ValueError(f"No Army lists were found in\n{lines}"))

    try:
        if tk_info.game_list and tk_info.player_list:
            append_tk_game_data(tk_info, army_list)
    except ValueError as e:
        errors.append(e)

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
    tk_info: Tk_info,
) -> ArmyEntry:
    army = parser.parse_block(armyblock)
    army.ingest_date = ingest_date
    army.event_size = event_size
    army.player_name = armyblock[0].strip(" -???")
    army.tournament = tournament_name
    army.list_as_str = "\n".join(armyblock)
    army.calculate_total_points()

    army.event_date = tk_info.event_date
    army.event_type = tk_info.event_type

    # TODO: break this logic out to its own function - TK player matching
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
            extra_info = "\n".join(armyblock)
            raise ValueError(
                f"""Player: "{army.player_name}" not on TK
                Extra info: {extra_info}"""
            )

    return army

def proccess_block(
    armyblock: List[str],
    event_size: int,
    event_name: str,
    ingest_date: datetime,
    tk_info: Tk_info,
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
        tk_info=tk_info,
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

    path = Path("data/list-files")

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
