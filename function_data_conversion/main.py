import re
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
    upload_bucket = "tournament-lists-json"

    if data.get("bucket"):
        bucket_name = data["bucket"]

        # only convert .docx files, because the json versions are also put back into the bucket there is another trigger
        if Path(file_name).suffix == ".docx":
            try:
                downloaded_docx_blob = download_blob(bucket_name, file_name)
                download_file_path = f"/tmp/{file_name}"
                downloaded_docx_blob.download_to_filename(download_file_path)
                print(
                    f"Downloaded {file_name} from {bucket_name} to {download_file_path}"
                )

                event_name = Path(download_file_path).stem
                lines = Docx_to_line_list(download_file_path)

                list_of_armies = Convert_lines_to_army_list(event_name, lines)
            except Multi_Error as e:
                return {"message": [str(x) for x in e.errors]}, 400
            except Exception as e:
                return {"message": [str(e)]}, 400
        else:
            return {
                "message": [
                    f"Uploaded file:{file_name} was not of extension '.docx' so is being ignored."
                ]
            }, 400
    elif data.get("player1_army"):
        try:
            list_of_armies = armies_from_report(data, Path(file_name).stem)

        except Multi_Error as e:
            return {"message": [str(x) for x in e.errors]}, 400
        except Exception as e:
            return {"message": [str(e)]}, 400
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
        not loaded_tk_info and download_file_path is not "/tmp/manual game report"
    ):  # Find name of close events since a misname may be why nothing was loaded.
        recent_tournaments = get_recent_tournaments()
        for tournament in recent_tournaments:
            ratio = fuzz.token_sort_ratio(
                Path(download_file_path).stem, tournament.get("Name")
            )
            if ratio > 80:
                possible_tk_names.append((tournament, ratio))
    else:
        possible_tk_names = [Path(download_file_path).stem]

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
        return {"message": [str(e)]}, 400
    print(f"Converted {download_file_path} to {converted_filename}")

    upload_blob(upload_bucket, converted_filename, upload_filename)
    print(f"Uploaded {upload_filename} to {upload_bucket}")
    remove(download_file_path)
    remove(converted_filename)
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
    json_message = {
        "data": {
            "player1_army": [
                "BH\n635 - Beast Lord, General, Beast Axe, Heavy  Armour, Hunting Call, Razortusk Chariot, Shield,  Death Cheater, Fatal Folly, Seed of the Dark  Forest\n110 - 1 Raiding Chariot\n110 - 1 Raiding Chariot\n110 - 1 Raiding Chariot 110 - 1 Raiding Chariot\n 110 - 1 Raiding Chariot\n110 - 1 Raiding Chariot"
            ],
            "player1_name": ["bob"],
            "player1_score": ["12"],
            "player1_vps": ["4567"],
            "player2_army": [""],
            "player1_magic": ["H", "DR1", "DR2", "DR3", "DR4", "DR5"],
            "player2_name": ["alice"],
            "player2_score": ["8"],
            "player2_vps": ["1234"],
            "player2_magic": ["H"],
            "map_selected": ["B5"],
            "deployment_selected": ["3 Counter Thrust"],
            "objective_selected": ["4 King of the Hill"],
            "game_date": ["2021-12-24"],
            "dropped_all": ["player2"],
        }
    }

    request_obj = Request.from_values(json=json_message)
    (results, code) = function_data_conversion(request_obj)
    if code != 200 and results.get("message"):
        print(results["message"])
