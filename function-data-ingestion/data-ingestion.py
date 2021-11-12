from docx import Document
import re
from dataclasses import dataclass
import jsons


def main(request):
    filePath = 'data\Round 1'

    doc = Document(f"{filePath}.docx")


    lines = []  # ALL the text in the archive, separated by lines

    par = doc.paragraphs
    for i in range(len(par)):
        text = par[i].text
        if len(text) > 1:
            lines.append(text)

    armyList = ["Beast Herds", "Dread Elves", "Dwarven Holds", "Daemon Legions", "Empire of Sonnstahl", "Highborn Elves", "Infernal Dwarves", "Kingdom of Equitaine",
                "Ogre Khans", "Orcs and Goblins", "Saurian Ancients", "Sylvan Elves", "Undying Dynasties", "Vampire Covenant", "Vermin Swarm", "Warriors of the Dark Gods"]


    @dataclass
    class UnitEntry():
        """Keeping track of a single unit entry"""
        points: int
        quantity: int
        name: str
        upgrades: list


    parsingList = False
    previousLine = ''
    listDict = {}
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

    jsonString = jsons.dumps(listDict)
    jsonFile = open(f"{filePath}.json", "w")
    jsonFile.write(jsonString)
    jsonFile.close

if __name__ == "__main__":
    main()