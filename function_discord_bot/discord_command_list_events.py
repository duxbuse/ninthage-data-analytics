from flask.wrappers import Request


def list_events(request: Request):
    """List all the events that are currently loaded in the database

    Args:
        request (Request): [description]

    Returns:
        [type]: [description]
    """

    return "This will be a list of all events already loaded"
