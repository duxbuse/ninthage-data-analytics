import jsons
import re
from docx import Document
from dataclasses import dataclass
from pathlib import Path



def docx_to_line_list(docxFile):
    doc = Document(docxFile)

    lines = []  # ALL the text in the file, separated by lines

    par = doc.paragraphs
    for i in range(len(par)):
        text = par[i].text
        if len(text) > 1:
            lines.append(text)
    return lines

@dataclass
class UnitEntry():
    """Keeping track of a single unit entry"""
    points: int
    quantity: int
    name: str
    upgrades: list

def Convert(docxFile):    
    
    armyList = ["Beast Herds", "Dread Elves", "Dwarven Holds", "Daemon Legions", "Empire of Sonnstahl", "Highborn Elves", "Infernal Dwarves", "Kingdom of Equitaine",
                "Ogre Khans", "Orcs and Goblins", "Saurian Ancients", "Sylvan Elves", "Undying Dynasties", "Vampire Covenant", "Vermin Swarm", "Warriors of the Dark Gods"]

    parsingList = False
    previousLine = ''
    listDict = {}

    filename = Path(docxFile).stem

    lines = docx_to_line_list(docxFile)

    for line in lines:

        currentArmy = [army for army in armyList if army in line]
        if currentArmy:
            parsingList = previousLine
            listDict[parsingList] = []
            continue
        if parsingList:
            splitLine = [x.strip(' .') for x in line.split(', ')]

            splitOutPointsRegex = '(\d{4}|\d{3}|\d{2})(?: - | )(.*)'
            pointsSearch = re.search(splitOutPointsRegex, splitLine[0])
            if pointsSearch:
                # break group 2 ("15 knights" | "41x spearmen" | chariot) into unit name and quantity
                splitOutQuantityRegex = '(\d{2}|\d{1}|)(?:x | |)(.*)'
                quantitySearch = re.search(
                    splitOutQuantityRegex, pointsSearch.group(2))
                if quantitySearch:
                    # if there was no quantity number then the regex match for group 1 is '' so we need to code that as 1
                    quantity = quantitySearch.group(
                        1) if quantitySearch.group(1) else 1
                    newEntry = UnitEntry(points=pointsSearch.group(
                        1), quantity=quantity, name=quantitySearch.group(2), upgrades=splitLine[1:])
                    listDict[parsingList].append(newEntry)
                    continue

            if 4480 < int(line) <= 4500:
                listDict[parsingList].append(int(line))
                parsingList = False
        previousLine = line

        output = {filename: [listDict]}


    return jsons.dumps(output)


if __name__ == "__main__":
    import sys
    filePath = Path(sys.argv[1])

    print(f"Input filepath = {filePath}")
    jsonString = Convert(filePath)
    new_path = filePath.parent / (filePath.stem + ".json")

    jsonFile = open(new_path, "w")
    jsonFile.write(jsonString)
    jsonFile.close