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
    CASUAL = auto()


Maps = {
    "OTHER": "Other",
    "A1": "A1",
    "A2": "A2",
    "A3": "A3",
    "A4": "A4",
    "A5": "A5",
    "A6": "A6",
    "A7": "A7",
    "A8": "A8",
    "B1": "B1",
    "B2": "B2",
    "B3": "B3",
    "B4": "B4",
    "B5": "B5",
    "B6": "B6",
    "B7": "B7",
    "B8": "B8",
}
Deployments = {
    "OTHER": "Other",
    "1 FRONTLINE CLASH": "Frontline Clash",
    "2 DAWN ASSULT": "Dawn Assault",
    "3 COUNTER THRUST": "Counter Thrust",
    "4 ENCIRCLE": "Encircle",
    "5 REFUSED FLANK": "Refused Flank",
    "6 MARCHING COLUMNS": "Marching Columns",
}
Objectives = {
    "OTHER": "Other",
    "1 HOLD THE GROUND": "Hold the Ground",
    "2 BREAKTHROUGH": "Breakthrough",
    "3 SPOILS OF WAR": "Spoils of War",
    "4 KING OF THE HILL": "King of the Hill",
    "5 CAPTURE THE FLAGS": "Capture the Flags",
    "6 SECURE TARGET": "Secure Target",
}

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
    "HE": "Highborn Elves",
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
    "UNDYING DYNASTIES": "Undying Dynasties",
    "UD": "Undying Dynasties",
    "VAMPIRE COVENANT": "Vampire Covenant",
    "VC": "Vampire Covenant",
    "VERMIN SWARM": "Vermin Swarm",
    "VS": "Vermin Swarm",
    "WARRIORS OF THE DARK GODS": "Warriors of the Dark Gods",
    "WDG": "Warriors of the Dark Gods",
    "WTDG": "Warriors of the Dark Gods",
    "WOTDG": "Warriors of the Dark Gods",
    "ASKLANDERS": "Åsklanders",
    "CULTISTS": "Cultists",
    "HOBGOBLINS": "Hobgoblins",
    "MAKHAR": "Makhar",
}


@dataclass
class Tk_info:
    event_date: Optional[datetime] = None
    event_type: Optional[Event_types] = Event_types.SINGLES
    event_id: Optional[int] = None
    game_list: Optional[dict] = field(default_factory=dict)
    # output from Get_players_names_from_games()
    player_list: Optional[dict] = field(
        default_factory=dict
    )  # dict: {Player_name: {TournamentPlayerId: 5678, PlayerId: 1234}}
    player_count: Optional[int] = None
    players_per_team: Optional[int] = None


@dataclass
class UnitEntry:
    """Keeping track of a single unit entry as part of a list"""

    points: int  # 300
    quantity: int  # 25
    name: str  # spearmen
    unit_uuid: UUID = field(default_factory=lambda: uuid4())
    upgrades: list[str] = field(default_factory=list)  # musician and banner


@dataclass
class Round:
    opponent: Optional[UUID] = None
    result: Optional[int] = None
    secondary_points: Optional[int] = None
    round_number: Optional[int] = None
    game_uuid: Optional[UUID] = None
    won_secondary: Optional[bool] = None
    deployed_first: Optional[bool] = None
    deployed_everything: Optional[bool] = None
    first_turn: Optional[bool] = None
    map_selected: Optional[str] = None
    deployment_selected: Optional[str] = None
    objective_selected: Optional[str] = None
    TODO: something about magic choices, also make every field optional if possible.


@dataclass
class ArmyEntry:
    """class to hold entire army list"""

    player_name: Optional[str] = None  # bob
    army: Optional[str] = None  # Vampire Covenant
    tournament: Optional[str] = None  # brawler bash 2021
    event_date: Optional[datetime] = None
    ingest_date: Optional[datetime] = None
    event_type: Optional[Event_types] = None
    list_placing: Optional[int] = None
    event_size: Optional[int] = None
    tourney_keeper_TournamentPlayerId: Optional[int] = None
    tourney_keeper_PlayerId: Optional[int] = None
    calculated_total_tournament_points: Optional[int] = None
    calculated_total_tournament_secondary_points: Optional[int] = None
    reported_total_army_points: Optional[int] = None
    calculated_total_army_points: Optional[int] = None
    validated: bool = False
    validation_errors: Optional[list[str]] = None
    round_performance: Optional[list[Round]] = None
    army_uuid: UUID = field(default_factory=lambda: uuid4())
    units: list[UnitEntry] = field(default_factory=list)

    def calculate_total_points(self) -> None:
        self.calculated_total_army_points = sum([x.points for x in self.units])
        if (
            self.reported_total_army_points != None
            and self.calculated_total_army_points != self.reported_total_army_points
        ):
            raise ValueError(
                f"""
            Reported:{self.reported_total_army_points}
            Calculated:{self.calculated_total_army_points}
            Army: {self.army}
            Player_name: {self.player_name}
            Tournament: {self.tournament}
            Found Units: {[(x.name, x.points) for x in self.units]}
            """
            )

    def calculate_total_tournament_points(self) -> None:
        if self.round_performance:
            self.calculated_total_tournament_points = sum(
                [x.result for x in self.round_performance]
            )
            self.calculated_total_tournament_secondary_points = sum(
                [x.secondary_points for x in self.round_performance]
            )

    def add_unit(self, unit: UnitEntry) -> None:
        self.units.append(unit)
