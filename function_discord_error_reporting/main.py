from os import getenv
from typing import List
import requests
from flask.wrappers import Request
from dotenv import load_dotenv
import json
from math import ceil



def function_discord_error_reporting(request:Request):
    print(f"{request.json=}")
    request_body = request.json["error"]["body"]
    errors:List[str] = request_body["message"]
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

    truncated_message = truncate_message(json_message)
    print(f"{truncated_message=}")

    r = requests.post(url, headers=headers, json=truncate_message(truncated_message))

    print(f"discord status code: {r.status_code}")
    print(f"discord text: {r.text}")
    if r.status_code != 200 or r.status_code != 204:
        return r.text, r.status_code

    return "reported to discord", 200

def truncate_message(message: dict) -> dict:
    DISCORD_EMBED_FIELD_VALUE = 1024
    message_as_string = json.dumps(message)
    # message will exceed discords limits
    if len(message_as_string) > DISCORD_EMBED_FIELD_VALUE:
        chars_to_remove = len(message_as_string) - DISCORD_EMBED_FIELD_VALUE
        fields = message["embeds"][0]["fields"]
        # TODO: assuming first field is the problem
        problem_field = fields[0]["value"]
        if len(problem_field) > chars_to_remove:
            truncation_warning = " [...] "
            half_of_chars = ceil((chars_to_remove + len(truncation_warning)) / 2) 
            midpoint = ceil(len(problem_field) / 2)
            new_field = problem_field[:midpoint-half_of_chars] + truncation_warning + problem_field[midpoint+half_of_chars:]
            message["embeds"][0]["fields"][0]["value"] = new_field
            return message
        else:
            # Assumption was wrong
            raise ValueError("message truncation failed, due to not a singular large first field")
    # Message needs to truncation
    return message

if __name__ == "__main__":
    load_dotenv()
    json_message = {'data': {'bucket': 'tournament-lists', 'contentType': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'crc32c': '91b1Ng==', 'etag': 'CJjkubP51/QCEAE=', 'generation': '1639095187960344', 'id': 'tournament-lists/To Kill a MoCTing Bird.docx/1639095187960344', 'kind': 'storage#object', 'md5Hash': 'OiB5IDLpdfBw5fAzA3bswg==', 'mediaLink': 'https://www.googleapis.com/download/storage/v1/b/tournament-lists/o/To%20Kill%20a%20MoCTing%20Bird.docx?generation=1639095187960344&alt=media', 'metageneration': '1', 'name': 'To Kill a MoCTing Bird.docx', 'selfLink': 'https://www.googleapis.com/storage/v1/b/tournament-lists/o/To%20Kill%20a%20MoCTing%20Bird.docx', 'size': '52341', 'storageClass': 'STANDARD', 'timeCreated': '2021-12-10T00:13:08.055Z', 'timeStorageClassUpdated': '2021-12-10T00:13:08.055Z', 'updated': '2021-12-10T00:13:08.055Z'}, 'error': {'body': '{"message": {"args": ["player: \\"Jorge Mtz\\" not found in TK player list: [\'Olli Katila\', \\"Tomasz \'Hande\\u0142ek\' Domagalski\\", \'Mart\\u00ed Vidal\', \'Paco Rafael Flores\', \'Lyzanor\', \'RogerTheEnhanced\', \'Ievgen Zapolskyi\', \'Guillem\', \'Chris Szymanski\', \'Chris Mince\', \'Allor\', \'Big Boss M.\', \'Jere Jukka\', \'Keith\', \'Henrik\', \'Benjamin Nardelli\', \'Michael Mattox\', \'Phil\', \'Arash\', \'McCrae Loudon\', \'DUQUET\', \'Clement Konopnicki\', \'Dmytro Stashok\', \'Jobadiah \\"Roman\\\\\'s Revenge\\"\', \'Jorge Mtz (Chummer)\', \'Alex Schmid\', \'Hugh Scarlin\', \'Scrub\', \'Alistair Parren\', \'Jacob Corteen \', \'Stanislaw Scheiner\', \'Micha\\u0142 Rusinek\', \'Marek Gmyrek\', \'Aleksander Jaworowski\', \'Erdem \\"Matrim\\"\', \'Bogi\', \'Luke Tranter\', \'Jeff Durham \', \'Pierre-Emmanuel Guillet\', \'Jon Oakes\', \'Nicholas\', \'Chris\', \'Brendan Hadder\', \'Hugo Chui\', \'Ivan Diaz\', \'Kirill Adelfinskiy\', \'Ryan\', \'Alexander Koshkin\', \'Aleksey \\"akniles\\" Slinka\', \'Pyry Peitso\', \'Maxim\\"Inkvizitor Maximilian\\"Biba\', \'PAVEL IUKHNO\', \'Ezekiel57\', \'Sviatoslav\', \'Jes\\u00fas Mart\\u00ednez\', \'Ryan simister\', \'Andrii\', \'Crashyyy\', \'Jesse\', \'Niklas Persson\', \'Tomasz Tutaj\', \'Wojtu\\u015b\', \'Habib Echanove \', \'Artem \\"Blackmane\\" Goysan\']\\n[Tourney Keeper Link](https://www.tourneykeeper.net/Team/TKTeamLeaderboard.aspx?Id=3675)"], "with_traceback": {}}}', 'code': 400, 'headers': {'Alt-Svc': 'h3=":443"; ma=2592000,h3-29=":443"; ma=2592000,h3-Q050=":443"; ma=2592000,h3-Q046=":443"; ma=2592000,h3-Q043=":443"; ma=2592000,quic=":443"; ma=2592000; v="46,43"', 'Cache-Control': 'private', 'Content-Length': '1298', 'Content-Type': 'text/html; charset=utf-8', 'Date': 'Fri, 10 Dec 2021 00:14:04 GMT', 'Function-Execution-Id': 'bg04zksda7cg', 'Server': 'Google Frontend', 'X-Cloud-Trace-Context': 'fc42df40c5dbb8f520bba175a3a7cb85;o=1'}, 'message': 'HTTP server responded with error code 400', 'tags': ['HttpError']}}
    request_obj = Request.from_values(json=json_message)
    function_discord_error_reporting(request_obj)
