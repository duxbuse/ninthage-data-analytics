from os import getenv
from typing import List
import requests
from flask.wrappers import Request
from dotenv import load_dotenv
import json



def function_discord_error_reporting(request:Request):
    load_dotenv()
    print(f"{request.json=}")
    request_body = json.loads(request.json["error"]["body"])
    errors:List[str] = request_body["message"]["args"]
    data = request.json["data"]
    FILE_NAME = data["name"]


    print(f"{errors=}")
    TOKEN = getenv('DISCORD_WEBHOOK_TOKEN')
    WEBHOOK_ID = getenv('DISCORD_WEBHOOK_ID')

    url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "",
        "Content-Type": "application/json"
    }


    all_errors = [dict(name="Value Error", value=x, inline=True) for x in errors]
    footer = {
                "name": "\u200B",
                "value": "Got an issue raise it [here](https://github.com/duxbuse/ninthage-data-analytics/issues)!"
                }
    fields = [*all_errors , footer]

    # For help on this https://gist.github.com/Birdie0/78ee79402a4301b1faf412ab5f1cdcf9
    json_message = {
        "content": "",
        "embeds": [{
            "author": {
            "name": FILE_NAME,
            },
            "title": "Errors:",
            "description": "",
            "color": 15224675,
            "fields": fields
        }]
    }

    r = requests.post(url, headers=headers, json=json_message)

    print(f"discord status code: {r.status_code}")
    if r.status_code != 200 or r.status_code != 204:
        return r.text, r.status_code

    return "reported to discord", 200

if __name__ == "__main__":
    request_obj = Request.from_values(json="test")
    function_discord_error_reporting(request_obj)
