from typing import List, Union
from docx import Document
import re
from data_classes import UnitEntry


def Docx_to_line_list(docxFile) -> List[str]:
    doc = Document(docxFile)

    lines = []  # ALL the text in the file, separated by lines

    par = doc.paragraphs
    for i in range(len(par)):
        text = par[i].text
        if len(text) > 1:
            lines.append(text)
    return lines

def Create_unitEntry_from_line(line: str) -> Union[UnitEntry, None]:
    splitLine = [x.strip(' .') for x in line.split(', ')]
    unit_upgrades = splitLine[1:]

    splitOutPointsRegex = '(\d{4}|\d{3}|\d{2})(?: - | )(.*)'
    pointsSearch = re.search(splitOutPointsRegex, splitLine[0])
    if pointsSearch:
        unit_points = int(pointsSearch.group(1)) if Is_int(pointsSearch.group(1)) else -1

        if unit_points == -1:
            raise ValueError("unit points must be an integer")

        # break group 2 ("15 knights" | "41x spearmen" | chariot) into unit name and quantity
        splitOutQuantityRegex = '(\d{2}|\d{1}|)(?:x | |)(.*)'
        quantitySearch = re.search(splitOutQuantityRegex, pointsSearch.group(2))
        if quantitySearch:
            # if there was no quantity number then the regex match for group 1 is '' so we need to hardcode that as 1
            quantity = int(quantitySearch.group(1)) if quantitySearch.group(1) else 1
            unit_name = quantitySearch.group(2)

            return UnitEntry(points=unit_points, quantity=quantity, name=unit_name, upgrades=unit_upgrades)


def Is_int(n) -> bool:
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()