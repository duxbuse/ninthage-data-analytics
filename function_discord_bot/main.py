from os import rmdir, getenv
from flask.wrappers import Request, Response
import requests
from flask import abort, jsonify
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
from google.cloud import storage


def function_discord_bot(request: Request):

    # Ensure security headers
    # Your public key can be found on your application in the Developer Portal
    PUBLIC_KEY = '5a4d255fbb9ac0df010b6844e0e9cb22b0a4a560e0d424724c7667c6a47bc01c'

    verify_key = VerifyKey(bytes.fromhex(PUBLIC_KEY))

    signature = request.headers["X-Signature-Ed25519"]
    timestamp = request.headers["X-Signature-Timestamp"]
    body = request.data.decode("utf-8")

    try:
        verify_key.verify(f'{timestamp}{body}'.encode(),
                          bytes.fromhex(signature))
    except BadSignatureError:
        abort(401, 'invalid request signature')

    # Handle valid requests
    if request.json["type"] == 1:
        return reply_to_ping()
    else:
        return jsonify({
            "type": 4,
            "data": {
                "tts": False,
                "content": validate_list(request),
                "embeds": [],
                "allowed_mentions": {"parse": []}
            }
        })


def validate_list(request: Request):
    data = request.json["data"]
    message_id = data["target_id"]
    attachment = data["resolved"]["messages"][message_id]["attachments"]
    url = attachment["url"]
    filename = attachment["filename"]

    download_file_path = f"/tmp/{filename}"
    upload_bucket = "tournament-lists"

    r = requests.get(url, allow_redirects=True)
    open(download_file_path, 'wb').write(r.content)

    upload_blob(upload_bucket, download_file_path, filename)
    rmdir("/tmp")
    return f"File: {filename} uploaded to bucket: {upload_bucket}"


def reply_to_ping():
    return jsonify({"type": 1})


def upload_blob(bucket_name, file_path, destination_blob_name) -> None:
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)

    print('File {} uploaded to {}.'.format(
        destination_blob_name,
        bucket_name))


if __name__ == "__main__":
    # Register bot slash commands
    from dotenv import load_dotenv
    import requests

    load_dotenv()

    TOKEN = getenv('DISCORD_TOKEN')
    APP_ID = getenv('DISCORD_APP_ID')

    url = f"https://discord.com/api/v8/applications/{APP_ID}/commands"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
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
