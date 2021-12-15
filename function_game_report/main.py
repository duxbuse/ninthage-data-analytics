from flask.wrappers import Request


def function_game_report(request: Request):
    print(f"{request.form=}")
    return "Report uploaded", 200


if __name__ == "__main__":
    pass
