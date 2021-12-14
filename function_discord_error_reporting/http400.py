from flask.wrappers import Request
from typing import List


def handle_400(request:Request, json_message:dict):
    print(f"{request.json=}")
    request_body = request.json["error"]["body"]
    errors:List[str] = request_body["message"]


    print(f"{errors=}")


    all_errors = [dict(name="Value Error", value=x, inline=True) for x in errors]
    json_message["embeds"][0]["fields"].insert(0, *all_errors)