import json
from math import ceil


def truncate_string(message: str) -> str:
    DISCORD_EMBED_FIELD_VALUE = 1024
    message_as_string = message
    # message will exceed discords limits
    if len(message_as_string) > DISCORD_EMBED_FIELD_VALUE:
        truncation_warning = " [...] "
        chars_to_remove = (
            len(message_as_string) + len(truncation_warning) - DISCORD_EMBED_FIELD_VALUE
        )
        half_of_chars = ceil((chars_to_remove) / 2)
        midpoint = ceil(len(message_as_string) / 2)
        new_field = (
            message_as_string[: midpoint - half_of_chars]
            + truncation_warning
            + message_as_string[midpoint + half_of_chars :]
        )
        return new_field
    return message


def truncate_message(message: dict):
    DISCORD_EMBED_TOTAL_LENGTH = 6000
    while character_total(message) > DISCORD_EMBED_TOTAL_LENGTH:
        message["embeds"][0]["fields"].pop(
            -2
        )  # take the second last item as the last is the footter and we want to leave that


def character_total(message: dict) -> int:
    embed = message["embeds"][0]
    total = 0
    total += len(json.dumps(embed["title"]))
    total += len(json.dumps(embed["description"]))
    total += len(json.dumps(embed["author"]["name"]))
    # total += len(json.dumps(embed["footer"])) # We are not using footer presently
    for field in embed["fields"]:
        total += len(json.dumps(field["name"]))
        total += len(json.dumps(field["value"]))
    return total
