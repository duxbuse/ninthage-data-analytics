from typing import List
from pathlib import Path
from datetime import datetime, timezone
from fuzzywuzzy import fuzz
from multi_error import Multi_Error
from utility_functions import (
    DetectParser,
    Is_int,
    Write_army_lists_to_json_file,
    clean_lines,
)
from parser_protocol import Parser
from tourney_keeper import load_tk_info, append_tk_game_data
from data_classes import ArmyEntry, Army_names, Tk_info
from ninth_builder import format_army_block

__not_yet_printed_tk_list__ = True


def Convert_lines_to_army_list(event_name: str, lines: List[str]) -> List[ArmyEntry]:
    errors = []

    army_list: List[ArmyEntry] = []

    try:
        tk_info = load_tk_info(event_name)
    except ValueError as e:
        errors.append(e)
        tk_info = Tk_info()

    cleaned_lines = clean_lines(lines)

    armyblocks = split_lines_into_blocks(cleaned_lines)
    ingest_date = datetime.now(timezone.utc)

    for armyblock in armyblocks:
        try:
            # format block
            formated_block = format_army_block(armyblock)
            if formated_block:
                armyblock = formated_block
            # Select which parser to use
            parser_selected = DetectParser(armyblock)
            # parse block into army object
            army = parse_army_block(
                parser=parser_selected,
                armyblock=armyblock,
                tournament_name=event_name,
                event_size=len(armyblocks),
                ingest_date=ingest_date,
                tk_info=tk_info,
            )
            # save into army list
            army_list.append(army)
        except ValueError as e:
            errors.append(e)

    if tk_info.player_count and tk_info.player_count != len(army_list):
        # If we have the player count from TK then we can check that the number of lists we read in are equal
        errors.append(
            ValueError(
                f"""
        Number of lists read: {len(army_list)} did not equal number of players on tourneykeeper: {tk_info.player_count}
        Players read from file: {[x.player_name for x in army_list]}
        Players read from TK: {tk_info.player_list.keys()}
        """
            )
        )

    if errors:
        raise Multi_Error(errors)

    if tk_info.game_list:
        append_tk_game_data(tk_info.game_list, army_list)

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
            if Is_int(line) and 2000 <= int(line) <= 4500:
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
    army.player_name = armyblock[0].strip(" -–")
    army.tournament = tournament_name
    army.calculate_total_points()

    army.event_date = tk_info.event_date
    army.event_type = tk_info.event_type

    if tk_info.player_list:
        # fuzzy match name from lists file and tourney keeper
        close_matches = [
            (tk_info.player_list[key][0], fuzz.token_sort_ratio(key, army.player_name))
            for key in tk_info.player_list
            if fuzz.token_sort_ratio(key, army.player_name) > 50
        ]
        if len(close_matches) > 0:
            sorted_by_fuzz_ratio = sorted(
                close_matches, key=lambda tup: tup[1], reverse=True
            )
            army.tourney_keeper_TournamentPlayerId = sorted_by_fuzz_ratio[0][0].get(
                "TournamentPlayerId"
            )
            army.tourney_keeper_PlayerId = close_matches[0][0].get("PlayerId")
            if (
                len(close_matches) > 1 and sorted_by_fuzz_ratio[0][1] != 100
            ):  # only report when there are a few options and the top pick isnt 100
                print(
                    f"Multiple close matches for {army.player_name} in {sorted_by_fuzz_ratio}"
                )
        else:
            global __not_yet_printed_tk_list__
            extra_info = "\n".join(armyblock)
            if __not_yet_printed_tk_list__:
                __not_yet_printed_tk_list__ = False
                raise ValueError(
                    f"""player: "{army.player_name}" not found in TK player list: {[*tk_info.player_list]}\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id={tk_info.event_id})
                    Extra info: {extra_info}"""
                )
            else:
                raise ValueError(
                    f"""player: "{army.player_name}" also not found in TK player list
                    Extra info: {extra_info}"""
                )

    return army


if __name__ == "__main__":
    """Used for testing locally"""
    import os
    from time import perf_counter
    from utility_functions import Docx_to_line_list

    t1_start = perf_counter()

    # To Kill a MoCTing Bird
    # "Brisvegas Battles 3"
    # and file.startswith("WTC Nations Cup Online 2021.docx")
    # GTC singles
    # data\2021 data\WTC Nations Cup Online 2021.docx

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
    t1_stop = perf_counter()
    print(f"Total Elapsed time: {round(t1_stop - t1_start)} seconds")
