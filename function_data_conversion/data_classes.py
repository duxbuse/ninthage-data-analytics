from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Union
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


Army_names = {
    "BEAST HERDS": "Beast Herds",
    "BH": "Beast Herds",

    "DREAD ELVES": "Dread Elves",
    "DE": "Dread Elves",

    "DWARVEN HOLDS": "Dwarven Holds",
    "DH": "Dwarven Holds",

    "DAEMON LEGIONS": "Daemon Legions",
    "DL": "Daemon Legions",

    "EMPIRE OF SONNSTAHL": "Empire of Sonnstahl",
    "EOS": "Empire of Sonnstahl",

    "HIGHBORN ELVES": "Highborn Elves",
    "HBE": "Highborn Elves",

    "INFERNAL DWARVES": "Infernal Dwarves",
    "ID": "Infernal Dwarves",

    "KINGDOM OF EQUITAINE": "Kingdom of Equitaine",
    "KOE": "Kingdom of Equitaine",

    "OGRE KHANS": "Ogre Khans",
    "OK": "Ogre Khans",

    "ORCS AND GOBLINS": "Orcs and Goblins",
    "ONG": "Orcs and Goblins",
    "O&G": "Orcs and Goblins",

    "SAURIAN ANCIENTS": "Saurian Ancients",
    "SA": "Saurian Ancients",

    "SYLVAN ELVES": "Sylvan Elves",
    "SE": "Sylvan Elves",

    "UNDYING DYNASTES": "Undying Dynasties",
    "UD": "Undying Dynasties",

    "VAMPIRE COVENANT": "Vampire Covenant",
    "VC": "Vampire Covenant",

    "VERMIN SWARM": "Vermin Swarm",
    "VS": "Vermin Swarm",

    "WARRIORS OF THE DARK GODS": "Warriors of the Dark Gods",
    "WDG": "Warriors of the Dark Gods",

    "ASKLANDERS": "Åsklanders",
    "CULTISTS": "Cultists",
    "HOBGOLBINS": "Hobgolbins",
    "MAKHAR": "Makhar"
}

@dataclass
class Tk_info():
    event_date: Optional[datetime] = datetime(1970, 1, 1, tzinfo=timezone.utc)
    event_type: Optional[Event_types] = Event_types.SINGLES
    game_list: Optional[dict] = field(default_factory=dict)
    # output from Get_players_names_from_games()
    player_list: Optional[dict] = field(default_factory=dict)
    player_count: Optional[int] = None


@dataclass
class UnitEntry():
    """Keeping track of a single unit entry as part of a list"""
    points: int  # 300
    quantity: int  # 25
    name: str  # spearmen
    unit_uuid: UUID = field(default_factory=lambda: uuid4())
    upgrades: list[str] = field(default_factory=list)  # musician and banner


@dataclass
class Round():
    opponent: Optional[Union[UUID, int]] = -1
    result: Optional[int] = -1
    secondary_points: Optional[int] = -1
    round_number: Optional[int] = -1
    game_uuid: Optional[Union[UUID, int]] = -1 #I know this is a type issue, but when there is no TK data to load we need a non 'None' default


@dataclass
class ArmyEntry():
    """class to hold entire army list
    """
    player_name: Optional[str] = None  # bob
    army: Optional[str] = None  # Vampire Covenant
    tournament: Optional[str] = None  # brawler bash 2021
    event_date: Optional[datetime] = None
    ingest_date: Optional[datetime] = None
    event_type: Optional[Event_types] = None
    list_placing: Optional[int] = -1
    event_size: Optional[int] = None
    tourney_keeper_TournamentPlayerId: Optional[int] = -1
    tourney_keeper_PlayerId: Optional[int] = -1
    calculated_total_tournament_points: Optional[int] = -1
    calculated_total_tournament_secondary_points: Optional[int] = -1
    reported_total_army_points: Optional[int] = -1
    calculated_total_army_points: Optional[int] = None
    validated: bool = False
    validation_errors: str = ''
    round_performance: list[Round] = field(default_factory=list)
    army_uuid: UUID = field(default_factory=lambda: uuid4())
    units: list[UnitEntry] = field(default_factory=list)

    def calculate_total_points(self) -> None:
        self.calculated_total_army_points = sum([x.points for x in self.units])
        if self.reported_total_army_points != -1 and self.calculated_total_army_points != self.reported_total_army_points:
            raise ValueError(f"""
            Mismatch between reported:{self.reported_total_army_points} and calculated:{self.calculated_total_army_points}.
            Army: {self.army}
            Player_name: {self.player_name}
            Tournament: {self.tournament}
            """)

    def calculate_total_tournament_points(self) -> None:
        if self.round_performance:
            self.calculated_total_tournament_points = sum(
                [x.result for x in self.round_performance])
            self.calculated_total_tournament_secondary_points = sum(
                [x.secondary_points for x in self.round_performance])

    def add_unit(self, unit: UnitEntry) -> None:
        self.units.append(unit)
