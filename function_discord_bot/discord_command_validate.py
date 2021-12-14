from flask.wrappers import Request


def validate(request: Request):
    return "looks legit to me. (note this is a dummy response)"
