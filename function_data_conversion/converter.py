from typing import List
from pathlib import Path
from datetime import datetime, timezone
from fuzzywuzzy import fuzz


from utility_functions import(
    Docx_to_line_list,
    DetectParser,
    Is_int,
    Write_army_lists_to_json_file
)
from parser_protocol import Parser
from tourney_keeper import (
    load_tk_info,
    append_tk_game_data
)
from data_classes import (
    ArmyEntry,
    Army_names,
    Tk_info,
    Round
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
    else:
        #need to add empty round() object so total object fits bigquery schema
        for army in army_list:
            if not army.round_performance:
                army.round_performance.append(Round())#empty round who references itself

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
            elif line == lines[-1]:
                armyblocks.append(active_block)

        previousLine = line
    return armyblocks


def parse_army_block(parser: Parser, armyblock: List[str], tournament_name: str, event_size: int, ingest_date: datetime, tk_info: Tk_info) -> ArmyEntry:
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
        close_matches = [tk_info.player_list[key]
                         for key in tk_info.player_list if fuzz.token_sort_ratio(key, army.player_name) > 75]
        if len(close_matches) == 1 and len(close_matches[0]) == 1:
            army.tourney_keeper_TournamentPlayerId = close_matches[0][0].get(
                "TournamentPlayerId")
            army.tourney_keeper_PlayerId = close_matches[0][0].get("PlayerId")
        else:
            raise ValueError(
                f"player: \"{army.player_name}\" not found in TK player list: {[*tk_info.player_list]}\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id={tk_info.event_id})")

    return army


if __name__ == "__main__":
    """Used for testing locally
    """
    import os
    from time import perf_counter

    t1_start = perf_counter()

    # To Kill a MoCTing Bird
    # "Brisvegas Battles 3"
    # and file.startswith("Round 2")
    # GTC singles
    # testtesttesttestsetsetset

    path = Path("data/2021 data")
    os.makedirs(os.path.dirname(path / "json"), exist_ok=True)

    for file in os.listdir(path):
        if file.endswith(".docx") and not file.startswith("~$") and file.startswith("VIII Torneo Impriwars.docx"):
            file_start = perf_counter()
            filePath = Path(os.path.join(path, file))

            print(f"Input filepath = {filePath}")
            list_of_armies = Convert_docx_to_list(filePath)
            new_path = filePath.parent / ("json/" + filePath.stem + ".json")

            Write_army_lists_to_json_file(new_path, list_of_armies)
            file_stop = perf_counter()
            print(f"{len(list_of_armies)} army lists written to {new_path} in {round(file_stop - file_start)} seconds")
            print(f"Player Name list: {[army.player_name for army in list_of_armies]}")
    t1_stop = perf_counter()
    print(f"Total Elapsed time: {round(t1_stop - t1_start)} seconds")
