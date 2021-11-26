from typing import List, Union
import re
import requests
from data_classes import ArmyEntry, UnitEntry, Army_names


class new_recruit_parser():

    def Is_int(self, n) -> bool:
        try:
            float(n)
        except ValueError:
            return False
        else:
            return float(n).is_integer()

    def validate(self, lines: List[str]) -> bool:
        url = "https://www.newrecruit.eu/api/listcheck"

        # flatten lines into single string
        flattened_list = ""

        # api can not handle list name on the same line as the army so must be removed
        army_name = self.detect_army_name(lines[1])
        if army_name:
            flattened_list += f"{army_name}\n"

        for line in lines[2:]:
            flattened_list += f"{line}\n"

        request_data = {"list": flattened_list}

        try:
            response = requests.post(url, data=request_data, timeout=2)
        except requests.exceptions.ReadTimeout as err:
            return False

        if response.status_code == 200 and response.text == "[]":
            return True

        return False

    def detect_army_name(self, line) -> Union[Army_names, None]:
        army_name = [army.value for army in Army_names if army.value in line]
        if army_name:
            return army_name[0]
        return None

    def detect_total_points(self, line) -> Union[int, None]:
        if self.Is_int(line) and 4480 < int(line) <= 4500:
            return int(line)
        return None

    def parse_block(self, lines: List[str]) -> ArmyEntry:
        new_army = ArmyEntry()
        for line in lines:

            if line == lines[-1]:  # last line is either the points total or last unit entry
                total_points = self.detect_total_points(line)
                if total_points:
                    new_army.reported_total_points = total_points
                else:
                    # line is 1 or more unit entries
                    new_units = self.parse_unit_line(line)
                    if new_units:
                        for unit in new_units:
                            new_army.add_unit(unit)
                continue

            # line is 1 or more unit entries
            new_units = self.parse_unit_line(line)
            if new_units:
                for unit in new_units:
                    new_army.add_unit(unit)
                continue

            # line is the army name since this is only going to happen once in a army list we do this check last to avoid checking every line
            army_name = self.detect_army_name(line)
            if army_name:
                new_army.army = army_name

        new_army.validated = self.validate(lines)

        return new_army

    def parse_unit_line(self, line: str) -> List[UnitEntry]:
        output = []

        split_line_points_entry = r'(\d{2,4})(?: - | )(.+?)(?=\d{2,4}|$)'
        pointsSearch = re.findall(split_line_points_entry, line)
        if pointsSearch:
            # potentially multiple units were on the same line and need to be handle separately

            for unit in pointsSearch:
                unit_points = int(unit[0]) if self.Is_int(unit[0]) else -1

                if unit_points == -1:
                    raise ValueError(
                        f"unit points: {unit[0]} must be an integer, in line: {line}")

                # break group 2 ("15 knights" | "41x spearmen" | chariot) into unit name and quantity
                splitOutQuantityRegex = r'(\d{1,2}|)(?:x | |)(.+)'
                quantitySearch = re.search(splitOutQuantityRegex, unit[1])
                if quantitySearch:
                    # if there was no quantity number then the regex match for group 1 is '' so we need to hardcode that as 1
                    quantity = int(quantitySearch.group(
                        1)) if quantitySearch.group(1) else 1
                    splitLine = [x.strip(' .')
                                 for x in quantitySearch.group(2).split(', ')]
                    unit_name = splitLine[0]
                    if len(splitLine) > 1:
                        unit_upgrades = splitLine[1:]
                    else:
                        unit_upgrades = []

                    output.append(UnitEntry(
                        points=unit_points, quantity=quantity, name=unit_name, upgrades=unit_upgrades))

        return output
