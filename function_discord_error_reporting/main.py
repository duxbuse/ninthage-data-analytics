from os import getenv
import requests
from flask.wrappers import Request

from http400 import handle_400
from http408 import handle_408
from http_error_catch_all import handle_error
from discord_message_limits import truncate_message


def function_discord_error_reporting(request: Request):
    if request.json:
        print(f"{request.json=}")
        if not request.json.get("data") and not request.json.get("data").get("name"):
            pass  # TODO: We should raise an exception here, but we also want to submit this info back to discord

        # If we add some additional custom file name use that rather than the generic one
        FILE_NAME = request.json["data"]["name"]
        if request.json["error"].get("name") and request.json["error"].get("event_id"): #If available use more detailed name
            FILE_NAME = f"{request.json['error']['name']}_{request.json['error']['event_id']}"

        WORKFLOW_ID = request.json["workflow_id"]

        json_message = {
            "content": "",
            "embeds": [
                {
                    "author": {
                        "name": FILE_NAME,
                    },
                    "title": "Errors:",
                    
                    "description": f"[WORKFLOW](https://console.cloud.google.com/workflows/workflow/us-central1/workflow_parse_lists/execution/{WORKFLOW_ID}?project=ninthage-data-analytics)",
                    "color": 15224675,
                    "fields": [
                        {
                            "name": "\u200B",
                            "value": "Got an issue raise it [here](https://github.com/duxbuse/ninthage-data-analytics/issues)!",
                        }
                    ],
                }
            ],
        }
        error_code: int = 418
        if request.json.get("error_code"):
            error_code = request.json.get("error_code").get("code", 418)
        elif request.json.get("error"):
            error_code = request.json.get("error").get("code", 418)

        print(f"{error_code=}")
        if error_code == 400:  # value errors
            handle_400(request, json_message)

        elif error_code == 408:  # Timeout
            handle_408(request, json_message)

        else:  # default
            handle_error(request, json_message)
        print(f"{json_message=}")

        truncate_message(json_message)
        print(f"after truncation {json_message=}")

        TOKEN = getenv("DISCORD_WEBHOOK_TOKEN")
        WEBHOOK_ID = getenv("DISCORD_WEBHOOK_ID")

        url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
        headers = {
            "Authorization": f"Bot {TOKEN}",
            "Accept": "application/json",
            "User-Agent": "ninthage-data-analytics/1.1.0",
            "Content-Type": "application/json",
        }

        r = requests.post(url, headers=headers, json=json_message)

        print(f"discord status code: {r.status_code}")
        print(f"discord text: {r.text}")
        if r.status_code != 200 or r.status_code != 204:
            return r.text, r.status_code

        return "reported to discord", 200
    return "There was no json payload", 500


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    json_message = {'workflow_id': "36bbcebf-7846-43e4-89f0-556e82f98954", 'data': {'event_id': '61945055989a624fe73e77bc', 'name': 'newrecruit_tournament.json'}, 'error': {'body': {'message': [''], 'name': '61945055989a624fe73e77bc'}, 'code': 400, 'headers': {'Alt-Svc': 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000,h3-Q050=":443"; ma=2592000,h3-Q046=":443"; ma=2592000,h3-Q043=":443"; ma=2592000,quic=":443"; ma=2592000; v="46,43"', 'Cache-Control': 'private', 'Content-Length': '51', 'Content-Type': 'application/json', 'Date': 'Wed, 03 Aug 2022 04:13:37 GMT', 'Function-Execution-Id': '0h7c0k2zksjj', 'Server': 'Google Frontend', 'X-Cloud-Trace-Context': '0beac778f6a680cc9d257e8ee4d80b76;o=1'}, 'message': 'HTTP server responded with error code 400', 'tags': ['HttpError']}}
    request_obj = Request.from_values(json=json_message)
    function_discord_error_reporting(request_obj)
