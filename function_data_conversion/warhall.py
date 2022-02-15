from multi_error import Multi_Error
from converter import Convert_lines_to_army_list
from data_classes import (
    Round,
    Event_types,
    Data_sources,
    ArmyEntry,
    Deployments,
    Army_names,
    Maps,
    Objectives,
)
from pydantic import BaseModel, ValidationError, validator
from typing import List, Optional



class warhall_player_data(BaseModel):
    ArmyName: str
    List: List[str]
    Objective: str
    PointDifference: int
    Result: int

    @validator("ArmyName")
    def validate_army_name(cls, ArmyName):
        if ArmyName not in Army_names.values():
            raise ValueError(f"{ArmyName=} is not a valid army name")
        return ArmyName

    @validator("Objective")
    def validate_objective(cls, Objective):
        if Objective not in ["Won", "Lost", "Draw"]:
            raise ValueError(f"{Objective=} is not a valid objective")
        return Objective

    @validator("Result")
    def validate_result(cls, Result):
        if not 0 <= Result <= 20:
            raise ValueError(f"{Result=} is not a valid result from 0-20")
        return Result

class warhall_data(BaseModel):
    Deployment: str
    Map: str
    Objective: str
    PlayersData: List[warhall_player_data]
    ReportTime: int

    @validator("Deployment")
    def validate_deployment(cls, Deployment):
        if Deployment not in Deployments.values():
            raise ValueError(f"{Deployment=} is not a valid deployment")
        return Deployment

    @validator("Map")
    def validate_map(cls, Map):
        if Map not in Maps.values():
            raise ValueError(f"{Map=} is not a valid map")
        return Map

    @validator("Objective")
    def validate_objective(cls, Objective):
        if Objective not in Objectives.values():
            raise ValueError(f"{Objective=} is not a valid objective")
        return Objective


def armies_from_warhall(data:dict) -> list[ArmyEntry]:
    data_obj = warhall_data(**data)
    pass

if __name__ == "__main__":
    example = {
    "Deployment": "Dawn Assault",
    "Map": "A2",
    "Objective": "Breakthrough",
    "PlayersData": [
        {
            "ArmyName": "Orcs and Goblins",
            "List": [
                "DEAD 510 - Orc Warlord, Feral Orc, War Boar, Shield, Light Armour (Tuktek's Guard),  Hand Weapon (Omen of the Apocalypse), Potion of Swiftness",
                "DEAD 455 - Orc Shaman, General, Feral Orc, Wizard Master, Shamanism, Rod of Battle",
                "DEAD 370 - Goblin King, Forest Goblin and Poison Attacks, Huntsmen Spider, Shield (Dusk Forged), Paired Weapons, Heavy Armour (Basalt Infusion),  Hand Weapon (Hero's Heart)",
                "DEAD 310 - Orc Chief, Feral Orc, Battle Standard Bearer (Aether Icon, Aether Icon), Great Weapon, Light Armour (Essence of Mithril), Obsidian Rock",
                "DEAD 120 - Goblin Chief, Common Goblin, Crown of the Wizard King",
                "DEAD 700 - 40 Orcs, Feral Orc, Bow, Spear, Standard Bearer (Green Tide), Musician, Champion",
                "DEAD 426 - 48 Goblins, Forest Goblin, Shield, Throwing Weapons, Standard Bearer (Green Tide), Musician",
                "DEAD 387 - 6 Trolls, Bridge Troll",
                "DEAD 135 - Gnasher Wrecking Team, ",
                "DEAD 135 - Gnasher Wrecking Team, ",
                "DEAD 80 - Scrap Wagon, ",
                "DEAD 80 - Scrap Wagon, ",
                "DEAD 175 - Greenhide Catapult, Splatterer, Orc Overseer",
                "DEAD 90 - Skewerer, ",
                "DEAD 525 - Gargantula, Web Launcher"
            ],
            "Objective": "Draw",
            "PointDifference": -2998,
            "Result": 4
        },
        {
            "ArmyName": "Kingdom of Equitaine",
            "List": [
                " 635 - Equitan Lord, General, Fey Steed, Shield, Bastard Sword (Shield Breaker), Percival's Panoply, Black Knight's Tabard, Dragonfire Gem, Sainted, Valour",
                " 480 - Equitan Lord, Pegasus Charger, Shield, Lance (Divine Judgement), Basalt Infusion, Paladin, Honour",
                " 355 - Equitan Lord, Battle Standard Bearer (Legion Standard, Legion Standard), Great Weapon (Supernatural Dexterity), Essence of Mithril, Justice",
                "DEAD 240 - Damsel, Wizard Adept, Divination, Lightning Vambraces",
                " 395 - 45 Lowborn Levies, Shield, Champion, Musician, Standard Bearer",
                "DEAD 335 - 6 Feudal Knights, Champion, Musician, Standard Bearer (Relic Shroud)",
                "DEAD 220 - 8 Ordo Sergeants, Great Weapon",
                "DEAD 180 - 15 Lowborn Archers, Longbow and Expert Bowmen, Musician",
                " 550 - 8 Knights Penitent, Champion (Ordo Minister and Orison), Standard Bearer",
                "DEAD 345 - 6 Knights Resplendent, ",
                "DEAD 220 - 3 Sky Heralds, Paired Weapons, Champion",
                " 185 - Sacred Reliquary, ",
                "DEAD 360 - Fey Knight, Stream and Springs"
            ],
            "Objective": "Draw",
            "PointDifference": 2998,
            "Result": 16
        }
    ],
    "ReportTime": 1643765781
}
    armies = armies_from_warhall(example)