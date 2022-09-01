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
    POSSIBLE_TK_NAMES = army_info.get("possible_tk_names", ["N/A"])
    if not POSSIBLE_TK_NAMES:
        POSSIBLE_TK_NAMES = ["N/A"]
    VALIDATION_ERRORS = army_info["validation_errors"]

    url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "ninthage-data-analytics/1.1.0",
        "Content-Type": "application/json",
    }

    # https://discordjs.guide/popular-topics/embeds.html#editing-the-embedded-message-content
    all_errors = [
        dict(
            name=x.get("player_name", "No Player Name") or "No Player Name",
            value=truncate_field_values(x.get("validation_errors", "No Errors")) or "No Errors",
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

    print(f"upload status code: {r.status_code}\n{r.text=}")
    if r.status_code == 429:
        print(f"Discord API rate limit exceeded\n{r.headers=}")
    elif r.status_code != 200 or r.status_code != 201 or r.status_code != 204:
        print(f"{json_message=}")

    return r.text, r.status_code


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    army_info={'bucket_name': 'tournament-lists-json', 'file_name': 'Polish Team Championships.json', 'loaded_tk_info': True, 'possible_tk_names': None, 'validation_count': 3, 'validation_errors': [{'player_name': 'Daniel Schaefer', 'validation_errors': ['Army: Use version 2 Nd Edition, Version 2022', 'Army: Characters use 1800 points - excess 2 points', 'Army: Chained Beasts use 1350 points - excess 1 points', 'Army: Core use 917 points', 'Army: Special use 710 points']}, {'player_name': 'Marcin "Krzemi" Krzemień', 'validation_errors': ['Army: Use version 2 Nd Edition, Version 2022', 'Unit: Marauding Giant, Could not find option Wizard Apprentice', 'Army: Characters use 1345 points', 'Army: Special use 2255 points', 'Army: Core use 900 points']}, {'player_name': 'Terminator', 'validation_errors': ['Army: Use version 2 Edition, Version 2022', 'Army: Invalid cost: 4499, correct cost: 4479', 'Unit: Minotaur Chieftain, invalid cost: 470, correct cost: 450', 'Army: Characters use 1230 points', 'Army: Core use 900 points', 'Army: Ambush Predators use 602 points', 'Army: Special use 1409 points', 'Army: Terrors of the Wild use 960 points']}, {'player_name': 'Maciej Pasek', 'validation_errors': ['Army: Use version 2 Nd Edition, Version 2022', 'Army: Invalid cost: 4499, correct cost: 4374', 'Unit: Vampire Knights, Could not find option Blood Ties', 'Unit: Vampire Knights, invalid cost: 614, correct cost: 489', 'Army: Characters use 1795 points', 'Army: Core use 1125 points', 'Army: Special use 455 points', 'Army: Swift Death use 1124 points']}]}
    request_body = {
        "file_name": "test",
        "list_number": 39,
        "output_table": "all_lists:tournament_lists",
    }
    json_message = {"data": {"body": request_body}, "army_info": {"body": army_info}}
    request_obj = Request.from_values(json=json_message)
    function_discord_success_reporting(request_obj)
