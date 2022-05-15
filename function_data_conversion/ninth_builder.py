from datetime import datetime
import requests
from pydantic import BaseModel
from typing import Optional

http = requests.Session()


class army_version(BaseModel):
    id: Optional[int]
    name: Optional[str]


class army(BaseModel):
    id: Optional[int]
    name: Optional[str]
    initials: Optional[str]
    army_version: Optional[army_version]


class unit(BaseModel):
    id: Optional[int]
    name: Optional[str]


class special_item(BaseModel):
    id: Optional[int]
    name: Optional[str]


class option_id(BaseModel):
    id: Optional[int]
    name: Optional[str]


class option(BaseModel):
    entry: Optional[str]
    fixed: Optional[str]
    name: Optional[str]
    quantity: Optional[int]
    is_sub: Optional[bool]
    option: Optional[option_id]
    special_item: Optional[special_item]


class option_base(BaseModel):
    entry: Optional[str]
    fixed: Optional[str]
    quantity: Optional[int]
    is_sub: Optional[bool]
    options: list[option]


class units(BaseModel):
    entry: Optional[str]
    fixed: Optional[str]
    name: Optional[str]
    unit: Optional[unit]
    size: Optional[int]
    points: Optional[int]
    total: Optional[float]
    option: Optional[option_base]


class error(BaseModel):
    severity: Optional[str]
    message: str


class validation(BaseModel):
    hasError: bool
    errors: list[error]


class formatted_army_block(BaseModel):
    original: Optional[str]
    formated: Optional[str]
    army: Optional[army]
    units: Optional[list[units]]
    validation: validation


def format_army_block(army_block: list[str], event_date: Optional[datetime]) -> Optional[formatted_army_block]:
    data_string = "\n".join(army_block)

    url = f"https://www.9thbuilder.com/en/api/v1/builder/imports/format"
    payload = {"data": data_string}
    if event_date:
        payload["date"] = str(event_date.timestamp())
    try:
        response = http.post(
            url,
            json=payload,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "User-Agent": "ninthage-data-analytics/1.1.0",
            },
            timeout=5,
        )
    except requests.exceptions.ReadTimeout as err:
        return None

    if response.status_code != 200:
        return None

    formatted_response = formatted_army_block(**response.json())

    return formatted_response


if __name__ == "__main__":
    data: str = """Tony Hayle
Daemonic Legions
850 - Maw of Akaan General (Greater Dominion) Wizard Adept Evocation Iron Husk Mark of the Eternal Champion
685 - Sentinel of Nukuja Dark Pulpit Thaumaturgy
625 - 24 Myrmidons Whipcrack Tail Standard Bearer Musician Champion
370 - 18 Imps Mark of the Eternal Champion Musician Champion
255 - 10 Lemures Standard Bearer Musician Champion
753 - 6 Hoarders Mirrored Scales Standard  Musician Champion
340 - 8 Eidolons Scout Aura of Despair
315 - Blazing Glory Horns of Hubris
207 - 6 Hellhounds Horns of Hubris
434 - 4 Bloat Flies Kaleidoscopic Flesh Champion
165 - 5 Furies
4999
"""
    event_date = datetime(2012,4,1,0,0)
    test = format_army_block(data.split("\n"), event_date)
    pass
