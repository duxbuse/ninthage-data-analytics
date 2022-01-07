import traceback
import google.cloud.storage
from pathlib import Path
from typing import Union
from google.cloud.storage.blob import Blob
from flask.wrappers import Request
from fuzzywuzzy import fuzz
from os import remove
import json
from converter import Convert_lines_to_army_list, Write_army_lists_to_json_file
from game_report import armies_from_report
from fading_flame import armies_from_fading_flame
from tourney_keeper import get_recent_tournaments
from utility_functions import Docx_to_line_list
from multi_error import Multi_Error


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

                list_of_armies = Convert_lines_to_army_list(event_name, lines)
            except Multi_Error as e:
                print(f"Multi_Error1: {[str(x) for x in e.errors]}")
                return {"message": [str(x) for x in e.errors]}, 400
            except Exception as e:
                tb1 = traceback.TracebackException.from_exception(e)
                print(f"Captured non multi error:\n {''.join(tb1.format())}")
                return {"message": [str(e)]}, 501
        else:
            return {
                "message": [
                    f"Uploaded file:{file_name} was not of extension '.docx' so is being ignored."
                ]
            }, 400
    # manual game report
    elif data.get("player1_army"):
        try:
            list_of_armies = armies_from_report(data, Path(file_name).stem)

        except Multi_Error as e:
            print(f"Multi_Error2: {[str(x) for x in e.errors]}")
            return {"message": [str(x) for x in e.errors]}, 400
        except Exception as e:
            print(f"None Multi Error: {str(type(e))}, {str(e)}")
            return {"message": [str(e)]}, 501
    # Fading Flame data
    elif file_name == "fading_flame.json":
        try:
            downloaded_docx_blob = download_blob("fading-flame", file_name)
            downloaded_docx_blob.download_to_filename(download_file_path)
            print(
                f"Downloaded {file_name} from fading-flame to {download_file_path}"
            )
            with open(download_file_path, "r") as json_file:
                data = json.load(json_file)
            remove(download_file_path)
            list_of_armies = armies_from_fading_flame(data)

        except Multi_Error as e:
            print(f"Multi_Error2: {[str(x) for x in e.errors]}")
            return {"message": [str(x) for x in e.errors]}, 400
        except Exception as e:
            return {"message": [str(e)]}, 501
    else:
        return {
            "message": [
                f"Data was neither an uploaded document or a manual upload from game reporter."
            ]
        }, 400

    loaded_tk_info = any(
        army.list_placing > 0 for army in list_of_armies if army.list_placing
    )
    possible_tk_names = []
    if (
        not loaded_tk_info and file_name != "manual game report"
    ):  # Find name of close events since a misname may be why nothing was loaded.
        recent_tournaments = get_recent_tournaments()
        for tournament in recent_tournaments:
            ratio = fuzz.token_sort_ratio(Path(file_name).stem, tournament.get("Name"))
            if ratio > 80:
                possible_tk_names.append((tournament, ratio))
    else:
        possible_tk_names = ["N/A"]

    validation_count = sum(1 for i in list_of_armies if i.validated)
    validation_errors = [
        {
            "player_name": x.player_name,
            "validation_errors": x.validation_errors,
        }
        for x in list_of_armies
        if x.validation_errors
    ]

    upload_filename = Path(download_file_path).stem + ".json"
    converted_filename = Path(download_file_path).parent / upload_filename
    try:
        Write_army_lists_to_json_file(converted_filename, list_of_armies)
    except Exception as e:
        print(f"error writing to json file")
        return {"message": [str(e)]}, 400
    print(f"Converted {download_file_path} to {converted_filename}")

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
        loaded_tk_info=loaded_tk_info,
        possible_tk_names=possible_tk_names,
        validation_count=validation_count,
        validation_errors=validation_errors,
    )
    return return_dict, 200


if __name__ == "__main__":
    json_message = {"data": {'deployment_selected': ['2 Dawn Assault'], 'dropped_all': ['player2'], 'game_date': ['2022-01-06'], 'map_selected': ['A8'], 'name': 'manual game report', 'objective_selected': ['1 Hold the Ground'], 'player1_army': ["Warriors of the Dark Gods\r\n485 - Sorcerer, Wizard Master, Evocation, Light Armour, Magical Heirloom, Ranger's Boots\r\n340 - Barbarian Chief, General, Black Steed (Prized Stallion), Shield, Heavy Armour, Hand Weapon (Burning Portent), Potion of Swiftness\r\n295 - Barbarian Chief, Shadow Chaser, Heavy Armour (Thrice-Forged), Paired Weapons (Shield Breaker)\r\n235 - Barbarian Chief, War Dais, Heavy Armour, Paired Weapons (Symbol of Slaughter), Rod of Battle\r\n385 - 40 Barbarians, Throwing Weapons, Paired Weapons, Standard Bearer (Wasteland Torch), Musician, Champion\r\n295 - 30 Barbarians, Shield, Standard Bearer (Legion Standard), Musician, Champion\r\n220 - 10 Fallen\r\n520 - 8 Warrior Knights, Lance, Pride, Standard Bearer (Stalker's Standard), Musician, Champion\r\n409 - 3 Chosen Knights, Wrath\r\n330 - 4 Wretched Ones\r\n320 - Battleshrine\r\n300 - Marauding Giant, Tribal Warspear\r\n200 - Chimera\r\n165 - 5 Flayers, Shield\r\n4499\r\n"], 'player1_magic': ['H', 'E1', 'E2', 'E3', 'E5', 'O6'], 'player1_name': ['Tom'], 'player1_score': ['16'], 'player1_vps': [''], 'player2_army': ["Kingdom of Equitaine\r\n505 - Equitan Lord, Pegasus Charger, Shield, Lance (Divine Judgement), Basalt Infusion, Sacred Chalice, Paladin, Honour\r\n485 - Damsel, Destrier, Wizard Master, Shamanism, Binding Scroll\r\n395 - Damsel, General, Revered Unicorn, Wizard Adept, Divination, Crystal Ball, Sainted\r\n340 - Folk Hero, Destrier, Paired Weapons, Battle Standard Bearer (Aether Icon, Aether Icon), Light Armour (Essence of Mithril), Bannerman, Castellan, Faith\r\n670 - 15 Feudal Knights, Champion (Knight Banneret), Musician, Standard Bearer (Stalker's Standard)\r\n275 - 6 Feudal Knights, Champion, Musician\r\n275 - 6 Feudal Knights, Champion, Musician\r\n650 - 5 Pegasus Knights, Champion (Knight Banneret (Oriflamme)), Standard Bearer (Banner of Speed)\r\n340 - 6 Sky Heralds, Paired Weapons, Champion\r\n135 - 5 Yeoman Outriders, Bow\r\n430 - The Lady's Courtier, Courtier of the Dawn\r\n4500"], 'player2_magic': ['H', 'DV3', 'DV4', 'S1', 'S2', 'S6'], 'player2_name': ['Erdem'], 'player2_score': ['4'], 'player2_vps': [''], 'who_deployed': ['player2'], 'who_started': ['player2'], 'won_secondary': ['player1']}}

    request_obj = Request.from_values(json=json_message)
    (results, code) = function_data_conversion(request_obj)
    if code != 200 and results.get("message"):
        print(results["message"])
