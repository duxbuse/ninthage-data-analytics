from os import getenv
import requests
from flask.wrappers import Request
from pathlib import Path
from dotenv import load_dotenv
import json




def function_discord_success_reporting(request:Request):
    load_dotenv()

    request_body = request.json["data"]["body"]

    TOKEN = getenv('DISCORD_WEBHOOK_TOKEN')
    WEBHOOK_ID = getenv('DISCORD_WEBHOOK_ID')
    FILE_NAME = Path(request_body['file_name']).stem + ".docx"
    LIST_NUMBER = request_body['list_number']
    OUTPUT_TABLE = request_body['output_table']

    army_info = request.json["army_info"]["body"]
    LOADED_TK_INFO = army_info['loaded_tk_info']
    VALIDATION_COUNT = army_info['validation_count']

    url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "",
        "Content-Type": "application/json"
    }

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
            "fields": [
                {
                "name": f"Additional Info",
                "value": f"Lists read = `{LIST_NUMBER}`\nTK info Loaded = `{LOADED_TK_INFO}`\nPassed Validation = `{VALIDATION_COUNT}`/`{LIST_NUMBER}`\nOutput Table = `{OUTPUT_TABLE}`",
                "inline": True
                },
                {
                "name": "\u200B",
                "value": "Got an issue raise it [here](https://github.com/duxbuse/ninthage-data-analytics/issues)!"
                }
            ]
        }]
    }

    r = requests.post(url, headers=headers, json=json_message)

    print(f"upload status code: {r.status_code}")
    if r.status_code != 200 or r.status_code != 201:
        print(f"{r.text}")

    return "reported to discord", 200

if __name__ == "__main__":
    json_message = {'data': {'body': ""}}
    request_obj = Request.from_values(json="json_message")
    function_discord_success_reporting(request_obj)
