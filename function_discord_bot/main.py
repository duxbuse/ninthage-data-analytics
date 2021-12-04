from os import getenv
from flask.wrappers import Request
import requests
from flask import jsonify
from security_headers import check_security_headers
from discord_command_upload import upload_file
from discord_command_validate import validate



def function_discord_bot(request: Request):
    check_security_headers(request)

    # Handle ping for livelyness
    if request.json["type"] == 1:
        return jsonify({"type": 1})
    else:
        # return message to discord
        command_name = request.json["data"]["name"]

        return jsonify({
            "type": 4,
            "data": {
                "tts": False,
                "content": registered_commands[command_name](request),
                "embeds": [],
                "allowed_mentions": {"parse": []}
            }
        })

registered_commands = {
        "upload" : upload_file,
        "validate" : validate
    }

if __name__ == "__main__":
    # Register message commands as per the list
    from dotenv import load_dotenv
    import requests

    load_dotenv()

    TOKEN = getenv('DISCORD_APP_TOKEN')
    APP_ID = getenv('DISCORD_APP_ID')

    url = f"https://discord.com/api/v8/applications/{APP_ID}/commands"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "",
        "Content-Type": "application/json"
    }

    json = [{"name": x, "type": 3} for x in registered_commands.keys()]

    for message_command in json:
        r = requests.post(url, headers=headers, json=message_command)

        print(f"upload status code: {r.status_code}")
        if r.status_code != 200 or r.status_code != 201:
            print(f"{r.text}")


