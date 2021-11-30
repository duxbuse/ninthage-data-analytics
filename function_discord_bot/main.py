# import os
import json
from flask.wrappers import Request


def function_discord_bot(request: Request):

    # TOKEN = os.getenv('DISCORD_TOKEN')

    # client = discord.Client()

    # @client.event
    # async def on_ready():
    #     print(f'{client.user} has connected to Discord!')

    # client.run(TOKEN)
    if request.json["type"] == 1:
        return reply_to_ping()



def reply_to_ping():
    return json.dumps({"type": 1})



if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()