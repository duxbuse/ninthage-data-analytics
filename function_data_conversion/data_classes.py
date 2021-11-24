from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from enum import Enum, unique, auto


@unique
class Parsers(Enum):
    NEW_RECRUIT = auto()
    BATTLE_SCRIBE = auto()
    INFO_TABLE = auto()


@unique
class Event_types(Enum):
    SINGLES = auto()
    TEAMS = auto()


@unique
class Army_names(Enum):
    BEAST_HERDS = "Beast Herds"
    DREAD_ELVES = "Dread Elves"
    DWARVEN_HOLDS = "Dwarven Holds"
    DAEMON_LEGIONS = "Daemon Legions"
    EMPIRE_OF_SONNSTAHL = "Empire of Sonnstahl"
    HIGHBORN_ELVES = "Highborn Elves"
    INFERNAL_DWARVES = "Infernal Dwarves"
    KINGDOM_OF_EQUITAINE = "Kingdom of Equitaine"
    OGRE_KHANS = "Ogre Khans"
    ORCS_AND_GOBLINS = "Orcs and Goblins"
    SAURIAN_ANCIENTS = "Saurian Ancients"
    SYLVAN_ELVES = "Sylvan Elves"
    UNDYING_DYNASTES = "Undying Dynasties"
    VAMPIRE_COVENANT = "Vampire Covenant"
    VERMIN_SWARM = "Vermin Swarm"
    WARRIORS_OF_THE_DARK_GODS = "Warriors of the Dark Gods"
    ASKLANDERS = "Åsklanders"
    CULTISTS = "Cultists"
    HOBGOLBINS = "Hobgolbins"
    MAKHAR = "Makhar"


@dataclass
class UnitEntry():
    """Keeping track of a single unit entry as part of a list"""
    points: int  # 300
    quantity: int  # 25
    name: str  # spearmen
    unit_uuid: UUID = field(default_factory=lambda: uuid4())
    upgrades: list[str] = field(default_factory=list)  # musician and banner


@dataclass
class ArmyEntry():
    """class to hold entire army list
    """
    player_name: Optional[str] = None  # bob
    army: Optional[Army_names] = None  # Vampire Covenant
    tournament: Optional[str] = None  # brawler bash 2021
    event_date: Optional[datetime] = None
    ingest_date: Optional[datetime] = None
    event_type: Optional[Event_types] = None
    list_placing: Optional[int] = None
    event_size: Optional[int] = None
    reported_total_points: Optional[int] = -1
    calculated_total_points: Optional[int] = None
    validated: bool = False
    army_uuid: UUID = field(default_factory=lambda: uuid4())
    units: list[UnitEntry] = field(default_factory=list)

    def calculate_total_points(self) -> None:
        self.calculated_total_points = sum([x.points for x in self.units])
        if self.reported_total_points != -1 and self.calculated_total_points != self.reported_total_points:
            raise ValueError(f"""
            Mismatch between 'reported':{self.reported_total_points} and 'calculated':{self.calculated_total_points}.
            Army: {self.army}
            Player_name: {self.player_name}
            Tournament: {self.tournament}
            """)

    def add_unit(self, unit: UnitEntry) -> None:
        self.units.append(unit)
