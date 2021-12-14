from flask.wrappers import Request


def handle_408(request: Request, json_message: dict):
    message = request.json["error"]["message"]

    error_message = dict(name="Timeout Error", value=message, inline=True)
    json_message["embeds"][0]["fields"].insert(0, error_message)
