from os import getenv
import requests
from flask.wrappers import Request
from pathlib import Path
from discord_message_limits import *

def function_discord_success_reporting(request: Request):
    print(f"{request.json=}")
    request_body = request.json["data"]["body"]
    print(f"{request_body=}")

    TOKEN = getenv("DISCORD_WEBHOOK_TOKEN")
    WEBHOOK_ID = getenv("DISCORD_WEBHOOK_ID")
    FILE_NAME = Path(request_body["file_name"]).stem + ".docx"
    LIST_NUMBER = request_body["list_number"]
    OUTPUT_TABLE = request_body["output_table"]

    army_info = request.json["army_info"]["body"]
    print(f"{army_info=}")
    LOADED_TK_INFO = army_info["loaded_tk_info"]
    VALIDATION_COUNT = army_info["validation_count"]
    POSSIBLE_TK_NAMES = army_info["possible_tk_names"]
    VALIDATION_ERRORS = army_info["validation_errors"]

    url = f"https://discord.com/api/webhooks/{WEBHOOK_ID}/{TOKEN}"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Accept": "application/json",
        "User-Agent": "ninthage-data-analytics/1.1.0",
        "Content-Type": "application/json",
    }

    # https://discordjs.guide/popular-topics/embeds.html#editing-the-embedded-message-content
    all_errors = [
        dict(
            name=x.get("player_name", "No Player Name") or "No Player Name",
            value=truncate_field_values(x.get("validation_errors", "No Errors")) or "No Errors",
            inline=False,
        )
        for x in VALIDATION_ERRORS
    ]
    header = {
        "name": f"Additional Info",
        "value": f"Lists read = `{LIST_NUMBER}`\nTK info Loaded = `{LOADED_TK_INFO}`\nPossible TK name matches = `{POSSIBLE_TK_NAMES[:3]}`\nPassed Validation = `{VALIDATION_COUNT}/{LIST_NUMBER}`\nOutput Table = `{OUTPUT_TABLE}`",
        "inline": False,
    }
    footer = {
        "name": "\u200B",
        "value": "Got an issue raise it [here](https://github.com/duxbuse/ninthage-data-analytics/issues)!",
    }
    # limit len(fields) to 25 as that is a discord limit
    fields = [header, *all_errors[:23], footer]

    # For help on this https://gist.github.com/Birdie0/78ee79402a4301b1faf412ab5f1cdcf9
    json_message = {
        "content": "",
        "embeds": [
            {
                "author": {
                    "name": FILE_NAME,
                },
                "title": "Success:",
                "description": "",
                "color": 5236872,
                "fields": fields,
            }
        ],
    }
    truncate_message(json_message)
    r = requests.post(url, headers=headers, json=json_message)

    print(f"upload status code: {r.status_code}\n{r.text=}")
    if r.status_code != 200 or r.status_code != 201 or r.status_code != 204:
        print(f"{json_message=}")

    return r.text, r.status_code


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    army_info={'bucket_name': 'tournament-lists-json', 'file_name': 'new-recruit-611ac82f2781604de4d20b8c.json', 'loaded_tk_info': 'N/A', 'possible_tk_names': ['N/A'], 'validation_count': 17, 'validation_errors': [{'player_name': None, 'validation_errors': ['Army: Invalid cost: 4494, correct cost: 4487', 'Unit: Chosen Lord, invalid cost: 730, correct cost: 805', 'Unit: Chosen Lord, invalid cost: 700, correct cost: 725', 'Unit: Sorcerer, invalid cost: 370, correct cost: 395', 'Unit: Warriors, invalid cost: 644, correct cost: 477', 'Unit: Barbarians, invalid cost: 160, correct cost: 146', 'Unit: Feldraks, invalid cost: 376, correct cost: 365', 'Unit: Battleshrine, invalid cost: 320, correct cost: 330', 'Unit: Feldrak Elder, invalid cost: 490, correct cost: 515', 'Unit: Feldrak Elder, invalid cost: 490, correct cost: 515']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4500, correct cost: 4381', 'Unit: Exalted Herald, invalid cost: 830, correct cost: 860', 'Unit: Chosen Lord, invalid cost: 630, correct cost: 645', 'Unit: Sorcerer, invalid cost: 370, correct cost: 395', 'Unit: Warriors, invalid cost: 720, correct cost: 540', 'Unit: Barbarians, invalid cost: 180, correct cost: 166', 'Unit: Battleshrine, invalid cost: 310, correct cost: 320', 'Unit: Forsworn, invalid cost: 255, correct cost: 225', 'Unit: Flayers, invalid cost: 145, correct cost: 155', 'Unit: Feldrak Elder, invalid cost: 480, correct cost: 495']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4620, correct cost: 4346', 'Unit: Prophet, invalid cost: 505, correct cost: 550', 'Unit: Taurukh Commissioner, invalid cost: 500, correct cost: 495', 'Unit: Taurukh Commissioner, invalid cost: 455, correct cost: 460', 'Unit: Vassal Conjurer, invalid cost: 255, correct cost: 260', 'Unit: Citadel Guard, invalid cost: 461, correct cost: 349', 'Unit: Vassal Levies, invalid cost: 220, correct cost: 144', 'Unit: Taurukh Anointed, invalid cost: 643, correct cost: 580', 'Unit: Taurukh Anointed, invalid cost: 643, correct cost: 580', 'Unit: Kadim Titan, invalid cost: 475, correct cost: 465']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4500, correct cost: 4394', 'Unit: Chosen Lord, invalid cost: 970, correct cost: 985', 'Unit: Sorcerer, invalid cost: 675, correct cost: 680', 'Unit: Warriors, invalid cost: 362, correct cost: 326', 'Unit: Warriors, invalid cost: 300, correct cost: 276', 'Unit: Barbarian Horsemen, invalid cost: 270, correct cost: 252', 'Unit: Chosen Knights, invalid cost: 638, correct cost: 595', 'Unit: Chosen Chariot, invalid cost: 400, correct cost: 395']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4498, correct cost: 2909', 'Army: Could not find unit 785 - Sentinel of Nukuja, General (Greater Dominion), Dark Pulpit, Thaumaturgy, Guiding Mirrored Scales', 'Army: Could not find unit 765 - Omen of Savar, Wizard Master, Divination, Living Shield', 'Unit: Succubi, invalid cost: 425, correct cost: 393', 'Unit: Lemures, invalid cost: 415, correct cost: 420', 'Unit: Lemures, invalid cost: 295, correct cost: 305', 'Unit: Brazen Beasts, invalid cost: 380, correct cost: 370', 'Unit: Bloat Flies, invalid cost: 334, correct cost: 343', 'Unit: Bloat Flies, invalid cost: 334, correct cost: 343', 'Unit: Furies, invalid cost: 165, correct cost: 135']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4496, correct cost: 4440', 'Unit: Temple Exarch, Could not find option Battle Oracle', 'Unit: Temple Exarch, invalid cost: 370, correct cost: 405', 'Unit: Temple Exarch, invalid cost: 360, correct cost: 295', 'Unit: Temple Exarch, invalid cost: 350, correct cost: 330', 'Unit: Silexian Officer, invalid cost: 340, correct cost: 350', 'Unit: Raiding Party, invalid cost: 268, correct cost: 257', 'Unit: Judicators, invalid cost: 500, correct cost: 480', 'Unit: Dread Knights, invalid cost: 398, correct cost: 373', 'Unit: Gorgons, invalid cost: 280, correct cost: 290', 'Unit: Divine Altar, invalid cost: 200, correct cost: 215', 'Unit: Hydra, invalid cost: 400, correct cost: 415']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4498, correct cost: 4037', 'Unit: Anvil of Power, invalid cost: 195, correct cost: 190', 'Unit: Clan Marksmen, invalid cost: 240, correct cost: 190', 'Unit: Clan Marksmen, invalid cost: 240, correct cost: 190', 'Unit: Clan Marksmen, invalid cost: 210, correct cost: 187', 'Unit: Clan Marksmen, invalid cost: 210, correct cost: 187', 'Unit: Greybeards, invalid cost: 225, correct cost: 202', 'Unit: Seekers, invalid cost: 625, correct cost: 528', 'Unit: Seekers, invalid cost: 625, correct cost: 528', 'Unit: Grudge Buster, invalid cost: 315, correct cost: 305', 'Unit: Grudge Buster, invalid cost: 315, correct cost: 305', 'Unit: Rangers, invalid cost: 203, correct cost: 150', 'Unit: Vengeance Seeker, invalid cost: 130, correct cost: 125', 'Unit: Steam Copters, invalid cost: 185, correct cost: 180', 'Unit: Steam Copters, invalid cost: 185, correct cost: 180', 'Unit: Field Artillery, invalid cost: 250, correct cost: 245']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4498, correct cost: 960', 'Army: Could not find unit 605 - Duke, General, Pegasus, Shield (Fortress of Faith), Lance (Supernatural Dexterity), Basalt Infusion, Obsidian Rock, Might, Grail Oath', "Army: Could not find unit 310 - Paladin, Barded Warhorse, Shield, Battle Standard Bearer, Lance (Wyrmwood Core), Alchemist's Alloy, Grail Oath", 'Army: Could not find unit 110 - Castellan, Horse, Bannerman', 'Army: Could not find unit 596 - 12x Knights Aspirant, Standard Bearer (Banner of the Last Charge), Musician, Champion', 'Army: Could not find unit 275 - 6x Knights of the Realm, Musician, Champion', 'Army: Could not find unit 275 - 6x Knights of the Realm, Musician, Champion', 'Army: Could not find unit 732 - 9x Knights of the Grail, Standard Bearer (Aether Icon), Musician, Champion', 'Army: Could not find unit 375 - The Green Knight', 'Army: Could not find unit 130 - Scorpion', 'Army: Could not find unit 130 - Scorpion', 'Unit: Damsel, Could not find option Barded Warhorse', 'Unit: Pegasus Knights, Could not find option Loose Formation', 'Unit: Damsel, invalid cost: 385, correct cost: 380', 'Unit: Pegasus Knights, invalid cost: 575, correct cost: 580']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4458, correct cost: 4074', 'Unit: Goblin Chief, Could not find option Forest Goblin', 'Unit: Goblin Chief, Could not find option Bow', 'Unit: Goblin Witch Doctor, Could not find option Common Goblin and Light Armour', 'Unit: Goblin Witch Doctor, Could not find option Common Goblin and Light Armour', 'Unit: Orc Boar Riders, Could not find option Feral Orc', 'Unit: Orc Boar Riders, Could not find option Feral Orc', 'Unit: Orc Shaman, invalid cost: 555, correct cost: 565', 'Unit: Orc Warlord, invalid cost: 405, correct cost: 400', 'Unit: Goblin Chief, invalid cost: 235, correct cost: 205', 'Unit: Goblin Witch Doctor, invalid cost: 195, correct cost: 200', 'Unit: Goblin Witch Doctor, invalid cost: 195, correct cost: 200', 'Unit: Orcs, invalid cost: 715, correct cost: 442', 'Unit: Goblins, invalid cost: 225, correct cost: 192', 'Unit: Orc Boar Riders, invalid cost: 170, correct cost: 149', 'Unit: Orc Boar Riders, invalid cost: 170, correct cost: 149', 'Unit: Iron Orcs, invalid cost: 433, correct cost: 428', 'Unit: Gnasher Wrecking Team, invalid cost: 135, correct cost: 130', 'Unit: Gnasher Wrecking Team, invalid cost: 135, correct cost: 130', 'Unit: Goblin Raiders, invalid cost: 125, correct cost: 117', 'Unit: Goblin Raiders, invalid cost: 125, correct cost: 117', 'Unit: Greenhide Catapult, invalid cost: 160, correct cost: 170']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4491, correct cost: 4461', 'Unit: Mage, invalid cost: 1025, correct cost: 970', 'Unit: Citizen Spears, invalid cost: 280, correct cost: 290', 'Unit: Citizen Spears, invalid cost: 280, correct cost: 290', 'Unit: Citizen Archers, invalid cost: 170, correct cost: 160', 'Unit: Citizen Archers, invalid cost: 170, correct cost: 160', 'Unit: Knights of Ryma, invalid cost: 445, correct cost: 440', 'Unit: Flame Wardens, invalid cost: 401, correct cost: 391', 'Unit: Sea Guard Reaper, invalid cost: 180, correct cost: 190', 'Unit: Sea Guard Reaper, invalid cost: 180, correct cost: 190', 'Unit: Phoenix, invalid cost: 375, correct cost: 395']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4500, correct cost: 4641', 'Unit: High Prince, invalid cost: 705, correct cost: 750', 'Unit: Mage, invalid cost: 275, correct cost: 280', 'Unit: Sea Guard, invalid cost: 648, correct cost: 684', 'Unit: Citizen Spears, invalid cost: 283, correct cost: 292', 'Unit: Elein Reavers, invalid cost: 195, correct cost: 191', 'Unit: Lion Guard, invalid cost: 644, correct cost: 664', 'Unit: Knights of Ryma, invalid cost: 395, correct cost: 365', 'Unit: Sea Guard Reaper, invalid cost: 180, correct cost: 190', 'Unit: Sea Guard Reaper, invalid cost: 180, correct cost: 190', 'Unit: Phoenix, invalid cost: 310, correct cost: 350']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4500, correct cost: 4401', 'Unit: Avatar of Nature, invalid cost: 660, correct cost: 645', 'Unit: Druid, invalid cost: 475, correct cost: 495', 'Unit: Chieftain, invalid cost: 310, correct cost: 305', 'Unit: Forest Guard, invalid cost: 440, correct cost: 435', 'Unit: Dryads, invalid cost: 437, correct cost: 432', 'Unit: Heath Riders, invalid cost: 249, correct cost: 207', 'Unit: Forest Rangers, invalid cost: 518, correct cost: 499', 'Unit: Blade Dancers, invalid cost: 507, correct cost: 497', 'Unit: Sylvan Sentinels, invalid cost: 317, correct cost: 308', 'Unit: Sylvan Sentinels, invalid cost: 317, correct cost: 308']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4453, correct cost: 4228', 'Unit: Orc Shaman, invalid cost: 510, correct cost: 555', 'Unit: Orc Warlord, invalid cost: 490, correct cost: 480', 'Unit: Goblin King, invalid cost: 295, correct cost: 290', "Unit: Orc 'Eadbashers, invalid cost: 645, correct cost: 519", 'Unit: Goblins, invalid cost: 300, correct cost: 305', 'Unit: Orcs, invalid cost: 310, correct cost: 191', 'Unit: Iron Orcs, invalid cost: 553, correct cost: 548', 'Unit: Gnasher Dashers, invalid cost: 145, correct cost: 130', 'Unit: Greenhide Catapult, invalid cost: 140, correct cost: 150', 'Unit: Gargantula, invalid cost: 525, correct cost: 515', 'Unit: Great Green Idol, invalid cost: 450, correct cost: 455']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4500, correct cost: 4411', 'Unit: Death Cult Hierarch, invalid cost: 565, correct cost: 570', 'Unit: Tomb Harbinger, invalid cost: 315, correct cost: 295', 'Unit: Tomb Architect, invalid cost: 205, correct cost: 200', 'Unit: Skeletons, invalid cost: 470, correct cost: 465', 'Unit: Skeleton Scouts, invalid cost: 140, correct cost: 145', 'Unit: Skeleton Scouts, invalid cost: 140, correct cost: 145', 'Unit: Skeleton Scouts, invalid cost: 140, correct cost: 145', 'Unit: Tomb Cataphracts, invalid cost: 660, correct cost: 655', 'Unit: Necropolis Guard, invalid cost: 405, correct cost: 366', 'Unit: Battle Sphinx, invalid cost: 480, correct cost: 470', 'Unit: Dread Sphinx, invalid cost: 450, correct cost: 430', 'Unit: Ancient Giant, invalid cost: 280, correct cost: 275']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4498, correct cost: 4211', 'Unit: Heavy Infantry, Could not find option Parent Unit', 'Unit: Heavy Infantry, Could not find option Parent Unit', 'Unit: Heavy Infantry, Could not find option Support Unit', 'Unit: Heavy Infantry, Could not find option Support Unit', 'Unit: Marshal, invalid cost: 335, correct cost: 325', 'Unit: Marshal, invalid cost: 250, correct cost: 240', 'Unit: Wizard, invalid cost: 240, correct cost: 250', 'Unit: Heavy Infantry, invalid cost: 339, correct cost: 283', 'Unit: Heavy Infantry, invalid cost: 339, correct cost: 283', 'Unit: Heavy Infantry, invalid cost: 185, correct cost: 161', 'Unit: Heavy Infantry, invalid cost: 185, correct cost: 161', 'Unit: Light Infantry, invalid cost: 315, correct cost: 310', 'Unit: Light Infantry, invalid cost: 155, correct cost: 141', 'Unit: Electoral Cavalry, invalid cost: 243, correct cost: 213', 'Unit: State Militia, invalid cost: 159, correct cost: 152', 'Unit: State Militia, invalid cost: 159, correct cost: 152', 'Unit: State Militia, invalid cost: 159, correct cost: 152', 'Unit: State Militia, invalid cost: 159, correct cost: 152', 'Unit: Imperial Guard, invalid cost: 256, correct cost: 251', 'Unit: Artillery, invalid cost: 245, correct cost: 240', 'Unit: Artillery, invalid cost: 190, correct cost: 180', 'Unit: Imperial Giant, invalid cost: 310, correct cost: 290']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4496, correct cost: 4145', 'Unit: Dragon Seeker, invalid cost: 405, correct cost: 400', 'Unit: Dragon Seeker, invalid cost: 395, correct cost: 390', 'Unit: Thane, invalid cost: 315, correct cost: 310', 'Unit: Runic Smith, invalid cost: 295, correct cost: 275', 'Unit: Engineer, invalid cost: 130, correct cost: 125', 'Unit: Engineer, invalid cost: 130, correct cost: 125', 'Unit: Greybeards, invalid cost: 487, correct cost: 436', 'Unit: Clan Warriors, invalid cost: 447, correct cost: 358', 'Unit: Clan Marksmen, invalid cost: 220, correct cost: 188', 'Unit: Hold Guardians, invalid cost: 595, correct cost: 580', 'Unit: Seekers, invalid cost: 577, correct cost: 488', 'Unit: Field Artillery, invalid cost: 250, correct cost: 235', 'Unit: Field Artillery, invalid cost: 250, correct cost: 235']}, {'player_name': None, 'validation_errors': ['Army: Invalid cost: 4500, correct cost: 4232', 'Unit: Vampire Knights, Could not find option Blood Ties', 'Unit: Vampire Count, invalid cost: 895, correct cost: 885', 'Unit: Necromancer, invalid cost: 520, correct cost: 535', 'Unit: Banshee, invalid cost: 155, correct cost: 145', 'Unit: Banshee, invalid cost: 155, correct cost: 145', 'Unit: Ghouls, invalid cost: 615, correct cost: 575', 'Unit: Skeletons, invalid cost: 230, correct cost: 220', 'Unit: Zombies, invalid cost: 145, correct cost: 140', 'Unit: Great Bats, invalid cost: 100, correct cost: 95', 'Unit: Phantom Hosts, invalid cost: 235, correct cost: 218', 'Unit: Vampire Knights, invalid cost: 625, correct cost: 489', 'Unit: Varkolak, invalid cost: 345, correct cost: 325', 'Unit: Varkolak, invalid cost: 345, correct cost: 325']}]}
    request_body = {
        "file_name": "Strength in Numbers 2021.json",
        "list_number": 39,
        "output_table": "all_lists:tournament_lists",
    }
    json_message = {"data": {"body": request_body}, "army_info": {"body": army_info}}
    request_obj = Request.from_values(json=json_message)
    function_discord_success_reporting(request_obj)
