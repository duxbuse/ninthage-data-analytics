from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto, unique
import math
from typing import Optional
from uuid import UUID, uuid4


@unique
class Parsers(Enum):
    NEW_RECRUIT = auto()
    BATTLE_SCRIBE = auto()
    INFO_TABLE = auto()


@unique
class Data_sources(Enum):
    TOURNEY_KEEPER = auto()
    NEW_RECRUIT = auto()
    FADING_FLAMES = auto()
    WARHALL = auto()
    MANUAL = auto()


@unique
class Event_types(Enum):
    SINGLES = auto()
    TEAMS = auto()
    CASUAL = auto()


Magic = {
    "H": "Hereditary",
    "A1": "A1",
    "A2": "A2",
    "A3": "A3",
    "A4": "A4",
    "A5": "A5",
    "A6": "A6",
    "C1": "C1",
    "C2": "C2",
    "C3": "C3",
    "C4": "C4",
    "C5": "C5",
    "C6": "C6",
    "DV1": "DV1",
    "DV2": "DV2",
    "DV3": "DV3",
    "DV4": "DV4",
    "DV5": "DV5",
    "DV6": "DV6",
    "DR1": "DR1",
    "DR2": "DR2",
    "DR3": "DR3",
    "DR4": "DR4",
    "DR5": "DR5",
    "DR6": "DR6",
    "E1": "E1",
    "E2": "E2",
    "E3": "E3",
    "E4": "E4",
    "E5": "E5",
    "E6": "E6",
    "O1": "O1",
    "O2": "O2",
    "O3": "O3",
    "O4": "O4",
    "O5": "O5",
    "O6": "O6",
    "P1": "P1",
    "P2": "P2",
    "P3": "P3",
    "P4": "P4",
    "P5": "P5",
    "P6": "P6",
    "S1": "S1",
    "S2": "S2",
    "S3": "S3",
    "S4": "S4",
    "S5": "S5",
    "S6": "S6",
    "T1": "T1",
    "T2": "T2",
    "T3": "T3",
    "T4": "T4",
    "T5": "T5",
    "T6": "T6",
    "W1": "W1",
    "W2": "W2",
    "W3": "W3",
    "W4": "W4",
    "W5": "W5",
    "W6": "W6",
}

Maps = {
    "Other": "OTHER",
    "None": "OTHER",
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
    "Other": "OTHER",
    "": "OTHER",
    "None": "OTHER",
    "Frontline Clash": "1 FRONTLINE CLASH",
    "Dawn Assault": "2 DAWN ASSAULT",
    "Counter Thrust": "3 COUNTER THRUST",
    "Counterthrust": "3 COUNTER THRUST",
    "Encircle": "4 ENCIRCLE",
    "Refused Flank": "5 REFUSED FLANK",
    "Marching Columns": "6 MARCHING COLUMNS",
}
Objectives = {
    "Other": "OTHER",
    "": "OTHER",
    "None": "OTHER",
    "Hold the Ground": "1 HOLD THE GROUND",
    "Breakthrough": "2 BREAKTHROUGH",
    "Spoils of War": "3 SPOILS OF WAR",
    "King of the Hill": "4 KING OF THE HILL",
    "Capture the Flags": "5 CAPTURE THE FLAGS",
    "Secure Target": "6 SECURE TARGET",
}


# When updating this also remember to update fading_flame.py faction mappings
Army_names = {
    "BEAST HERDS": "Beast Herds",
    "BH": "Beast Herds",
    "DREAD ELVES": "Dread Elves",
    "DE": "Dread Elves",
    "DWARVEN HOLDS": "Dwarven Holds",
    "DH": "Dwarven Holds",
    "Dwarfs": "Dwarven Holds",
    "DAEMON LEGIONS": "Daemon Legions",
    "DAEMONIC LEGIONS": "Daemon Legions",
    "DL": "Daemon Legions",
    "EMPIRE OF SONNSTAHL": "Empire of Sonnstahl",
    "EOS": "Empire of Sonnstahl",
    "HIGHBORN ELVES": "Highborn Elves",
    "HE": "Highborn Elves",
    "HBE": "Highborn Elves",
    "INFERNAL DWARVES": "Infernal Dwarves",
    "INFERNAL DWARFS": "Infernal Dwarves",
    "ID": "Infernal Dwarves",
    "KINGDOM OF EQUITAINE": "Kingdom of Equitaine",
    "KOE": "Kingdom of Equitaine",
    "OGRE KHANS": "Ogre Khans",
    "OK": "Ogre Khans",
    "ORCS AND GOBLINS": "Orcs and Goblins",
    "ORCS & GOBLINS": "Orcs and Goblins",
    "ONG": "Orcs and Goblins",
    "O&G": "Orcs and Goblins",
    "OG": "Orcs and Goblins",
    "SAURIAN ANCIENTS": "Saurian Ancients",
    "SA": "Saurian Ancients",
    "SYLVAN ELVES": "Sylvan Elves",
    "SE": "Sylvan Elves",
    "UNDYING DYNASTIES": "Undying Dynasties",
    "UD": "Undying Dynasties",
    "VAMPIRE COVENANT": "Vampire Covenant",
    "VAMPIRE COVENANTS": "Vampire Covenant",
    "VC": "Vampire Covenant",
    "VERMIN SWARM": "Vermin Swarm",
    "VS": "Vermin Swarm",
    "THE VERMIN SWARM": "Vermin Swarm",
    "WARRIORS OF THE DARK GODS": "Warriors of the Dark Gods",
    "WDG": "Warriors of the Dark Gods",
    "WTDG": "Warriors of the Dark Gods",
    "WOTDG": "Warriors of the Dark Gods",
    "ÅSKLANDERS": "Åsklanders",
    "ASKLANDERS": "Åsklanders",
    "ASKLANDER": "Åsklanders",
    "CULTISTS": "Cultists",
    "CULTIST": "Cultists",
    "HOBGOBLINS": "Hobgoblins",
    "HOBGOBLIN": "Hobgoblins",
    "MAKHAR": "Makhar",
    "LEGIONS OF SIN": "Legions of Sin",
    "PLACEHOLDER": "Placeholder",
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
    )  # dict: {PlayerId: 1234: {TournamentPlayerId: 5678, Player_name: bob}}
    player_count: Optional[int] = None
    players_per_team: Optional[int] = None


@dataclass
class UnitEntry:
    """Keeping track of a single unit entry as part of a list"""

    points: int  # 300
    quantity: int  # 25
    name: str  # spearmen
    dead: Optional[bool] = None
    half: Optional[bool] = None
    unit_uuid: UUID = field(default_factory=lambda: uuid4())
    upgrades: Optional[list[str]] = None  # musician and banner


@dataclass
class Round:
    opponent: Optional[UUID] = None  # Expect that this is an army_uuid
    result: Optional[int] = None
    secondary_points: Optional[int] = None
    round_number: Optional[int] = None
    game_uuid: UUID = field(default_factory=lambda: uuid4())
    fading_flame_game_id: Optional[str] = None
    won_secondary: Optional[bool] = None
    deployed_first: Optional[bool] = None
    deployed_everything: Optional[bool] = None
    first_turn: Optional[bool] = None
    map_selected: Optional[str] = None
    deployment_selected: Optional[str] = None
    objective_selected: Optional[str] = None
    spells_selected: Optional[list[str]] = None


@dataclass
class ArmyEntry:
    """class to hold entire army list"""

    player_name: Optional[str] = None  # bob
    army: Optional[str] = None  # Vampire Covenant
    army_version_id: Optional[int] = None
    army_version_name: Optional[str] = None
    tournament: Optional[str] = None  # brawler bash 2021
    event_date: Optional[datetime] = None
    ingest_date: Optional[datetime] = None
    event_type: Optional[Event_types] = None
    list_placing: Optional[int] = None
    list_as_str: Optional[str] = None
    event_size: Optional[int] = None
    data_source: Optional[Data_sources] = None
    tourney_keeper_TournamentPlayerId: Optional[int] = None
    tourney_keeper_PlayerId: Optional[int] = None
    fading_flame_player_id: Optional[str] = None
    calculated_total_tournament_points: Optional[int] = None
    calculated_total_tournament_secondary_points: Optional[int] = None
    reported_total_army_points: Optional[int] = None
    calculated_total_army_points: Optional[int] = None
    validated: bool = False
    validation_errors: Optional[list[str]] = None
    round_performance: Optional[list[Round]] = None
    country_name: Optional[str] = None
    country_flag: Optional[str] = None
    participants_per_team: Optional[int] = None
    team_point_cap_max: Optional[int] = None  # 100
    team_point_cap_min: Optional[int] = None  # 60
    team_placing: Optional[int] = None
    team_total_tournament_points: Optional[int] = None
    team_total_secondary_points: Optional[int] = None
    team_id: Optional[str] = None
    team_captain: Optional[bool] = None
    units: Optional[list[UnitEntry]] = None
    army_uuid: UUID = field(default_factory=lambda: uuid4())

    def calculate_total_points(self) -> None:
        self.calculated_total_army_points = sum([x.points for x in self.units or []])
        if (
            self.reported_total_army_points != None
            and self.calculated_total_army_points != self.reported_total_army_points
        ):
            msg = f"""
            Reported:{self.reported_total_army_points}
            Calculated:{self.calculated_total_army_points}
            Army: {self.army}
            Player_name: {self.player_name}
            Tournament: {self.tournament}
            Found Units: {[(x.name, x.points) for x in self.units or []]}
            """
            if self.data_source == Data_sources.TOURNEY_KEEPER:
                raise ValueError(msg)
            else:
                print(msg)

    def points_killed(self) -> int:
        points = 0
        for x in self.units or []:
            if x.dead:
                points += x.points
                if "general" in str(x.upgrades):
                    points += 200
                if "battle standard bearer" in str(x.upgrades):
                    points += 200
            elif x.half:
                points += math.ceil(x.points / 2)
        return points

    def calculate_total_tournament_points(self) -> None:
        if self.round_performance:
            if all([isinstance(x.result, int) for x in self.round_performance]):
                self.calculated_total_tournament_points = sum(
                    [x.result for x in self.round_performance if x.result]
                )
            if all(
                [isinstance(x.secondary_points, int) for x in self.round_performance]
            ):
                self.calculated_total_tournament_secondary_points = sum(
                    [
                        x.secondary_points
                        for x in self.round_performance
                        if x.secondary_points
                    ]
                )

    def add_unit(self, unit: UnitEntry) -> None:
        if self.units is not None:
            self.units.append(unit)
        else:
            self.units = [unit]
