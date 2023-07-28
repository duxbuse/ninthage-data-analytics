import json
import traceback
from os import remove
from pathlib import Path
from typing import Union

import google.cloud.storage
from flask.wrappers import Request
from google.cloud.storage.blob import Blob

from converter import Write_army_lists_to_json_file
from fading_flame import armies_from_fading_flame
from game_report import armies_from_report
from multi_error import Multi_Error
from new_recruit_tournaments import armies_from_NR_tournament
from tourney_keeper import armies_from_docx
from utility_functions import Docx_to_line_list
from warhall import armies_from_warhall


def download_blob(bucket_name, blob_name) -> Union[Blob, None]:
    """Downloads a file from a bucket."""
    storage_client = google.cloud.storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob


def upload_blob(bucket_name, file_path, destination_blob_name) -> None:
    """Uploads a file to the bucket."""
    storage_client = google.cloud.storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)

    print("File {} uploaded to {}.".format(destination_blob_name, bucket_name))


def function_data_conversion(request: Request) -> tuple[dict, int]:
    """Google Cloud Function that upon invocation downloads a .docx file and converts it into newline delimetered .json

    Args:
        request (flask.request): http request object, expecting the body to have a data json object that has buck file upload details
    """

    data = request.json["data"]
    print(f"{request.json=}")

    list_of_armies = []
    file_name = data["name"]
    download_file_path = f"/tmp/{file_name}"

    upload_bucket = "tournament-lists-json"
    tk_loaded = "N/A"
    possible_matches = ["N/A"]

    # break these into separate functions

    # Uploaded word doc
    if data.get("bucket"):
        bucket_name = data["bucket"]

        # only convert .docx files, because the json versions are also put back into the bucket there is another trigger
        if Path(file_name).suffix == ".docx":
            try:
                downloaded_docx_blob = download_blob(bucket_name, file_name)
                downloaded_docx_blob.download_to_filename(download_file_path)
                print(
                    f"Downloaded {file_name} from {bucket_name} to {download_file_path}"
                )

                event_name = Path(download_file_path).stem
                lines = Docx_to_line_list(download_file_path)

                list_of_armies, tk_loaded, possible_matches = armies_from_docx(event_name, lines)
            except Multi_Error as e:
                print(f"Multi_ErrorWD: {[str(x) for x in e.errors]}")
                return {"message": [str(x) for x in e.errors]}, 400
            except Exception as e:
                tb1 = traceback.TracebackException.from_exception(e)
                print(f"Non multi errorWD:{e}\n {''.join(tb1.format())}")
                return {"message": [str(e)]}, 400
        else:
            return {
                "message": [
                    f"Uploaded file:{file_name} was not of extension '.docx' so is being ignored."
                ]
            }, 400
    
    # manual game report
    elif file_name == "manual game report" or file_name == "manual_game_report":
        try:
            list_of_armies = armies_from_report(data, Path(file_name).stem)

        except Multi_Error as e:
            print(f"Multi_ErrorGR: {[str(x) for x in e.errors]}")
            return {"message": [str(x) for x in e.errors]}, 400
        except Exception as e:
            print(f"Non Multi ErrorGR: {str(type(e))}, {str(e)}")
            return {"message": [str(e)]}, 400
    
    # Fading Flame data
    elif file_name == "fading_flame.json":
        try:
            downloaded_FF_blob = download_blob("fading-flame", file_name)
            downloaded_FF_blob.download_to_filename(download_file_path)
            if downloaded_FF_blob:
                print(
                    f"Downloaded {file_name} from fading-flame to {download_file_path}"
                )
            with open(download_file_path, "r") as json_file:
                data = json.load(json_file)
                print(f"Loaded data")
            remove(download_file_path)
            list_of_armies = armies_from_fading_flame(data)

        except Multi_Error as e:
            print(f"Multi_ErrorFF: {[str(x) for x in e.errors]}")
            return {"message": [str(x) for x in e.errors]}, 400
        except Exception as e:
            print(f"Non Multi ErrorFF: {str(type(e))}, {str(e)}")
            return {"message": [str(e)]}, 400
    
    # Warhall data
    elif file_name == "warhall":
        file_name = data.get("file_name", "")# actually random file name
        download_file_path = f"/tmp/{file_name}"
        try:
            downloaded_warhall_blob = download_blob("warhall", file_name)
            downloaded_warhall_blob.download_to_filename(download_file_path)
            if downloaded_warhall_blob:
                print(
                    f"Downloaded {file_name} from warhall to {download_file_path}"
                )
            with open(download_file_path, "r") as json_file:
                data = json.load(json_file)
                print(f"Loaded data")
            remove(download_file_path)
            list_of_armies = armies_from_warhall(data)

        except Multi_Error as e:
            print(f"File Name: {file_name}, Multi_ErrorWH: {[str(x) for x in e.errors]}")
            return {"message": [str(x) for x in e.errors], "name": file_name}, 400
        except Exception as e:
            print(f"File Name: {file_name}, Non Multi ErrorWH: {str(type(e))}, {str(e)}")
            return {"message": [str(e)], "name": file_name}, 400

    # NEW RECRUIT TOURNAMENTS
    elif file_name == "newrecruit_tournament.json":
        file_name = data.get("event_id", "")# actually random file name
        download_file_path = f"/tmp/new-recruit-{file_name}"
        if __name__ == "__main__":
            import pathlib
            download_file_path = f"{pathlib.Path().resolve()}/data/nr-test-data/{file_name}.json"
        try:
            downloaded_newrecruit_blob = download_blob("newrecruit_tournaments", file_name)
            downloaded_newrecruit_blob.download_to_filename(download_file_path)
            if downloaded_newrecruit_blob:
                print(
                    f"Downloaded {file_name} from newrecruit_tournaments to {download_file_path}"
                )
            with open(download_file_path, "r") as json_file:
                data = json.load(json_file)
                print(f"Loaded data")

            if __name__ != "__main__":     
                remove(download_file_path)

            list_of_armies = armies_from_NR_tournament(data)

        except Multi_Error as e:
            print(f"File Name: {file_name}, Multi_ErrorNR: {[str(x) for x in e.errors]}")
            return {"message": [str(x) for x in e.errors], "name": file_name}, 400
        except Exception as e:
            print(f"File Name: {file_name}, Non Multi ErrorNR: {str(type(e))}, {str(e)}")
            return {"message": [str(e)], "name": file_name}, 400

    else:
        return {
            "message": [
                f"Data was neither an uploaded document or a manual upload from game reporter."
            ]
        }, 400

    #----------------------------------------------------------------------------------------------
    # Calculate validation errors
    #----------------------------------------------------------------------------------------------

    validation_count = sum(1 for i in list_of_armies if i.validated)
    validation_errors = [
        {
            "player_name": x.player_name,
            "validation_errors": x.validation_errors,
        }
        for x in list_of_armies
        if x.validation_errors
    ]

    #----------------------------------------------------------------------------------------------
    # Upload json version
    #----------------------------------------------------------------------------------------------

    upload_filename = Path(download_file_path).stem + ".json"
    if __name__ == "__main__":
        upload_filename = Path(download_file_path).stem + "-converted.json"
    converted_filename = Path(download_file_path).parent / upload_filename


    try:
        Write_army_lists_to_json_file(converted_filename, list_of_armies)
    except Exception as e:
        print(f"error writing to json file")
        return {"message": [str(e)]}, 400
    print(f"Converted {download_file_path} to {converted_filename}")


    if __name__ != "__main__":
        upload_blob(upload_bucket, converted_filename, upload_filename)
        print(f"Uploaded {upload_filename} to {upload_bucket}")
        try:
            if Path(file_name).suffix == ".docx":
                remove(download_file_path)
            remove(converted_filename)
        except FileNotFoundError as e:
            print(f"Failed to remove file: {e}")

        return_dict = dict(
            bucket_name=upload_bucket,
            file_name=upload_filename,
            loaded_tk_info=tk_loaded,
            possible_tk_names=possible_matches,
            validation_count=validation_count,
            validation_errors=validation_errors,
        )
    return return_dict, 200


if __name__ == "__main__":
    # json_message = {"data": {'deployment_selected': ['2 Dawn Assault'], 'dropped_all': ['player2'], 'game_date': ['2022-01-06'], 'map_selected': ['A8'], 'name': 'manual game report', 'objective_selected': ['1 Hold the Ground'], 'player1_army': ["Warriors of the Dark Gods\r\n485 - Sorcerer, Wizard Master, Evocation, Light Armour, Magical Heirloom, Ranger's Boots\r\n340 - Barbarian Chief, General, Black Steed (Prized Stallion), Shield, Heavy Armour, Hand Weapon (Burning Portent), Potion of Swiftness\r\n295 - Barbarian Chief, Shadow Chaser, Heavy Armour (Thrice-Forged), Paired Weapons (Shield Breaker)\r\n235 - Barbarian Chief, War Dais, Heavy Armour, Paired Weapons (Symbol of Slaughter), Rod of Battle\r\n385 - 40 Barbarians, Throwing Weapons, Paired Weapons, Standard Bearer (Wasteland Torch), Musician, Champion\r\n295 - 30 Barbarians, Shield, Standard Bearer (Legion Standard), Musician, Champion\r\n220 - 10 Fallen\r\n520 - 8 Warrior Knights, Lance, Pride, Standard Bearer (Stalker's Standard), Musician, Champion\r\n409 - 3 Chosen Knights, Wrath\r\n330 - 4 Wretched Ones\r\n320 - Battleshrine\r\n300 - Marauding Giant, Tribal Warspear\r\n200 - Chimera\r\n165 - 5 Flayers, Shield\r\n4499\r\n"], 'player1_magic': ['H', 'E1', 'E2', 'E3', 'E5', 'O6'], 'player1_name': ['Tom'], 'player1_score': ['16'], 'player1_vps': [''], 'player2_army': ["Kingdom of Equitaine\r\n505 - Equitan Lord, Pegasus Charger, Shield, Lance (Divine Judgement), Basalt Infusion, Sacred Chalice, Paladin, Honour\r\n485 - Damsel, Destrier, Wizard Master, Shamanism, Binding Scroll\r\n395 - Damsel, General, Revered Unicorn, Wizard Adept, Divination, Crystal Ball, Sainted\r\n340 - Folk Hero, Destrier, Paired Weapons, Battle Standard Bearer (Aether Icon, Aether Icon), Light Armour (Essence of Mithril), Bannerman, Castellan, Faith\r\n670 - 15 Feudal Knights, Champion (Knight Banneret), Musician, Standard Bearer (Stalker's Standard)\r\n275 - 6 Feudal Knights, Champion, Musician\r\n275 - 6 Feudal Knights, Champion, Musician\r\n650 - 5 Pegasus Knights, Champion (Knight Banneret (Oriflamme)), Standard Bearer (Banner of Speed)\r\n340 - 6 Sky Heralds, Paired Weapons, Champion\r\n135 - 5 Yeoman Outriders, Bow\r\n430 - The Lady's Courtier, Courtier of the Dawn\r\n4500"], 'player2_magic': ['H', 'DV3', 'DV4', 'S1', 'S2', 'S6'], 'player2_name': ['Erdem'], 'player2_score': ['4'], 'player2_vps': [''], 'who_deployed': ['player2'], 'who_started': ['player2'], 'won_secondary': ['player1']}}
    # json_message = {'data': {'deployment_selected': ['2 Dawn Assault'], 'game_date': ['2022-02-25'], 'map_selected': ['A1'], 'name': 'manual_game_report', 'objective_selected': ['6 Secure Target'], 'player1_army': ['810 tengu commander general alpha carnosaur halberd (deathstalker) obsidian rock\r\n155 skink commander master tracker infiltrator chart\r\n815 anurarch guardian divination master tablet of atua binding scroll spell breaker mindreader copycat forbidenpath\r\n\r\n380 19 tengu spear pattern of the clever girl\r\n250 15 tengu\r\n205 20 skink javelineers\r\n205 20 skink javelineers\r\n189 9 raptor packs\r\n\r\n300 2X5 cameleons\r\n360 2X3 pteradons\r\n290 2X5 skink hunter with pheromon\r\n\r\n540 1 taurosaur BSB\r\n\r\ntotal 4499'], 'player1_magic': ['P3'], 'player1_name': ['lamronchak'], 'player1_score': ['11'], 'player1_vps': ['2313'], 'player2_army': ["Undying Dynasties\r\n485 - Death Cult Hierarch, Wizard Master, Cosmology, Binding Scroll, Talisman of the Void\r\n300 - Death Cult Hierarch, Wizard Adept, Evocation, Book of Arcane Mastery, Hierophant\r\n430 - Pharaoh, General, Shield (Sun's Embrace), Light Armour (Destiny's Call), Hand Weapon (Scourge of Kings), Death Mask of Teput\r\n200 - Tomb Architect, Light Armour\r\n517 - 59 Skeletons, Spear, Standard Bearer (Aether Icon), Musician, Champion\r\n195 - 17 Skeleton Archers, Musician\r\n125 - 10 Skeleton Archers, Musician\r\n145 - 5 Skeleton Scouts\r\n145 - 5 Skeleton Scouts\r\n712 - 8 Shabtis, Paired Weapons, Musician\r\n525 - 5 Tomb Cataphracts, Musician\r\n291 - 4 Sand Stalkers\r\n430 - Dread Sphinx\r\n4500"], 'player2_magic': ['W5'], 'player2_name': ['gundizalbo'], 'player2_score': ['9'], 'player2_vps': ['1625'], 'who_deployed': ['player1'], 'who_started': ['player2']}}
    json_message = {"data": {
        "event_id": "6362bf252f099e47dcca88c4",
        "name": "newrecruit_tournament.json"
    }}
    request_obj = Request.from_values(json=json_message)
    (results, code) = function_data_conversion(request_obj)
    if code != 200 and results.get("message"):
        print(results["message"])
