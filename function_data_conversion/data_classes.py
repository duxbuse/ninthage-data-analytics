from dataclasses import dataclass


@dataclass
class UnitEntry():
    """Keeping track of a single unit entry as part of a list"""
    points: int
    quantity: int
    name: str
    upgrades: list


@dataclass
class ArmyEntry():
    """class to hold entire army list
    """
    player_name: str
    army: str
    units: list[UnitEntry]
    tournament: str
    total_points: int = 0

    def calculate_total_points(self):
        self.total_points = sum([int(x.points) for x in self.units])