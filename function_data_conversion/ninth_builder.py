import requests


def format_army_block(army_block: list[str]) -> list[str]:

    data_string = "\n".join(army_block)

    url = f"https://www.9thbuilder.com/en/api/v1/builder/imports/format"
    try:
        response = requests.post(
            url,
            json={"data": data_string},
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "ninthage-data-analytics/1.1.0",
            },
            timeout=2,
        )  # need to blank the user agent as the default is automatically blocked
    except requests.exceptions.ReadTimeout as err:
        return []

    if response.status_code != 200:
        return []

    message = response.json()["formated"]
    message_list = message.split("\n")
    return [x.strip() for x in message_list]
