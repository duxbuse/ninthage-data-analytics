import traceback
from google.cloud import storage
from pathlib import Path
from typing import Union
from google.cloud.storage.blob import Blob
from flask.wrappers import Request
from fuzzywuzzy import fuzz
from os import remove
from converter import Convert_lines_to_army_list, Write_army_lists_to_json_file
from game_report import armies_from_report
from tourney_keeper import get_recent_tournaments
from utility_functions import Docx_to_line_list
from multi_error import Multi_Error


def download_blob(bucket_name, blob_name) -> Union[Blob, None]:
    """Downloads a file from a bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob


def upload_blob(bucket_name, file_path, destination_blob_name) -> None:
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
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
    print(f"request.json = {data}")

    list_of_armies = []
    file_name = data["name"]
    download_file_path = f"/tmp/{file_name}"

    upload_bucket = "tournament-lists-json"

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
    json_message = {'data': {'deployment_selected': ['3 Counter Thrust'], 'game_date': ['2021-12-10'], 'map_selected': [''], 'name': 'manual game report', 'objective_selected': ['5 Capture the Flags'], 'player1_army': ["++ Dwarven Holds (Dwarven Holds 2021) [4,500pts] ++\r\n\r\n+ Characters +\r\n\r\nThane [290pts]: Ancestral Memory, Army General, Crossbow (3+), Hand Weapon, Shield\r\n. Runic Special Items: Rune of Denial - Dominant, 2x Rune of Shielding\r\n\r\n+ Core +\r\n\r\nClan Marksmen [298pts]: 16x Clan Marksman, Crossbow (4+)\r\n\r\nClan Marksmen [280pts]: 15x Clan Marksman, Crossbow (4+)\r\n\r\nClan Marksmen [280pts]: 15x Clan Marksman, Crossbow (4+)\r\n\r\nClan Marksmen [272pts]: 14x Clan Marksman, Crossbow (4+), Standard Bearer\r\n\r\n+ Engines of War +\r\n\r\nField Artillery [250pts]: Cannon (4+)\r\n\r\nField Artillery [300pts]\r\n. Catapult (4+): Rune Crafted\r\n\r\n+ Special +\r\n\r\nKing's Guard [653pts]: Champion, 28x King's Guard, Musician, Standard Bearer\r\n. Runic Banner Enchantment: Banner of Discipline\r\n\r\nKing's Guard [653pts]: Champion, 28x King's Guard, Musician, Standard Bearer\r\n. Runic Banner Enchantment: Banner of Discipline\r\n\r\nKing's Guard [674pts]: Champion, 29x King's Guard, Musician, Standard Bearer\r\n. Runic Banner Enchantment: Banner of Discipline\r\n\r\nSeekers [550pts]: Champion, Musician, 25x Seeker\r\n\r\n++ Total: [4,500pts] ++\r\n\r\nCreated with BattleScribe (https://battlescribe.net)"], 'player1_name': ['Sander'], 'player1_score': ['0'], 'player1_vps': [''], 'player2_army': ["Vermin Swarm\r\n685 - Bloodfur Legate, General, Triumphal Platform, Greater Eagle Standard (Sacred Aquila), Paired Weapons (Hero's Heart), Crown of the Wizard King, Cowl of the Apostate\r\n475 - Swarm Priest, Sacred Platform (Whispering Bell, Great Weapon), Wizard Adept, Witchcraft, Rod of Battle, Caelysian Pantheon\r\n320 - Swarm Priest, Wizard Adept, Thaumaturgy, Light Armour (Destiny's Call), Hand Weapon (Swarm Master), Holy Triumvirate, Cult of Errahman\r\n260 - Swarm Priest, Wizard Adept, Thaumaturgy, Orator's Toga, Holy Triumvirate, Cult of Errahman\r\n575 - 50 Blackfur Veterans, Champion, Musician, Standard Bearer with Eagle Standard (Bell of the Deep Roads)\r\n349 - 44 Vermin Legionaries, Shield and Spear, Champion, Musician, Standard Bearer with Eagle Standard (Legion Standard)\r\n220 - 55 Vermin Slaves, Musician\r\n510 - 11 Fetthis Brutes, Champion\r\n475 - 39 Plague Disciples, Great Weapon, Champion, Musician, Standard Bearer (Banner of the Relentless Company)\r\n445 - 39 Plague Disciples, Great Weapon, Champion, Musician, Standard Bearer (Legion Standard)\r\n185 - 4 Experimental Weapon Teams, Jezail and Shield\r\n4499"], 'player2_name': ['Niek'], 'player2_score': ['20'], 'player2_vps': [''], 'won_secondary': ['player2']}}

    request_obj = Request.from_values(json=json_message)
    (results, code) = function_data_conversion(request_obj)
    if code != 200 and results.get("message"):
        print(results["message"])
