import json
def truncate_field_values(values: list[str]) -> str:

    # This needs to remove items from the value list until the size is right then return, randomly cutting the string up is cause malformed json as a result

    DISCORD_EMBED_FIELD_VALUE = 1024
    current_total = sum(len(x) for x in values)
    while current_total + len(values) > DISCORD_EMBED_FIELD_VALUE: #len(values) represents the extra `\n` that will be appended
        last_value = values.pop()
        current_total -= len(last_value)
    return '\n'.join(values)

def truncate_message(message: dict):
    DISCORD_EMBED_TOTAL_LENGTH = 6000
    current_total = character_total(message)
    while current_total > DISCORD_EMBED_TOTAL_LENGTH:
        # Drop the last non footer field until passing the discord requirements
        message["embeds"][0]["fields"] = [*message["embeds"][0]["fields"][:-3], message["embeds"][0]["fields"][-1]]
        # reduce the character count buy what was just removed
        current_total -= len(json.dumps(message["embeds"][0]["fields"][-2]["name"]))
        current_total -= len(json.dumps(message["embeds"][0]["fields"][-2]["value"]))

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
