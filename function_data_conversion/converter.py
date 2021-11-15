from typing import List
import jsons
from pathlib import Path
from data_classes import ArmyEntry
from utility_functions import Docx_to_line_list, Create_unitEntry_from_line, Is_int


def Convert_docx_to_list(docxFilePath) -> List:
    """Read in a .docx file reading in multiple army lists and saving them into a list object

    Args:
        docxFilePath (str): path to .docx file

    Returns:
        List: list of ArmyEntry objects representing all lists in the .docx file
    """

    # Possible army list strings to look for and to determine that the current line is initiating a list
    armyList = ["Beast Herds", "Dread Elves", "Dwarven Holds", "Daemon Legions", "Empire of Sonnstahl", "Highborn Elves", "Infernal Dwarves", "Kingdom of Equitaine",
                "Ogre Khans", "Orcs and Goblins", "Saurian Ancients", "Sylvan Elves", "Undying Dynasties", "Vampire Covenant", "Vermin Swarm", "Warriors of the Dark Gods"]

    curently_parsing_army = False
    previousLine = ''
    list_of_armies = []

    filename = Path(docxFilePath).stem

    lines = Docx_to_line_list(docxFilePath)

    for line in lines:
        if Is_int(line) and 4480 < int(line) <= 4500:
            curently_parsing_army.total_points = int(line)
            list_of_armies.append(curently_parsing_army)
            curently_parsing_army = False
            
        if curently_parsing_army:
            new_unitEntry = Create_unitEntry_from_line(line)
            curently_parsing_army.units.append(new_unitEntry)
        else:
            currentArmy = [army for army in armyList if army in line]
            if currentArmy:
                curently_parsing_army = ArmyEntry(
                    tournament=filename, army=currentArmy[0], player_name=previousLine, units=[])


        previousLine = line

    return list_of_armies


def Write_army_lists_to_json_file(file_path, list_of_armies):
    """Takes a list of army lists and a file path and writes the list of armies in json new line delimited to the filepath

    Args:
        file_path (string): path to write new file to
        list_of_armies (list[ArmyEntry]): list of ArmyEntry objects to be written to file
    """
    jsonFile = open(file_path, "w")

    for list in list_of_armies:
        jsonFile.write(jsons.dumps(list) + '\n')
    jsonFile.close


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        filePath = Path(sys.argv[1])
    else:
        filePath = Path("data/Round 1.docx")

    print(f"Input filepath = {filePath}")
    list_of_armies = Convert_docx_to_list(filePath)
    new_path = filePath.parent / (filePath.stem + ".json")

    Write_army_lists_to_json_file(new_path, list_of_armies)
