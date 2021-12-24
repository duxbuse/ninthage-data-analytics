from pathlib import Path
import jsons
from typing import List
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from docx.text.paragraph import Paragraph
import re

from parser_protocol import Parser
from data_classes import Parsers
from new_recruit_parser import new_recruit_parser
from data_classes import ArmyEntry


def clean_lines(lines: List[str]) -> List[str]:
    cleaned_lines = []
    for line in lines:
        text = line.strip()  # remove leading and trailing whitespace
        multiple_lines = (
            text.splitlines()
        )  # line break and page break characters are split into separate sections
        for section in multiple_lines:
            if (
                len(section) >= 2
            ):  # hard coded ignore short lines need to handle army short names aka "BH"
                cleaned_lines.append(
                    " ".join(section.split())
                )  # remove weird unicode spaces \xa0
    return cleaned_lines


def Docx_to_line_list(docxFile) -> List[str]:
    # remove hyperlinks as they are treated different to paragraphs especially when that is all that is on the line.
    # This is explained https://github.com/python-openxml/python-docx/issues/85#issuecomment-917134257
    Paragraph.text = property(lambda self: GetParagraphText(self))
    doc = Document(docxFile)

    lines = []  # ALL the text in the file, separated by lines

    par = doc.paragraphs
    for line in par:
        lines.append(line.text)
    return lines


# For avoiding hyperlinks https://github.com/python-openxml/python-docx/issues/85#issuecomment-917134257
def GetParagraphText(paragraph):
    def GetTag(element):
        return "%s:%s" % (element.prefix, re.match("{.*}(.*)", element.tag).group(1))

    text = ""
    runCount = 0
    for child in paragraph._p:
        tag = GetTag(child)
        if tag == "w:r":
            text += paragraph.runs[runCount].text
            runCount += 1
        if tag == "w:hyperlink":
            for subChild in child:
                if GetTag(subChild) == "w:r":
                    text += subChild.text
    return text


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


def Write_army_lists_to_json_file(
    file_path: Path, list_of_armies: List[ArmyEntry]
) -> None:
    """Takes a list of army lists and a file path and writes the list of armies in json new line delimited to the filepath

    Args:
        file_path (string): path to write new file to
        list_of_armies (list[ArmyEntry]): list of ArmyEntry objects to be written to file
    """
    with open(file_path, "w") as jsonFile:

        for army in list_of_armies:

            no_nulls = {k: v for k, v in vars(army).items() if v is not None}
            if no_nulls.get("round_performance"):
                no_nulls["round_performance"] = [
                    {k: v for k, v in vars(x).items() if v is not None}
                    for x in no_nulls["round_performance"]
                ]
            army_as_string = jsons.dumps(no_nulls) + "\n"
            if "null" in army_as_string:  # TODO: need to remove field if null
                jsonFile.close
                raise ValueError(
                    f"""
                    Invalid List - null value found in
                    Army: {army.army}
                    Player: {army.player_name}
                    Tournament: {army.tournament}
                    ArmyString: {army_as_string}
                    """
                )
            else:
                jsonFile.write(army_as_string)
