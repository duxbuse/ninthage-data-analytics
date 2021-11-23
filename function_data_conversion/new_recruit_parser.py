from data_classes import ArmyEntry, UnitEntry, Army_names
from typing import List, Union
from utility_functions import Is_int
import re


class new_recruit_parser():

    def detect_army_name(self, line) -> Union[Army_names, None]:
        army_name = [army.value for army in Army_names if army.value in line]
        if army_name:
            return army_name[0]
        return None

    def detect_total_points(self, line) -> Union[int, None]:
        if Is_int(line) and 4480 < int(line) <= 4500:
            return int(line)
        return None

    def parse_block(self, lines: List[str]) -> ArmyEntry:
        new_army = ArmyEntry()
        for line in lines:
            
            if line == lines[-1]: #last line is either the points total or last unit entry
                total_points = self.detect_total_points(line)
                if total_points:
                    new_army.reported_total_points = total_points
                else:
                    new_unit = self.parse_unit_line(line)
                    if new_unit:
                        new_army.add_unit(new_unit)

                new_army.calculate_total_points()
                continue
            
            new_unit = self.parse_unit_line(line)# line is a unit entry
            if new_unit:
                new_army.add_unit(new_unit)
                continue

            army_name = self.detect_army_name(line) # line is the army name since this is only going to happen once in a army list we do this check last to avoid checking every line
            if army_name:
                new_army.army = army_name

        return new_army



    def parse_unit_line(self, line: str) -> Union[UnitEntry, None]:
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

        return None