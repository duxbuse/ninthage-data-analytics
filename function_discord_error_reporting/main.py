from os import getenv
import requests
from flask.wrappers import Request
from dotenv import load_dotenv



def function_discord_error_reporting(request:Request) -> int:
    load_dotenv()

    print(f"{request.json=}")
    TOKEN = getenv('DISCORD_WEBHOOK_TOKEN')
    WEBHOOK_ID = getenv('DISCORD_WEBHOOK_ID')
    FILE_NAME = "FILE_NAME_ABC123"

    url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "",
        "Content-Type": "application/json"
    }

    # For help on this https://gist.github.com/Birdie0/78ee79402a4301b1faf412ab5f1cdcf9
    json = {
        "content": "",
        "embeds": [{
            "author": {
            "name": FILE_NAME,
            },
            "title": "Errors:",
            "description": "",
            "color": 15224675,
            "fields": [
                {
                "name": "Core % not met",
                "value": "only `15%` not `20%`",
                "inline": True
                },
                {
                "name": "Unit: wizard",
                "value": "Unknown item: `big wand energy`",
                "inline": True
                },
                {
                "name": "Unit: spearmen",
                "value": "Incorrect price `200` should be `$2.50`",
                "inline": True
                },
                {
                "name": "Core % not met",
                "value": "only `15%` not `20%`",
                "inline": True
                },
                {
                "name": "Unit: wizard",
                "value": "Unknown item: `big wand energy`",
                "inline": True
                },
                {
                "name": "Unit: spearmen",
                "value": "Incorrect price `200` should be `$2.50`",
                "inline": True
                },
                {
                "name": "\u200B",
                "value": "Got an issue raise it [here](https://github.com/duxbuse/ninthage-data-analytics/issues)!"
                }
            ]
        }]
    }

    r = requests.post(url, headers=headers, json=json)

    print(f"upload status code: {r.status_code}")
    if r.status_code != 200 or r.status_code != 201:
        print(f"{r.text}")

    return r.status_code

if __name__ == "__main__":
    request_obj = Request.from_values(json="test")
    function_discord_error_reporting(request_obj)
