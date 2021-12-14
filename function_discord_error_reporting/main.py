from os import getenv
import requests
from flask.wrappers import Request
from dotenv import load_dotenv

from http400 import handle_400
from http408 import handle_408
from http_error_catch_all import handle_error
from discord_message_limits import truncate_message


def function_discord_error_reporting(request: Request):
    FILE_NAME = request.json["data"]["name"]
    json_message = {
        "content": "",
        "embeds": [
            {
                "author": {
                    "name": FILE_NAME,
                },
                "title": "Errors:",
                "description": "",
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

    error_code: int = request.json["error"]["code"]
    if error_code == 400:
        handle_400(request, json_message)

    elif error_code == 408:
        handle_408(request, json_message)

    else:
        handle_error(request, json_message)

    truncated_message = truncate_message(json_message)
    print(f"{truncated_message=}")

    TOKEN = getenv("DISCORD_WEBHOOK_TOKEN")
    WEBHOOK_ID = getenv("DISCORD_WEBHOOK_ID")

    url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "",
        "Content-Type": "application/json",
    }

    r = requests.post(url, headers=headers, json=truncated_message)

    print(f"discord status code: {r.status_code}")
    print(f"discord text: {r.text}")
    if r.status_code != 200 or r.status_code != 204:
        return r.text, r.status_code

    return "reported to discord", 200


if __name__ == "__main__":
    load_dotenv()
    json_message = {
        "data": {
            "bucket": "tournament-lists",
            "contentType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "crc32c": "kBvh6w==",
            "etag": "CJv42KWL4fQCEAE=",
            "generation": "1639409228594203",
            "id": "tournament-lists/Cossacks Raid - Master.docx/1639409228594203",
            "kind": "storage#object",
            "md5Hash": "z1DQCBrK4l8ONRfCMgW60A==",
            "mediaLink": "https://www.googleapis.com/download/storage/v1/b/tournament-lists/o/Cossacks%20Raid%20-%20Master.docx?generation=1639409228594203&alt=media",
            "metageneration": "1",
            "name": "Cossacks Raid - Master.docx",
            "selfLink": "https://www.googleapis.com/storage/v1/b/tournament-lists/o/Cossacks%20Raid%20-%20Master.docx",
            "size": "63743",
            "storageClass": "STANDARD",
            "timeCreated": "2021-12-13T15:27:08.627Z",
            "timeStorageClassUpdated": "2021-12-13T15:27:08.627Z",
            "updated": "2021-12-13T15:27:08.627Z",
        },
        "error": {
            "body": "Error: could not handle the request\n",
            "code": 408,
            "headers": {
                "Alt-Svc": 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000,h3-Q050=":443"; ma=2592000,h3-Q046=":443"; ma=2592000,h3-Q043=":443"; ma=2592000,quic=":443"; ma=2592000; v="46,43"',
                "Cache-Control": "private",
                "Content-Length": "36",
                "Content-Type": "text/plain; charset=utf-8",
                "Date": "Mon, 13 Dec 2021 15:29:09 GMT",
                "Server": "Google Frontend",
                "X-Cloud-Trace-Context": "2e5ad196cccd48bce38f390afb9b2e41;o=1",
                "X-Content-Type-Options": "nosniff",
            },
            "message": "HTTP server responded with error code 408",
            "tags": ["HttpError"],
        },
    }
    request_obj = Request.from_values(json=json_message)
    function_discord_error_reporting(request_obj)
