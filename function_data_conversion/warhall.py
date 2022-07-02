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
from pydantic import BaseModel, validator

from multi_error import Multi_Error
class warhall_player_data(BaseModel):
    ArmyName: str
    List: list[str]
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
    PlayersData: list[warhall_player_data]
    ReportTime: int

    @validator("Deployment")
    def validate_deployment(cls, Deployment):
        if Deployment not in Deployments.values():
            raise ValueError(f"{Deployment=} is not a valid deployment")
        return Deployment

    @validator("Map", pre=True)
    def validate_map(cls, Map):
        if isinstance(Map, int):
            Map = list(enumerate(Maps.values()))[Map][1] # convert int to string from our list of maps
        if Map not in Maps.values():
            raise ValueError(f"{Map=} is not a valid map")
        return Map

    @validator("Objective")
    def validate_objective(cls, Objective):
        if Objective not in Objectives.values():
            raise ValueError(f"{Objective=} is not a valid objective")
        return Objective

def mark_dead(player_data: warhall_player_data, army_data: ArmyEntry) -> None:
    """
    Calculate the dead from the warhall data
    """
    if not army_data.units or len(player_data.List) != len(army_data.units):
        raise ValueError(f"{len(player_data.List)=} should be the same length as {len(army_data.units)=}")

    for unit in zip(player_data.List, army_data.units):
        if unit[0][:4] == "DEAD":
            unit[1].dead = True
        else:
            unit[1].dead = False

def armies_from_warhall(data:dict) -> list[ArmyEntry]:
    errors: list[Exception] = []
    try:
        data_obj = warhall_data(**data)
    except ValueError as e:
        errors.append(e)
        raise Multi_Error(errors)

    if len(data_obj.PlayersData) != 2:
        errors.append(ValueError(f"{data_obj.PlayersData=} Should only be 2 players"))

    list_of_armies = list[ArmyEntry]()
    # load in all the army data
    for player in data_obj.PlayersData:
        try:
            army = Convert_lines_to_army_list("warhall", [player.ArmyName] + player.List).pop()
            army_round = Round(
                result=player.Result,
                won_secondary=player.Objective == "Won",
                map_selected=data_obj.Map,
                deployment_selected=data_obj.Deployment,
                objective_selected=data_obj.Objective,
            )
            army.round_performance = [army_round]
            army.data_source = Data_sources.WARHALL
            army.event_type = Event_types.CASUAL
            army.calculate_total_points()
            mark_dead(player, army)
            list_of_armies.append(army)
        except ValueError as e:
            errors.append(e)

    # set each other as opponents
    for i, army in enumerate(list_of_armies):
        army.round_performance[0].opponent = list_of_armies[i-1].army_uuid
        army.round_performance[0].secondary_points = list_of_armies[i-1].points_killed()

    # check that calculated secondary points == points difference
    calculated_difference = list_of_armies[0].round_performance[0].secondary_points - list_of_armies[1].round_performance[0].secondary_points
    if abs(calculated_difference) != abs(data_obj.PlayersData[0].PointDifference):
        errors.append(ValueError(f"{abs(calculated_difference)=} should be {abs(data_obj.PlayersData[0].PointDifference)=}"))

    if errors:
        raise Multi_Error(errors)

    return list_of_armies

if __name__ == "__main__":
    example = {
    "Deployment": "Dawn Assault",
    "Map": 5,
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
    print(bool(armies))