# import os
import json
from flask.wrappers import Request, Response
from flask import abort
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



def reply_to_ping():
    js = json.dumps({"type": 1})
    return Response(js, status=200, mimetype='application/json') 



if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    
    # TOKEN = os.getenv('DISCORD_TOKEN')

    # client = discord.Client()

    # @client.event
    # async def on_ready():
    #     print(f'{client.user} has connected to Discord!')

    # client.run(TOKEN)