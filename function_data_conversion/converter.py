from typing import List
import jsons
from pathlib import Path
from data_classes import ArmyEntry
from utility_functions import Docx_to_line_list, Create_unitEntry_from_line, Is_int


def Convert_docx_to_list(docxFilePath) -> List[ArmyEntry]:
    """Read in a .docx file reading in multiple army lists and saving them into a list object

    Args:
        docxFilePath (str): path to .docx file

    Returns:
        List: list of ArmyEntry objects representing all lists in the .docx file
    """

    # Possible army list strings to look for and to determine that the current line is initiating a list
    armyList = ["Beast Herds", "Dread Elves", "Dwarven Holds", "Daemon Legions", "Empire of Sonnstahl", "Highborn Elves", "Infernal Dwarves", "Kingdom of Equitaine",
                "Ogre Khans", "Orcs and Goblins", "Saurian Ancients", "Sylvan Elves", "Undying Dynasties", "Vampire Covenant", "Vermin Swarm", "Warriors of the Dark Gods",
                "Åsklanders", "Cultists", "Hobgolbins", "Makhar", ]

    curently_parsing_army = False
    previousLine = ''
    list_of_armies = []

    filename = Path(docxFilePath).stem

    lines = Docx_to_line_list(docxFilePath)

    for line in lines:
        if Is_int(line) and 4480 < int(line) <= 4500:
            assert(isinstance(curently_parsing_army, ArmyEntry))
            curently_parsing_army.total_points = int(line)
            list_of_armies.append(curently_parsing_army)
            curently_parsing_army = False
            
        currentArmy = [army for army in armyList if army in line]
        if currentArmy or line == lines[-1]:#if a player forgot to put the total points at the end, we can assume since a new army is starting or we are on the last line that the old one is finished.
            if curently_parsing_army: 
                if line == lines[-1]: #last line is a unit in a list with no total points so we still need to add the unit to the army
                    new_unitEntry = Create_unitEntry_from_line(line)
                    if new_unitEntry:
                        curently_parsing_army.units.append(new_unitEntry)

                curently_parsing_army.calculate_total_points() #no total points were found so calculate it
                list_of_armies.append(curently_parsing_army)
                curently_parsing_army = False #end the current list

            if currentArmy: #if we found a subsequent list then assume the current line is for a new army
                curently_parsing_army = ArmyEntry(tournament=filename, army=currentArmy[0], player_name=previousLine) #start a new list

        elif curently_parsing_army:
            new_unitEntry = Create_unitEntry_from_line(line)
            if new_unitEntry:
                assert(isinstance(curently_parsing_army, ArmyEntry))
                curently_parsing_army.units.append(new_unitEntry)

        previousLine = line  

    return list_of_armies


def Write_army_lists_to_json_file(file_path, list_of_armies) -> None:
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
                raise ValueError(f"Invalid List for Player: {army.player_name}, playing: {army.army}")
            else:
                jsonFile.write(army_as_string)


if __name__ == "__main__":
    """Used for testing locally
    """
    import sys

    if len(sys.argv) > 1:
        filePath = Path(sys.argv[1])
    else:
        filePath = Path("data/Round 6.docx")

    print(f"Input filepath = {filePath}")
    list_of_armies = Convert_docx_to_list(filePath)
    new_path = filePath.parent / (filePath.stem + ".json")

    Write_army_lists_to_json_file(new_path, list_of_armies)
