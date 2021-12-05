from os import getenv
import requests
from flask.wrappers import Request
from dotenv import load_dotenv
import json



def function_discord_error_reporting(request:Request) -> requests.Response:
    load_dotenv()
    request_body = json.loads(request.json["data"]["body"])
    error = request_body["message"]


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
                "name": "Value Error",
                "value": error,
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

    return r

if __name__ == "__main__":
    request_obj = Request.from_values(json="test")
    function_discord_error_reporting(request_obj)
