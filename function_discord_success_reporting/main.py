from os import getenv
import requests
from flask.wrappers import Request
from pathlib import Path
from dotenv import load_dotenv
from math import ceil
import json




def function_discord_success_reporting(request:Request):
    load_dotenv()

    request_body = request.json["data"]["body"]
    print(f"{request_body=}")

    TOKEN = getenv('DISCORD_WEBHOOK_TOKEN')
    WEBHOOK_ID = getenv('DISCORD_WEBHOOK_ID')
    FILE_NAME = Path(request_body['file_name']).stem + ".docx"
    LIST_NUMBER = request_body['list_number']
    OUTPUT_TABLE = request_body['output_table']

    army_info = request.json["army_info"]["body"]
    LOADED_TK_INFO = army_info['loaded_tk_info']
    VALIDATION_COUNT = army_info['validation_count']
    VALIDATION_ERRORS = army_info['validation_errors']

    url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "",
        "Content-Type": "application/json"
    }


    # https://discordjs.guide/popular-topics/embeds.html#editing-the-embedded-message-content
    all_errors = [dict(name=x["player_name"], value=truncate_field(x["validation_errors"]), inline=True) for x in VALIDATION_ERRORS]
    header = {
                "name": f"Additional Info",
                "value": f"Lists read = `{LIST_NUMBER}`\nTK info Loaded = `{LOADED_TK_INFO}`\nPassed Validation = `{VALIDATION_COUNT}`/`{LIST_NUMBER}`\nOutput Table = `{OUTPUT_TABLE}`",
                "inline": True
            }
    footer = {
                "name": "\u200B",
                "value": "Got an issue raise it [here](https://github.com/duxbuse/ninthage-data-analytics/issues)!"
                }
    # limit len(fields) to 25 as that is a discord limit
    fields = [header, *all_errors[:23] , footer]


    # For help on this https://gist.github.com/Birdie0/78ee79402a4301b1faf412ab5f1cdcf9
    json_message = {
        "content": "",
        "embeds": [{
            "author": {
            "name": FILE_NAME,
            },
            "title": "Success:",
            "description": "",
            "color": 5236872,
            "fields": fields
        }]
    }
    truncate_message(json_message)
    r = requests.post(url, headers=headers, json=json_message)

    print(f"upload status code: {r.status_code}")
    if r.status_code != 200 or r.status_code != 201:
        print(f"{json_message=}")

    return r.text, r.status_code

def truncate_field(value: str) -> str:
    DISCORD_EMBED_FIELD_VALUE = 1024
    # message will exceed discords limits
    if len(value) > DISCORD_EMBED_FIELD_VALUE:
        chars_to_remove = len(value) - DISCORD_EMBED_FIELD_VALUE
        truncation_warning = " [...] "
        half_of_chars = ceil((chars_to_remove + len(truncation_warning)) / 2) 
        midpoint = ceil(len(value) / 2)
        new_value = value[:midpoint-half_of_chars] + truncation_warning + value[midpoint+half_of_chars:]
        return new_value
    return value

def truncate_message(message: dict):
    DISCORD_EMBED_TOTAL_LENGTH = 6000
    current_total = character_total(message)
    while current_total > DISCORD_EMBED_TOTAL_LENGTH:
        # Drop the last non footer field until passing the discord requirements
        message["embeds"][0]["fields"] = [*message["embeds"][0]["fields"][:-3], message["embeds"][0]["fields"][-1]]
        # reduce the character count buy what was just removed
        current_total -= len(json.dumps(message["embeds"][0]["fields"][-2]["name"]))
        current_total -= len(json.dumps(message["embeds"][0]["fields"][-2]["value"]))

def character_total(message: dict) -> int:
    embed = message["embeds"][0]
    total = 0
    total += len(json.dumps(embed["title"]))
    total += len(json.dumps(embed["description"]))
    total += len(json.dumps(embed["author"]["name"]))
    # total += len(json.dumps(embed["footer"])) # We are not using footer presently
    for field in embed["fields"]:
        total += len(json.dumps(field["name"]))
        total += len(json.dumps(field["value"]))
    return total

if __name__ == "__main__":
    json_message = {'data': {'body': ""}}
    request_obj = Request.from_values(json="json_message")
    function_discord_success_reporting(request_obj)
