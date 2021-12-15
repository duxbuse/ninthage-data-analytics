from flask.wrappers import Request
from discord_message_limits import truncate_string


def handle_error(request: Request, json_message: dict):
    message = request.json["error"]["message"]

    error_message = dict(
        name="Other Error", value=truncate_string(message), inline=True
    )
    json_message["embeds"][0]["fields"].insert(0, error_message)
