from datetime import datetime
# from distutils.log import error
from pydantic import BaseModel, validator

from converter import Convert_lines_to_army_list
from data_classes import (
    Army_names,
    ArmyEntry,
    Data_sources,
    Deployments,
    Event_types,
    Maps,
    Objectives,
    Round,
)
from multi_error import Multi_Error


class warhall_player_data(BaseModel):
    ArmyName: str
    PlayerName: str
    List: list[str]
    Objective: str
    PointDifference: int
    Result: int

    @validator("ArmyName")
    def validate_army_name(cls, ArmyName):
        if ArmyName not in Army_names.values() and ArmyName != "":
            print(f"WARNING: {ArmyName=} is not a valid army name. Storing as is.")
            # raise ValueError(f"{ArmyName=} is not a valid army name")
        return ArmyName

    @validator("Objective")
    def validate_objective(cls, Objective):
        if Objective.casefold() not in [obj.casefold() for obj in ["Won", "Lost", "Draw", ""]]:
            print(f"WARNING: {Objective=} is not a valid objective. Storing as is.")
            # raise ValueError(f"{Objective=} is not a valid objective")
        return Objective

    @validator("Result")
    def validate_result(cls, Result):
        if not 0 <= Result <= 20:
            print(f"WARNING: {Result=} is not a valid result from 0-20. Storing as is.")
            # raise ValueError(f"{Result=} is not a valid result from 0-20")
        return Result


class warhall_data(BaseModel):
    Deployment: str
    Map: str
    Objective: str
    PlayersData: list[warhall_player_data]
    ReportTime: int

    @validator("Deployment")
    def validate_deployment(cls, Deployment):
        if Deployment not in Deployments:
            print(f"WARNING: {Deployment=} is not a valid deployment. Storing as is.")
            return Deployment # Return original if not found
            # raise ValueError(f"{Deployment=} is not a valid deployment")
        return Deployments[Deployment]

    @validator("Map", pre=True)
    def validate_map(cls, Map):
        if isinstance(Map, int):
            try:
                Map = list(enumerate(Maps.values()))[Map][
                    1
                ]  # convert int to string from our list of maps
            except IndexError:
                print(f"WARNING: Map index {Map} out of range. Storing as is.")
                return str(Map)
        if Map not in Maps.values():
            print(f"WARNING: {Map=} is not a valid map. Storing as is.")
            return Map # Return original
            # raise ValueError(f"{Map=} is not a valid map")
        return Map

    @validator("Objective")
    def validate_objective(cls, Objective):
        if Objective not in Objectives:
            print(f"WARNING: {Objective=} is not a valid objective. Storing as is.")
            return Objective # Return original
            # raise ValueError(f"{Objective=} is not a valid objective")
        return Objectives[Objective]


def mark_half_or_dead(player_data: warhall_player_data, army_data: ArmyEntry) -> None:
    """
    Calculate the half points and fully dead from the warhall data
    """
    if not army_data.units:
        return
    if len(player_data.List) != len(army_data.units):
        raise ValueError(
            f"{len(player_data.List)=} should be the same length as {len(army_data.units)=}"
        )

    for unit in zip(player_data.List, army_data.units):
        if unit[0][:4] == "DEAD":
            unit[1].dead = True
        else:
            unit[1].dead = False

        if unit[0][:4] == "HALF":
            unit[1].half = True
        else:
            unit[1].half = False


def armies_from_warhall(data: dict) -> tuple[list[ArmyEntry], list[str]]:
    errors: list[Exception] = []
    now = datetime.now()
    try:
        data_obj = warhall_data(**data)
    except ValueError as e:
        errors.append(e)
    except ValueError as e:
        errors.append(e)
        return [], [str(e)]

    if len(data_obj.PlayersData) != 2:
        errors.append(ValueError(f"{data_obj.PlayersData=} Should only be 2 players"))

    scored_game = True
    if data_obj.PlayersData[0].Result == 0 and data_obj.PlayersData[0].Result == 0:
        scored_game = False
        # score should be null because it is unknown

    list_of_armies = list[ArmyEntry]()
    # load in all the army data
    for player in data_obj.PlayersData:
        army = "Could not convert"
        try:
            army = Convert_lines_to_army_list(
                event_name="warhall",
                event_date=now,
                lines=[player.ArmyName] + player.List,
            ).pop() if player.List else ArmyEntry()

            army_round = Round(
                result=player.Result if scored_game else None,
                won_secondary=player.Objective == "Won" if data_obj.Objective != "" else  None,
                map_selected = data_obj.Map if data_obj.Map != 0 else  None,
                deployment_selected=data_obj.Deployment if data_obj.Deployment != "" else  None,
                objective_selected=data_obj.Objective if data_obj.Objective != "" else  None,
            )
            army.player_name = player.PlayerName
            army.round_performance = [army_round]
            army.data_source = Data_sources.WARHALL
            army.event_type = Event_types.CASUAL
            army.event_date = now
            army.calculate_total_points()
            mark_half_or_dead(player, army)
            list_of_armies.append(army)
        except ValueError as e:
            errors.append(ValueError(f"Failed {army=}"))
            errors.append(e)

    if len(list_of_armies) != 2:
        e = ValueError(f"Only {len(list_of_armies)} army list/s loaded.\n")
        errors.append(e)

    # set each other as opponents and set points killed
    for i, army in enumerate(list_of_armies):
        army.round_performance[0].opponent = list_of_armies[i - 1].army_uuid
        army.round_performance[0].secondary_points = list_of_armies[
            i - 1
        ].points_killed()

    # if errors:
    #     raise Multi_Error(errors)

    return list_of_armies, [str(e) for e in errors]


if __name__ == "__main__":
    from main import download_blob
    from os import remove
    import json

    file_name = "03dc3b35-3987-4fc4-a106-db1d04f8cb0f.json"
    download_file_path = f"./{file_name}"

    downloaded_warhall_blob = download_blob("warhall", file_name)
    downloaded_warhall_blob.download_to_filename(download_file_path)
    if downloaded_warhall_blob:
        print(
            f"Downloaded {file_name} from warhall to {download_file_path}"
        )
    with open(download_file_path, "r") as json_file:
        data = json.load(json_file)
        print(f"Loaded data")
    remove(download_file_path)
    list_of_armies = armies_from_warhall(data)
    print(f"Finished")
