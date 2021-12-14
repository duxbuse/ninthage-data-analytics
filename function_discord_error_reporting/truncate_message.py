import json
from math import ceil
def truncate_message(message: dict) -> dict:
    DISCORD_EMBED_FIELD_VALUE = 1024
    message_as_string = json.dumps(message)
    # message will exceed discords limits
    if len(message_as_string) > DISCORD_EMBED_FIELD_VALUE:
        chars_to_remove = len(message_as_string) - DISCORD_EMBED_FIELD_VALUE
        fields = message["embeds"][0]["fields"]
        # TODO: assuming first field is the problem
        problem_field = fields[0]["value"]
        if len(problem_field) > chars_to_remove:
            truncation_warning = " [...] "
            half_of_chars = ceil((chars_to_remove + len(truncation_warning)) / 2) 
            midpoint = ceil(len(problem_field) / 2)
            new_field = problem_field[:midpoint-half_of_chars] + truncation_warning + problem_field[midpoint+half_of_chars:]
            message["embeds"][0]["fields"][0]["value"] = new_field
            return message
        else:
            # Assumption was wrong
            raise ValueError("message truncation failed, due to not a singular large first field")
    # Message needs to truncation
    return message