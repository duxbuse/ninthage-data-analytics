from dataclasses import dataclass, field


@dataclass
class UnitEntry():
    """Keeping track of a single unit entry as part of a list"""
    points: int #300
    quantity: int #25
    name: str #spearmen
    upgrades: list[str] = [] #musician and banner


@dataclass
class ArmyEntry():
    """class to hold entire army list
    """
    player_name: str
    army: str
    tournament: str
    total_points: int = 0
    units: list[UnitEntry] = field(default_factory=list)

    def calculate_total_points(self) -> None:
        self.total_points = sum([int(x.points) for x in self.units])