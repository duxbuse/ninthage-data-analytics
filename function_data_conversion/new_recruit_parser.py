import re
import string
from typing import List, Union

import requests

from data_classes import Army_names, ArmyEntry, UnitEntry

http = requests.Session()

class new_recruit_parser:
    @staticmethod
    def Is_int(n) -> bool:
        try:
            float(n)
        except ValueError:
            return False
        else:
            return float(n).is_integer()

    def validate(self, lines: List[str]) -> list[str]:
        # This takes 52% of exec time
        """
        """
        if len(lines) < 6:  # minimum is name, army, and 4 units
            raise ValueError(
                f"Army Block has to few lines for validation.\nRequires at minimum name, army, and 4 units.\n\nWhole army list = {lines}"
            )

        url = "https://api.newrecruit.eu/api/listcheck"

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
            response = http.post(url, data=request_data, timeout=20)
        except requests.exceptions.Timeout:  # Parent timeout class as there are a few ways to timeout
            return ["Validation Timeout"]

        if response.status_code == 200:
            r = response.json()
            if type(r) == dict:
                return [r.get("error")]
            elif type(r) == list:
                return [x.get("msg") for x in response.json()]
            else:
                return ["Unknown Validation error"]
        elif response.status_code == 502:
            return ["Validation Failed, New Recruit is under maintenance"]
        else:
            return [f"Validation Failed with code:{response.status_code}"]

    def detect_army_name(self, line: str) -> Union[str, None]:
        army_name = Army_names.get(line.strip().upper())
        if army_name:
            return army_name
        return None

    @staticmethod
    def detect_total_points(line:str) -> Union[int, None]:
        # Examples
        # Total Army Cost: 4499 pts
        # 4498pts
        cleaned_line = (
            line.lower()
            .replace("total", "")
            .replace("army", "")
            .replace("cost", "")
            .replace("pts", "")
            .replace("points", "")
        )
        table = str.maketrans(
            dict.fromkeys(string.punctuation)
        )  # OR {key: None for key in string.punctuation}
        cleaned_line = cleaned_line.translate(table)
        cleaned_line = cleaned_line.strip()
        # simple case where its just the number
        if new_recruit_parser.Is_int(cleaned_line) and 2000 <= int(cleaned_line) <= 4500:
            return int(cleaned_line)
        return None

    def parse_block(self, lines: List[str]) -> ArmyEntry:
        new_army = ArmyEntry()
        for i, line in enumerate(lines):

            if (
                i == len(lines) - 1
            ):  # last line is either the points total or last unit entry
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

        return new_army

    def parse_unit_line(self, line: str) -> List[UnitEntry]:
        output = []

        # regex explanation don't match "Benji#9781 - Captain" so we need to start with a negative lookbehind due to python being basic, and needing fixed look behinds we need to do each variation separately
        # Then match number "630 - Death Cult Hierarch" -> "<number> - <unit name>, upgrades"
        # Sometimes there are unit entries on the same line so we then do a positive lookahead to make sure if there is another unit entry its not captured by the '(.+?)'
        split_line_points_entry = r"^(\d{2,4}?)(?: ?[\W ] ?)(.+)"
        pointsSearch = re.search(
            split_line_points_entry, line.lower().strip(".")
        )  # ensure its all lowercase to prevent casing issues
        if pointsSearch:
            # potentially multiple units were on the same line and need to be handle separately
            multi_unit = r"(\d{2,4}?)(?: ?[\W ] ?)(.+?)(?=\d{2,4}|$)"
            multi_pointsSearch = re.findall(multi_unit, line.lower())
            for unit in multi_pointsSearch:
                unit_points = int(unit[0]) if self.Is_int(unit[0]) else -1

                if unit_points == -1:
                    raise ValueError(
                        f"unit points: {unit[0]} must be an integer, in line: {line}"
                    )

                # break group 2 ("15 knights" | "41x spearmen" | chariot) into unit name and quantity
                splitOutQuantityRegex = r"(\d{1,2}|)(?:x | |)(.+)"
                quantitySearch = re.search(splitOutQuantityRegex, unit[1])
                if quantitySearch:
                    # if there was no quantity number then the regex match for group 1 is '' so we need to hardcode that as 1
                    quantity = (
                        int(quantitySearch.group(1)) if quantitySearch.group(1) else 1
                    )
                    cleaned_upgrades = self.clear_superfluous_data(
                        quantitySearch.group(2)
                    )
                    non_nested_upgrades = self.break_nested_upgrades(cleaned_upgrades)
                    splitLine = [x.strip() for x in non_nested_upgrades.split(", ")]
                    unit_name = splitLine[0]
                    if len(splitLine) > 1:
                        unit_upgrades = splitLine[1:]
                    else:
                        unit_upgrades = []

                    unit_upgrades = self.expand_short_hand(unit_upgrades)
                    output.append(
                        UnitEntry(
                            points=unit_points,
                            quantity=quantity,
                            name=unit_name,
                            upgrades=unit_upgrades,
                        )
                    )

        return output

    def clear_superfluous_data(self, unit_upgrades: str) -> str:
        """getting rid of things we don't want to store

        Args:
            unit_upgrades (str): [description]

        Returns:
            str: cleaned string
        """
        # removing "(4+)|4+" from "Crossbow (4+)|Crossbow 4+"
        regex = r" ?(\(\d\+\)|\d\+)"
        unit_upgrades = re.sub(regex, "", unit_upgrades)

        # removing [xxpts]
        regex = r" ?(\[\d+ ?pts\]|\d+ ?pts)"
        unit_upgrades = re.sub(regex, "", unit_upgrades)

        # Clear out some guff encoding
        unit_upgrades = unit_upgrades.replace("&#39;", "'")

        return unit_upgrades

    def expand_short_hand(self, unit_upgrades: list[str]) -> list[str]:

        new_unit_upgrades = unit_upgrades[
            :
        ]  # Need to take a slice as then it is not linked to the original object, to avoid infinite loop
        for index, upgrade in enumerate(unit_upgrades):
            # m -> musician
            regex = r"^(m|muso)$"
            new_unit_upgrades[index] = re.sub(regex, "musician", upgrade, flags=re.IGNORECASE)

            # s -> standard bearer
            regex = r"^(s|standard)$"
            new_unit_upgrades[index] = re.sub(regex, "standard bearer", upgrade, flags=re.IGNORECASE)

            # c -> champion
            regex = r"^(c|champ)$"
            new_unit_upgrades[index] = re.sub(regex, "champion", upgrade, flags=re.IGNORECASE)

            # bsb -> battle standard bearer
            regex = r"^(bsb|battlestandard)$"
            new_unit_upgrades[index] = re.sub(regex, "battle standard bearer", upgrade, flags=re.IGNORECASE)

            # FCG -> champ+muso+standard
            regex = r"^(fcg|gmc|full command|full command group)$"
            if re.match(regex, upgrade, flags=re.IGNORECASE):
                new_unit_upgrades[index] = re.sub(regex, "standard bearer", upgrade, flags=re.IGNORECASE)
                new_unit_upgrades.append("musician")
                new_unit_upgrades.append("champion")

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
