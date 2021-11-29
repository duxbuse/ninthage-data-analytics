from pathlib import Path
import jsons
from typing import List
from docx import Document

from parser_protocol import Parser
from data_classes import Parsers
from new_recruit_parser import new_recruit_parser
from data_classes import (
    ArmyEntry
)


def Docx_to_line_list(docxFile) -> List[str]:
    doc = Document(docxFile)

    lines = []  # ALL the text in the file, separated by lines

    par = doc.paragraphs
    for i in range(len(par)):
        text = par[i].text.strip(' .')
        text = ' '.join(text.split())  # remove weird unicode spaces \xa0
        if len(text) > 2:  # hard coded ignore short lines, need to allow for people whos names are "tom" so must be 3+
            lines.append(text)
    return lines


def DetectParser(armyblock: List[str]) -> Parser:
    # Read through block to determine formatting
    # TODO: currently hardcoded to always use newrecruit
    parser_selected = Parsers.NEW_RECRUIT

    if parser_selected == Parsers.NEW_RECRUIT:
        active_parser = new_recruit_parser()
    # elif parser_selected == Parsers.BATTLE_SCRIBE:
    #     active_parser = battle_scribe_parser() #TODO: need to build a battle scribe parser
    else:
        active_parser = new_recruit_parser()
    return active_parser


def Is_int(n) -> bool:
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


def Write_army_lists_to_json_file(file_path: Path, list_of_armies: List[ArmyEntry]) -> None:
    """Takes a list of army lists and a file path and writes the list of armies in json new line delimited to the filepath

    Args:
        file_path (string): path to write new file to
        list_of_armies (list[ArmyEntry]): list of ArmyEntry objects to be written to file
    """
    with open(file_path, "w") as jsonFile:

        for army in list_of_armies:
            army_as_string = jsons.dumps(army) + '\n'
            army_as_string = army_as_string.replace('"round_performance": []', '"round_performance": [{}]')
            if "null" in army_as_string:
                jsonFile.close
                raise ValueError(f"""
                    Invalid List 
                    Army: {army.army}
                    Player: {army.player_name}
                    Tournament: {army.tournament}
                    """)
            else:
                jsonFile.write(army_as_string)
