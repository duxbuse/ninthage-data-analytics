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

    def validate(self, lines: List[str]) -> str:
        """
            TODO: Known issues:
            if some units are on the same line we can still read it in but validation will fail
            
        """


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
            response = requests.post(url, data=request_data, timeout=1)
        except requests.exceptions.ReadTimeout as err:
            return err

        return response.text

    def detect_army_name(self, line: str) -> Union[str, None]:
        army_name = Army_names.get(line.upper())
        if army_name:
            return army_name
        return None

    def detect_total_points(self, line) -> Union[int, None]:
        if self.Is_int(line) and 2000 <= int(line) <= 4500:
            return int(line)
        return None

    def parse_block(self, lines: List[str]) -> ArmyEntry:
        new_army = ArmyEntry()
        for line in lines:

            if line == lines[-1]:  # last line is either the points total or last unit entry
                total_points = self.detect_total_points(line)
                if total_points:
                    new_army.reported_total_army_points = total_points
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

        validation_errors = self.validate(lines)
        new_army.validated = not validation_errors
        new_army.validation_errors = validation_errors

        return new_army

    def parse_unit_line(self, line: str) -> List[UnitEntry]:
        output = []

        split_line_points_entry = r'(\d{2,4})(?: - | –| )(.+?)(?=\d{2,4}|$)'
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
                    non_nested_upgrades = self.break_nested_upgrades(
                        quantitySearch.group(2))
                    splitLine = [x.strip() for x in non_nested_upgrades.split(', ')]
                    unit_name = splitLine[0]
                    if len(splitLine) > 1:
                        unit_upgrades = splitLine[1:]
                    else:
                        unit_upgrades = []

                    unit_upgrades = self.expand_short_hand(unit_upgrades)
                    output.append(UnitEntry(
                        points=unit_points, quantity=quantity, name=unit_name, upgrades=unit_upgrades))

        return output

    def expand_short_hand(self, unit_upgrades: list[str]) -> list[str]:

        new_unit_upgrades = unit_upgrades
        for index, upgrade in enumerate(unit_upgrades):
            # m -> musician
            regex = r'^(m|M|muso)$'
            new_unit_upgrades[index] = re.sub(regex, 'Musician', upgrade)
            # s -> standard bearer
            regex = r'^(s|S|standard)$'
            new_unit_upgrades[index] = re.sub(regex, 'Standard Bearer', upgrade)
            # c -> champion
            regex = r'^(c|C|champ)$'
            new_unit_upgrades[index] = re.sub(regex, 'Champion', upgrade)
            # bsb -> battle standard bearer
            regex = r'^(bsb|BSB)$'
            new_unit_upgrades[index] = re.sub(regex, 'Battle Standard Bearer', upgrade)
        return new_unit_upgrades

    def break_nested_upgrades(self, unit_upgrades: str) -> str:
        """Resolving nested upgrades that are contained inside ()
        More details https://github.com/duxbuse/ninthage-data-analytics/issues/12

        Args:
            unit_upgrades (str): "340 - Marshal, Battle Standard Bearer (Aether Icon, Aether Icon), Shield, Paired Weapons (Shield Breaker), Blacksteel, Great Tactician"

        Returns:
            str: "340 - Marshal, Battle Standard Bearer, Aether Icon, Aether Icon, Shield, Paired Weapons, Shield Breaker, Blacksteel, Great Tactician"
        """
        return unit_upgrades.replace(" (", ", ").replace(")", "")
