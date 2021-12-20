# Game reported through web form since flattened=false everything is now a list so we need a lot of [0]
from datetime import datetime, timezone
from converter import Convert_lines_to_army_list
from data_classes import (
    Round,
    Event_types,
    ArmyEntry,
    Maps,
    Deployments,
    Objectives,
    Magic,
)


def armies_from_report(data: dict, event_name: str) -> list[ArmyEntry]:
    name1 = "name-not-provided"
    if data.get("player1_name", [None])[0]:
        name1 = data.get("player1_name")[0]
    player1_list = "\n".join([name1, data.get("player1_army")[0]])
    player2_list = ""
    name2 = "name-not-provided"
    if data.get("player2_army", [None])[0]:
        if data.get("player2_name", [None])[0]:
            name2 = data.get("player2_name")[0]

        player2_list = "\n".join([name2, data.get("player2_army")[0]])

    lines = "\n".join([player1_list, player2_list]).split("\n")
    list_of_armies = Convert_lines_to_army_list(event_name, lines)
    if len(list_of_armies) == 0:
        raise ValueError("No armies found")
    player1_army = list_of_armies[
        0
    ]  # TODO: There is a case here where player 1 is missing but player 2 exists and then we rename player2's army list as player 1
    player2_army = None
    if data.get("player2_army", [None])[0]:
        player2_army = list_of_armies[1]

    player1_round = None
    if any(
        [
            data.get("player2_army"),
            data.get("player1_score"),
            data.get("player1_vps"),
            data.get("won_secondary", [None])[0] == "player1",
            data.get("who_deployed", [None])[0] == "player1",
            data.get("dropped_all", [None])[0] == "player1",
            data.get("who_started", [None])[0] == "player1",
            data.get("map_selected"),
            data.get("deployment_selected"),
            data.get("objective_selected"),
            data.get("player1_magic"),
        ]
    ):
        player1_round = Round(
            round_number=1,
        )

    player2_round = None
    if any(
        [
            data.get("player2_army"),
            data.get("player2_score"),
            data.get("player2_vps"),
            data.get("won_secondary", [None])[0] == "player2",
            data.get("who_deployed", [None])[0] == "player2",
            data.get("dropped_all", [None])[0] == "player2",
            data.get("who_started", [None])[0] == "player2",
            data.get("map_selected"),
            data.get("deployment_selected"),
            data.get("objective_selected"),
            data.get("player2_magic"),
        ]
    ):
        if not player2_army:
            player2_army = ArmyEntry()
            list_of_armies.append(player2_army)
        player2_round = Round(
            round_number=1,
        )

    # Opponent exists
    if player1_round and player2_round:
        player1_round.opponent = player2_army.army_uuid
        player2_round.opponent = player1_army.army_uuid

    # Set scores
    score_total = 0
    if data.get("player1_score", [None])[0]:
        player1_round.result = int(data.get("player1_score")[0])
        score_total += player1_round.result
    if data.get("player2_score", [None])[0]:
        player2_round.result = int(data.get("player2_score")[0])
        score_total += player2_round.result

    if score_total > 20:
        raise ValueError(f"Sum of scores exceed 20\n{player1_round=}\n{player2_round=}")

    # Set secondary points
    if data.get("player1_vps", [None])[0]:
        player1_round.secondary_points = int(data.get("player1_vps")[0])
    if data.get("player2_vps", [None])[0]:
        player2_round.secondary_points = int(data.get("player2_vps")[0])

    # Who won secondary
    if data.get("won_secondary", [None])[0] == "player1":
        player1_round.won_secondary = True
    elif data.get("won_secondary", [None])[0] == "player2":
        player2_round.won_secondary = True

    # Who deployed first
    if data.get("who_deployed", [None])[0] == "player1":
        player1_round.deployed_first = True
    elif data.get("who_deployed", [None])[0] == "player2":
        player2_round.deployed_first = True

    # Who dropped all
    if data.get("dropped_all", [None])[0] == "player1":
        player1_round.deployed_everything = True
    elif data.get("dropped_all", [None])[0] == "player2":
        player2_round.deployed_everything = True

    # Who had first turn
    if data.get("who_started", [None])[0] == "player1":
        player1_round.first_turn = True
    elif data.get("who_started", [None])[0] == "player2":
        player2_round.first_turn = True

    # Game date
    if data.get("game_date", [None])[0]:  # 2021-12-24'
        game_date = datetime.strptime(data.get("game_date")[0], "%Y-%m-%d").replace(
            tzinfo=timezone.utc
        )

        player1_army.event_date = game_date
        if player2_army:
            player2_army.event_date = game_date

    # Map played
    if data.get("map_selected", [None])[0]:
        player1_round.map_selected = Maps[data.get("map_selected")[0].upper()]
        player2_round.map_selected = Maps[data.get("map_selected")[0].upper()]

    # Deployment played
    if data.get("deployment_selected", [None])[0]:
        player1_round.deployment_selected = Deployments[
            data.get("deployment_selected")[0].upper()
        ]
        player2_round.deployment_selected = Deployments[
            data.get("deployment_selected")[0].upper()
        ]

    # Objective played
    if data.get("objective_selected", [None])[0]:
        player1_round.objective_selected = Objectives[
            data.get("objective_selected")[0].upper()
        ]
        player2_round.objective_selected = Objectives[
            data.get("objective_selected")[0].upper()
        ]

    # Spells taken
    if data.get("player1_magic"):
        player1_round.spells_selected = [
            Magic[x.upper()] for x in data.get("player1_magic") or []
        ]
    if data.get("player2_magic"):
        player2_round.spells_selected = [
            Magic[x.upper()] for x in data.get("player2_magic") or []
        ]

    if player1_round:
        player1_army.round_performance = [player1_round]
    if player2_round:
        player2_army.round_performance = [player2_round]

    player1_army.calculate_total_tournament_points()
    player1_army.event_type = Event_types.CASUAL
    if player2_army:
        player2_army.calculate_total_tournament_points()
        player2_army.event_type = Event_types.CASUAL

    return list_of_armies
