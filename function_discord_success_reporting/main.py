from os import getenv
import requests
from flask.wrappers import Request
from pathlib import Path
from dotenv import load_dotenv
from math import ceil
import json




def function_discord_success_reporting(request:Request):
    load_dotenv()

    request_body = request.json["data"]["body"]
    print(f"{request_body=}")

    TOKEN = getenv('DISCORD_WEBHOOK_TOKEN')
    WEBHOOK_ID = getenv('DISCORD_WEBHOOK_ID')
    FILE_NAME = Path(request_body['file_name']).stem + ".docx"
    LIST_NUMBER = request_body['list_number']
    OUTPUT_TABLE = request_body['output_table']

    army_info = request.json["army_info"]["body"]
    print(f"{army_info=}")
    LOADED_TK_INFO = army_info['loaded_tk_info']
    VALIDATION_COUNT = army_info['validation_count']
    VALIDATION_ERRORS = army_info['validation_errors']

    url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "",
        "Content-Type": "application/json"
    }


    # https://discordjs.guide/popular-topics/embeds.html#editing-the-embedded-message-content
    all_errors = [dict(name=x["player_name"], value=truncate_field_values(x["validation_errors"]), inline=True) for x in VALIDATION_ERRORS]
    header = {
                "name": f"Additional Info",
                "value": f"Lists read = `{LIST_NUMBER}`\nTK info Loaded = `{LOADED_TK_INFO}`\nPassed Validation = `{VALIDATION_COUNT}`/`{LIST_NUMBER}`\nOutput Table = `{OUTPUT_TABLE}`",
                "inline": True
            }
    footer = {
                "name": "\u200B",
                "value": "Got an issue raise it [here](https://github.com/duxbuse/ninthage-data-analytics/issues)!"
                }
    # limit len(fields) to 25 as that is a discord limit
    fields = [header, *all_errors[:23] , footer]


    # For help on this https://gist.github.com/Birdie0/78ee79402a4301b1faf412ab5f1cdcf9
    json_message = {
        "content": "",
        "embeds": [{
            "author": {
            "name": FILE_NAME,
            },
            "title": "Success:",
            "description": "",
            "color": 5236872,
            "fields": fields
        }]
    }
    truncate_message(json_message)
    r = requests.post(url, headers=headers, json=json_message)

    print(f"upload status code: {r.status_code}")
    if r.status_code != 200 or r.status_code != 201:
        print(f"{json_message=}")

    return r.text, r.status_code

def truncate_field_values(values: list[str]) -> str:

    # This needs to remove items from the value list until the size is right then return, randomly cutting the string up is cause malformed json as a result

    DISCORD_EMBED_FIELD_VALUE = 1024
    current_total = sum(len(x) for x in values)
    while current_total > DISCORD_EMBED_FIELD_VALUE:
        last_value = values.pop()
        current_total -= len(last_value)
    return str(values)

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

if __name__ == "__main__":
    army_info={'bucket_name': 'tournament-lists-json', 'file_name': 'TorneoAlpacas2.json', 'loaded_tk_info': False, 'validation_count': 2, 'validation_errors': [{'player_name': 'Guillem ‘’Perchas’’ Lana', 'validation_errors': ['Vampire Count: could not find option Binding Scroll Vampire Courtier', 'Vampire Count: could not find option Wizard (Wizard Apprentice, Shamanism)', 'Vampire Count: could not find option Battle Standard Bearer (Flaming Standard, Aether Icon)', 'Vampire Count: could not find option Flaming Standard', 'Vampire Count: could not find option Aether Icon', 'Vampire Count: could not find option Obsidian Rock Necromancer', 'Vampire Count: could not find option Alchemy', 'Vampire Count: Invalid cost: 820, correct cost: 1250', 'Bloodline is limited to 1.', 'Independant is incompatible with Strigoi Bloodline', 'Bestial Bulk is incompatible with Shield Breaker', 'Strigoi Bloodline is incompatible with Independant', 'Ghoul Lord is limited to 1 per Army.', 'Level is limited to 1.', 'Wizard Master is incompatible with Strigoi Bloodline', 'Path is limited to 1.', 'Weapon is limited to 1.', 'Shield Breaker is incompatible with Bestial Bulk']}, {'player_name': 'Jonathan ‘’Lance Coockwood’’ Queija', 'validation_errors': ['Silexian Officer: could not find option Halberd (Shield Breaker) Silexian Officer', 'Silexian Officer: Invalid cost: 315, correct cost: 435', 'Special Equipment is limited to 100 points.', "Willow's Ward is incompatible with Raptor Chariot", "Willow's Ward is limited to 1 per Army.", 'Armour Enchant is limited to 1.', 'Melee Weapons is limited to 1.', 'Spear is incompatible with Raptor Chariot']}, {'player_name': 'Kolzar ‘’La leyenda’’ Amat', 'validation_errors': ['Could not find unit 440 - Damsel: Barded Warhorse', 'Could not find unit 515 - Duke: Barded Warhorse', 'Could not find unit 435 - Duke: Barded Warhorse', 'Could not find unit 275 - 6 Knights of the Realm: C', 'Could not find unit 285 - 6 Knights of the Realm: FCG', 'Could not find unit 285 - 6 Knights of the Realm: FCG', 'Could not find unit 285 - 6 Knights of the Realm: FCG', 'Could not find unit 593 - 7 Knights of the Grail: FCG', 'Could not find unit 540 - 11 Knights of the Quest: FCG', 'Could not find unit 135 - 5 Yeoman Outriders: Shield', 'Could not find unit Total: 4', 'Army: requires General', 'Army: requires a minimum of 4 units', ' Core: required minimum cost is not fulfilled']}, {'player_name': 'Enrique ‘’Lyzanor’’ Perez', 'validation_errors': ['Overlord: could not find option Gauntlets of Madzhab', 'Overlord: could not find option Arrogance', 'Vizier: could not find option Blessed Icon of Zalaman Tekash', 'Disciples of Lugar: could not find option Champion 3 Taurukh Anointed', 'Infernal Engine: could not find option Titan Mortar', 'Overlord: Invalid cost: 495, correct cost: 350', 'Prophet: Invalid cost: 545, correct cost: 560', 'Vizier: Invalid cost: 360, correct cost: 325', 'Infernal Warriors: Invalid cost: 462, correct cost: 471', 'Infernal Warriors: Invalid cost: 420, correct cost: 430', 'Vassal Levies: Invalid cost: 243, correct cost: 248', 'Infernal Bastion: Invalid cost: 265, correct cost: 275', 'Disciples of Lugar: Invalid cost: 650, correct cost: 710', 'Infernal Engine: Invalid cost: 410, correct cost: 420', 'Overlord: requires 2 Weapon Enchant', 'Weapons is limited to 1.']}, {'player_name': 'Gonza ‘’Bad Bunny’’', 'validation_errors': ['Death Cult Hierarch: could not find option cosmo', 'Death Cult Hierarch: could not find option Soul Conduit Death Cult Hierarch', 'Death Cult Hierarch: could not find option divi', 'Tomb Cataphracts: could not find option Champion 7 Shabti Archers', 'Death Cult Hierarch: Invalid cost: 430, correct cost: 565', 'Tomb Cataphracts: Invalid cost: 575, correct cost: 720', 'Level is limited to 1.', 'Standard Bearer is limited to 1.']}, {'player_name': 'Sergi ‘’Sergielknight’’ Canadell', 'validation_errors': ['Warlock Outcast: could not find option Binding Scroll Temple Exarch', 'Warlock Outcast: could not find option General', 'Warlock Outcast: could not find option Divination', 'Warlock Outcast: could not find option Battle Oracle', 'Warlock Outcast: could not find option Seal of the Republic', 'Silexian Spears: could not find option Champion 23 Silexian Auxiliaries', 'Silexian Spears: could not find option Standard Bearer (Flaming Standard) 15 Silexian Auxiliaries', 'Warlock Outcast: Invalid cost: 500, correct cost: 460', 'Silexian Spears: Invalid cost: 531, correct cost: 596', 'Army: requires General', 'Standard Bearer is limited to 1.', ' Core: required minimum cost is not fulfilled']}, {'player_name': 'Toni', 'validation_errors': ['Shaman: could not find option Rottenjaw Mammoth Hunter', 'Shaman: could not find option Hunting Spear', 'Shaman: could not find option Scout', 'Tribesmen: could not find option Champion 3 Tribesmen', 'Shaman: Invalid cost: 510, correct cost: 625', 'Tribesmen: Invalid cost: 525, correct cost: 595', 'Close Combat Weapon is limited to 1.', ' Core: required minimum cost is not fulfilled']}, {'player_name': 'Ruben ‘’Big1’’', 'validation_errors': ['High Prince: could not find option Lucky Charm Mage', 'High Prince: could not find option Wizard Master', 'High Prince: could not find option Cosmology', 'Commander: could not find option Master of Canreig Tower 22 Sea Guard', 'Commander: could not find option Standard Bearer', 'Commander: could not find option Musician', 'Commander: could not find option Champion', 'Sword Masters: could not find option Champion Lion Chariot', 'High Prince: Invalid cost: 865, correct cost: 910', 'Commander: Invalid cost: 390, correct cost: 190', 'Sword Masters: Invalid cost: 565, correct cost: 555', ' Core: required minimum cost is not fulfilled']}, {'player_name': 'Ricardo ‘’Big2’’', 'validation_errors': ['Thane: could not find option Holdstone Runic Smith', 'Thane: could not find option Battle Rune', 'Thane: Invalid cost: 290, correct cost: 270']}, {'player_name': 'Dani ‘’Gordito’’', 'validation_errors': ['Could not find unit 410 - Tempre Exarch - general', 'Could not find unit 495 - 26x temple militants', 'Could not find unit 190 - raptor chariot', 'Could not find unit 190 - raptor chariot', 'Could not find unit 383 - 6x dread Knights', 'Could not find unit 200 - Divine altar', 'Could not find unit 170 - 5x black cloaks', 'Could not find unit 170 - 5x black cloaks', 'Could not find unit 190 - Repeater battery', 'Could not find unit 190 - Repeater battery', 'Could not find unit 380 – kraken', 'Army: requires General', 'Army: requires a minimum of 4 units', ' Core: required minimum cost is not fulfilled']}, {'player_name': 'Jose ‘’Killerdawn’’ Ibañez', 'validation_errors': ['Khan: could not find option Binding Scroll Shaman', 'Khan: could not find option Wizard Adept', 'Khan: could not find option Shamanism', 'Khan: could not find option Magical Heirloom Shaman', 'Khan: could not find option Wizard Adept', 'Khan: could not find option Pyromancy', 'Mercenary Veterans: could not find option Champion 2 Yetis', 'Khan: Invalid cost: 350, correct cost: 370', 'Mercenary Veterans: Invalid cost: 495, correct cost: 485', 'Close Combat Weapon is limited to 1.', 'Firebrand: requires Shaman']}]}
    request_body={'file_name': 'TorneoAlpacas2.json', 'list_number': 13, 'output_table': 'all_lists:tournament_lists'}
    json_message = {'data': {'body': request_body}, 'army_info': {'body': army_info}}
    request_obj = Request.from_values(json=json_message)
    function_discord_success_reporting(request_obj)
