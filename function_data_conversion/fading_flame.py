from datetime import datetime, timezone
from multi_error import Multi_Error
from converter import Convert_lines_to_army_list
from data_classes import (
    Round,
    Event_types,
    Data_sources,
    ArmyEntry,
    Army_names,
)

faction_mapping = {
    1: Army_names["BEAST HERDS"],
    2:Army_names["DREAD ELVES"],
    3: Army_names["DWARVEN HOLDS"],
    4: Army_names["DAEMON LEGIONS"],
    5: Army_names["EMPIRE OF SONNSTAHL"],
    6: Army_names["HIGHBORN ELVES"],
    7: Army_names["INFERNAL DWARVES"],
    8: Army_names["KINGDOM OF EQUITAINE"],
    9: Army_names["OGRE KHANS"],
    10: Army_names["ORCS AND GOBLINS"],
    11: Army_names["SAURIAN ANCIENTS"],
    12: Army_names["SYLVAN ELVES"],
    13: Army_names["UNDYING DYNASTIES"],
    14: Army_names["VAMPIRE COVENANT"],
    15: Army_names["VERMIN SWARM"],
    16: Army_names["WARRIORS OF THE DARK GODS"],
    17: Army_names["ASKLANDERS"],
    18: Army_names["CULTISTS"],
    19: Army_names["HOBGOBLINS"],
    20: Army_names["MAKHAR"],
}
#objective_mapping = {
#     "1": Objectives["1 HOLD THE GROUND"],
#     "3": Objectives["2 BREAKTHROUGH"],
#     "4": Objectives["3 SPOILS OF WAR"],
#     "5": Objectives["5 CAPTURE THE FLAGS"],
#     "6": Objectives["6 SECURE TARGET"],
# }

def armies_from_fading_flame(data:dict) -> list[ArmyEntry]:
    event_name:str = data.get("name")
    games:list = data.get("games")

    errors: list[Exception] = []

    list_of_all_armies:list[ArmyEntry] = []

    for game in games:
        # Strip out important information
        game_id:str = game.get("id")
        game_result = game.get("result", {})
        if not game_result:
            raise ValueError("No result is a big issue")

        game_date = datetime.strptime(game_result.get("recordedAt"), "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)

        player1 = game_result.get("player1", {})
        player2 = game_result.get("player2", {})

        player1_id:str = player1.get("id")
        player1_vps:int = player1.get("victoryPoints")
        player1_bps:int = player1.get("battlePoints")
        player1_won_sec:bool = game_result.get("secondaryObjective") == 1

        player2_id:str = player2.get("id")
        player2_vps:int = player2.get("victoryPoints")
        player2_bps:int = player2.get("battlePoints")
        player2_won_sec:bool = game_result.get("secondaryObjective") == 2

        if not game_result.get("player1List") or not game_result.get("player2List"):
            errors.append(ValueError(f"No armies lists found\nGame id = {game_id}"))
            continue
        player1_list_no_army:str = game_result.get("player1List", {}).get("list", {})
        player1_faction:str = faction_mapping[game_result.get("player1List", {}).get("faction")]

        player2_list_no_army:str = game_result.get("player2List", {}).get("list")
        player2_faction:str = faction_mapping[game_result.get("player2List", {}).get("faction")]

        # build up compliant list of lines to be read in
        lines = "\n".join([player1_faction, player1_list_no_army, player2_faction, player2_list_no_army]).split("\n")
        try:
            list_of_armies = Convert_lines_to_army_list(event_name, lines)
        

            if not list_of_armies or len(list_of_armies) == 0:
                errors.append(ValueError(f"No armies found\nGame id = {game_id}"))
                continue
            if len(list_of_armies) == 1:
                errors.append(ValueError(f"2 armies were supplied but only 1 passed conversion\n{list_of_armies[0].player_name} playing {list_of_armies[0].army} passed.\nGame id = {game_id}"))
                continue

            player1_armyEntry = list_of_armies[0]
            player2_armyEntry = list_of_armies[1]


            # Set data and round data
            player1_armyEntry.fading_flame_player_id = player1_id
            player1_armyEntry.event_date = game_date
            player1_armyEntry.data_source = Data_sources.FADING_FLAMES
            player1_armyEntry.event_type = Event_types.CASUAL
            player1_armyEntry.round_performance = [Round(
                opponent=player2_armyEntry.army_uuid,
                result=player1_bps,
                secondary_points=player1_vps,
                round_number=1,
                fading_flame_game_id=game_id,
                won_secondary=player1_won_sec
            )]
            player1_armyEntry.calculate_total_tournament_points()

            player2_armyEntry.fading_flame_player_id = player2_id
            player2_armyEntry.event_date = game_date
            player2_armyEntry.data_source = Data_sources.FADING_FLAMES
            player2_armyEntry.event_type = Event_types.CASUAL
            player2_armyEntry.round_performance = [Round(
                opponent=player1_armyEntry.army_uuid,
                result=player2_bps,
                secondary_points=player2_vps,
                round_number=1,
                fading_flame_game_id=game_id,
                won_secondary=player2_won_sec
            )]
            player2_armyEntry.calculate_total_tournament_points()


            list_of_all_armies.extend(list_of_armies)
        except Multi_Error as e:
            errors.extend(e.errors)

    if errors:
        raise Multi_Error(errors)

    return list_of_all_armies



if __name__ == "__main__":
    import json
    with open("function_data_conversion\\fading_flame-test.json", "r") as json_file:
                data = json.load(json_file)
    output = armies_from_fading_flame(data)
    print(output)