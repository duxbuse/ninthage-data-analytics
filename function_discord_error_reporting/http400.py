from flask.wrappers import Request
from typing import List
from discord_message_limits import truncate_string


def handle_400(request: Request, json_message: dict):
    print(f"{request.json=}")
    request_body = request.json["error"]["body"]
    errors: List[Exception] = request_body["message"]

    print(f"{errors=}")

    all_errors = [
        dict(name="Value Error", value=truncate_string(str(x)), inline=True)
        for x in errors[:24]
    ]  # limit on 25 fields, so we take only 24 as there is a footer field
    json_message["embeds"][0]["fields"].insert(
        0, *all_errors
    )  # add all the errors at the beginning before the header
