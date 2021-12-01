from flask.wrappers import Request, Response
from flask import abort, jsonify
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError


def function_discord_bot(request: Request):

    # Ensure security headers
    # Your public key can be found on your application in the Developer Portal
    PUBLIC_KEY = '5a4d255fbb9ac0df010b6844e0e9cb22b0a4a560e0d424724c7667c6a47bc01c'

    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))

    signature = request.headers["X-Signature-Ed25519"]
    timestamp = request.headers["X-Signature-Timestamp"]
    body = request.data.decode("utf-8")

    try:
        verify_key.verify(f'{timestamp}{body}'.encode(), bytes.fromhex(signature))
    except BadSignatureError:
        abort(401, 'invalid request signature')


    # Handle valid requests
    if request.json["type"] == 1:
        return reply_to_ping()
    else:
        attachments = validate_list(request)
        print(f"DEBUG: attachments: {attachments}")
        return jsonify({
            "type": 4,
            "data": {
                "tts": False,
                "content": "check da logs",
                "embeds": [],
                "allowed_mentions": { "parse": [] }
            }
        })


def validate_list(request: Request):
    data = request.json["data"]
    message_id = data["target_id"]

    return data["resolved"]["messages"][message_id]["attachments"]


def reply_to_ping():
    return jsonify({"type": 1})



if __name__ == "__main__":
    # Register bot slash commands
    import os
    from dotenv import load_dotenv
    import requests

    load_dotenv()

    
    TOKEN = os.getenv('DISCORD_TOKEN')
    APP_ID = os.getenv('DISCORD_APP_ID')

    url = f"https://discord.com/api/v8/applications/{APP_ID}/commands"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept":"application/json",
        "User-Agent": "",
        "Content-Type": "application/json"
    }   

    # This is an example CHAT_INPUT or Slash Command, with a type of 1
    json = {
    "name": "validate",
    "type": 3
}

    r = requests.post(url, headers=headers, json=json)

    print(f"upload status code: {r.status_code}")
    if r.status_code != 200:
        print(f"{r.text}")