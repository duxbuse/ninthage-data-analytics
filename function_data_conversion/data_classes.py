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
    units: list
    tournament: str
    total_points: int = -1
