from os import getenv
import requests
from flask.wrappers import Request
from pathlib import Path
from discord_message_limits import *


def function_discord_success_reporting(request: Request):
    print(f"{request.json=}")
    request_body = request.json["data"]["body"]
    print(f"{request_body=}")

    TOKEN = getenv("DISCORD_WEBHOOK_TOKEN")
    WEBHOOK_ID = getenv("DISCORD_WEBHOOK_ID")
    FILE_NAME = Path(request_body["file_name"]).stem + ".docx"
    LIST_NUMBER = request_body["list_number"]
    OUTPUT_TABLE = request_body["output_table"]

    army_info = request.json["army_info"]["body"]
    print(f"{army_info=}")
    LOADED_TK_INFO = army_info["loaded_tk_info"]
    VALIDATION_COUNT = army_info["validation_count"]
    VALIDATION_ERRORS = army_info["validation_errors"]
    POSSIBLE_TK_NAMES = army_info["possible_tk_names"]

    url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "",
        "Content-Type": "application/json",
    }

    # https://discordjs.guide/popular-topics/embeds.html#editing-the-embedded-message-content
    all_errors = [
        dict(
            name=x["player_name"],
            value=truncate_field_values(x["validation_errors"]),
            inline=False,
        )
        for x in VALIDATION_ERRORS
    ]
    header = {
        "name": f"Additional Info",
        "value": f"Lists read = `{LIST_NUMBER}`\nTK info Loaded = `{LOADED_TK_INFO}`\nPossible TK name matches = `{POSSIBLE_TK_NAMES[:3]}`\nPassed Validation = `{VALIDATION_COUNT}/{LIST_NUMBER}`\nOutput Table = `{OUTPUT_TABLE}`",
        "inline": False,
    }
    footer = {
        "name": "\u200B",
        "value": "Got an issue raise it [here](https://github.com/duxbuse/ninthage-data-analytics/issues)!",
    }
    # limit len(fields) to 25 as that is a discord limit
    fields = [header, *all_errors[:23], footer]

    # For help on this https://gist.github.com/Birdie0/78ee79402a4301b1faf412ab5f1cdcf9
    json_message = {
        "content": "",
        "embeds": [
            {
                "author": {
                    "name": FILE_NAME,
                },
                "title": "Success:",
                "description": "",
                "color": 5236872,
                "fields": fields,
            }
        ],
    }
    truncate_message(json_message)
    r = requests.post(url, headers=headers, json=json_message)

    print(f"upload status code: {r.status_code}")
    if r.status_code != 200 or r.status_code != 201:
        print(f"{json_message=}")

    return r.text, r.status_code


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    army_info = {
        "bucket_name": "tournament-lists-json",
        "file_name": "Strength in Numbers 2021.json",
        "loaded_tk_info": False,
        "possible_tk_names": [],
        "validation_count": 25,
        "validation_errors": [
            {
                "player_name": "Brendan Hadder",
                "validation_errors": [
                    "Overlord: could not find option Gauntlets of Madzhab",
                    "Overlord: could not find option Arrogance",
                    "Vizier: could not find option Blessed Icon of Zalaman Tekash",
                    "Infernal Artillery: could not find option Titan Mortar",
                    "Infernal Artillery: could not find option Titan Mortar",
                    "Prophet: Invalid cost: 540, correct cost: 550",
                    "Overlord: Invalid cost: 480, correct cost: 365",
                    "Vizier: Invalid cost: 280, correct cost: 230",
                    "Citadel Guard: Invalid cost: 442, correct cost: 463",
                    "Infernal Warriors: Invalid cost: 460, correct cost: 470",
                    "Vassal Levies: Invalid cost: 224, correct cost: 229",
                    "Infernal Artillery: Invalid cost: 240, correct cost: 155",
                    "Infernal Artillery: Invalid cost: 240, correct cost: 155",
                    "Vassal Cavalry: Invalid cost: 190, correct cost: 200",
                    "Disciples of Lugar: Invalid cost: 489, correct cost: 484",
                    "Kadim Titan: Invalid cost: 475, correct cost: 495",
                    "Overlord: requires 2 Weapon Enchant",
                ],
            },
            {
                "player_name": "Andrew Rapmund",
                "validation_errors": [
                    "Infernal Artillery: could not find option Titan Mortar",
                    "Infernal Artillery: could not find option Titan Mortar",
                    "Infernal Engine: could not find option Rocket Battery",
                    "Vizier: Invalid cost: 290, correct cost: 285",
                    "Citadel Guard: Invalid cost: 633, correct cost: 662",
                    "Citadel Guard: Invalid cost: 589, correct cost: 616",
                    "Vassal Levies: Invalid cost: 205, correct cost: 210",
                    "Infernal Artillery: Invalid cost: 240, correct cost: 155",
                    "Infernal Artillery: Invalid cost: 240, correct cost: 155",
                    "Kadim Incarnates: Invalid cost: 470, correct cost: 490",
                    "Taurukh Anointed: Invalid cost: 280, correct cost: 290",
                    "Taurukh Anointed: Invalid cost: 280, correct cost: 290",
                    "Infernal Engine: Invalid cost: 470, correct cost: 420",
                ],
            },
            {
                "player_name": "Sean",
                "validation_errors": [
                    "Saurian Veteran: could not find option Light Armour (Taurosaur's Vigour) Carnosaur",
                    "Saurian Veteran: Invalid cost: 445, correct cost: 235",
                ],
            },
            {
                "player_name": "BRAD",
                "validation_errors": [
                    "Infernal Artillery: could not find option Titan Mortar",
                    "Taurukh Commissioner: Invalid cost: 450, correct cost: 460",
                    "Citadel Guard: Invalid cost: 501, correct cost: 524",
                    "Citadel Guard: Invalid cost: 501, correct cost: 524",
                    "Citadel Guard: Invalid cost: 457, correct cost: 478",
                    "Infernal Artillery: Invalid cost: 240, correct cost: 155",
                    "Taurukh Anointed: Invalid cost: 655, correct cost: 692",
                    "Taurukh Anointed: Invalid cost: 560, correct cost: 588",
                    "Kadim Titan: Invalid cost: 475, correct cost: 495",
                    "Army is overbudget: total cost is 4576",
                ],
            },
            {
                "player_name": "Sherman",
                "validation_errors": [
                    "Inquisitor: Invalid cost: 395, correct cost: 400",
                    "Inquisitor: Invalid cost: 355, correct cost: 360",
                    "Artificer: Invalid cost: 145, correct cost: 150",
                    "Electoral Cavalry: Invalid cost: 477, correct cost: 488",
                    "Imperial Guard: Invalid cost: 412, correct cost: 390",
                    "Army is overbudget: total cost is 4503",
                ],
            },
            {
                "player_name": "Maxwel Lepora",
                "validation_errors": [
                    "Infernal Artillery: could not find option Titan Mortar",
                    "Infernal Artillery: could not find option Titan Mortar",
                    "Taurukh Commissioner: Invalid cost: 495, correct cost: 505",
                    "Citadel Guard: Invalid cost: 618, correct cost: 647",
                    "Citadel Guard: Invalid cost: 596, correct cost: 624",
                    "Vassal Levies: Invalid cost: 396, correct cost: 386",
                    "Infernal Artillery: Invalid cost: 240, correct cost: 155",
                    "Infernal Artillery: Invalid cost: 240, correct cost: 155",
                    "Taurukh Anointed: Invalid cost: 635, correct cost: 658",
                ],
            },
            {
                "player_name": "Charles Sadler",
                "validation_errors": [
                    "Marshal: could not find option BSB Shield (Willow's Ward)"
                ],
            },
            {
                "player_name": "Carbonara Neil (C)",
                "validation_errors": [
                    "Warlock Outcast: could not find option Witchcraft - 380",
                    "Warlock Outcast: could not find option Obsidian Rock - 260",
                    "Silexian Officer: could not find option Seal of the 9th Fleet - 285",
                    "Could not find unit Silent Assassin - 180",
                    "Silexian Spears: could not find option Champion - 650",
                    "Silexian Auxiliaries: could not find option Musician - 240",
                    "Silexian Auxiliaries: could not find option Musician - 240",
                    "Obsidian Guard: could not find option Musician - 230",
                    "Obsidian Guard: could not find option Musician - 230",
                    "Judicators: could not find option Musician - 210",
                    "Judicators: could not find option Musician - 210",
                    "Divine Altar: could not find option Effigy of Dread - 200",
                    "Shadow Riders: could not find option Repeater Crossbow - 195",
                    "Shadow Riders: could not find option Repeater Crossbow - 195",
                    "Raptor Chariot: could not find option Halberd - 190",
                    "Raptor Chariot: could not find option Halberd - 190",
                    "Gorgons: could not find option Paired Weapons - 155",
                    "Could not find unit Mist Leviathan - 260",
                    "Warlock Outcast: Invalid cost: NaN, correct cost: 380",
                    "Warlock Outcast: Invalid cost: NaN, correct cost: 235",
                    "Silexian Officer: Invalid cost: NaN, correct cost: 245",
                    "Silexian Auxiliaries: Invalid cost: 15, correct cost: 230",
                    "Silexian Auxiliaries: Invalid cost: 15, correct cost: 230",
                    "Silexian Spears: Invalid cost: 40, correct cost: 640",
                    "Divine Altar: Invalid cost: NaN, correct cost: 200",
                    "Raptor Chariot: Invalid cost: NaN, correct cost: 190",
                    "Raptor Chariot: Invalid cost: NaN, correct cost: 190",
                    "Shadow Riders: Invalid cost: 5, correct cost: 170",
                    "Shadow Riders: Invalid cost: 5, correct cost: 170",
                    "Gorgons: Invalid cost: NaN, correct cost: 150",
                    "Obsidian Guard: Invalid cost: 10, correct cost: 220",
                    "Obsidian Guard: Invalid cost: 10, correct cost: 220",
                    "Judicators: Invalid cost: 10, correct cost: 200",
                    "Judicators: Invalid cost: 10, correct cost: 200",
                    " Core: required minimum cost is not fulfilled",
                ],
            },
            {
                "player_name": "Diavolo Pablo",
                "validation_errors": [
                    "Infernal Artillery: could not find option Rocket Battery",
                    "Infernal Artillery: could not find option Rocket Battery",
                    "Infernal Engine: could not find option Naphtha Thrower",
                    "Prophet: Invalid cost: 540, correct cost: 530",
                    "Citadel Guard: Invalid cost: 495, correct cost: 520",
                    "Citadel Guard: Invalid cost: 365, correct cost: 385",
                    "Vassal Levies: Invalid cost: 265, correct cost: 270",
                    "Infernal Artillery: Invalid cost: 280, correct cost: 155",
                    "Infernal Artillery: Invalid cost: 280, correct cost: 155",
                    "Vassal Cavalry: Invalid cost: 190, correct cost: 200",
                    "Vassal Cavalry: Invalid cost: 190, correct cost: 200",
                    "Taurukh Enforcers: Invalid cost: 425, correct cost: 430",
                    "Kadim Titan: Invalid cost: 475, correct cost: 495",
                    "Infernal Engine: Invalid cost: 440, correct cost: 420",
                ],
            },
            {
                "player_name": "Tom",
                "validation_errors": [
                    "Could not find unit Vampire Courtier (155)",
                    "Could not find unit Vampire Count (340)",
                    "Could not find unit Vampire Courtier (155)",
                    "Ghouls: could not find option Champion- 615",
                    "Could not find unit 3 Bat Swarms- 132",
                    "Could not find unit 3 Bat Swarms- 132",
                    "Could not find unit 8 Dire Wolves- 125",
                    "Could not find unit 8 Dire Wolves- 125",
                    "Could not find unit Altar of Undeath- 350",
                    "Barrow Guard: could not find option Standard",
                    "Barrow Guard: could not find option Banner of Speed- 326 5 Black Knights- 170",
                    "Ghasts: could not find option Champion- 434",
                    "Could not find unit 8 Spectral Hunters- 290",
                    "Could not find unit 4499/4500",
                    "Ghouls: Invalid cost: 40, correct cost: 605",
                    "Ghasts: Invalid cost: 6, correct cost: 424",
                    "Barrow Guard: Invalid cost: 18, correct cost: 230",
                    "Army: requires General",
                    "Army: requires a minimum of 4 units",
                    " Core Units: required minimum cost is not fulfilled",
                ],
            },
            {
                "player_name": "Scott",
                "validation_errors": [
                    "Runic Smith: could not find option Battle Rune Dragon Seeker",
                    "Runic Smith: could not find option Monster Seeker",
                    "Runic Smith: Invalid cost: 295, correct cost: 235",
                ],
            },
            {
                "player_name": "Frankie",
                "validation_errors": [
                    "High Prince: could not find option additionnal Learned Spells",
                    "High Prince: Invalid cost: 650, correct cost: 630",
                ],
            },
            {
                "player_name": '"Stone Cold" Steve',
                "validation_errors": [
                    "Chosen: could not find option Champion 5 Chosen Knights",
                    "Chosen: Invalid cost: 855, correct cost: 1000",
                    "Favour is limited to 1.",
                    "Standard Bearer is limited to 1.",
                    "Wasteland Torch is limited to 1 per Army.",
                ],
            },
            {
                "player_name": 'Fergus "The gimp with no limp"',
                "validation_errors": [
                    "High Prince: could not find option additionnal Learned Spells",
                    "High Prince: Invalid cost: 650, correct cost: 630",
                ],
            },
        ],
    }
    request_body = {
        "file_name": "Strength in Numbers 2021.json",
        "list_number": 39,
        "output_table": "all_lists:tournament_lists",
    }
    json_message = {"data": {"body": request_body}, "army_info": {"body": army_info}}
    request_obj = Request.from_values(json=json_message)
    function_discord_success_reporting(request_obj)
