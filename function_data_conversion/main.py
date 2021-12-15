from google.cloud import storage
from pathlib import Path
from typing import Union
from google.cloud.storage.blob import Blob
from fuzzywuzzy import fuzz
from os import remove
from converter import Convert_lines_to_army_list, Write_army_lists_to_json_file
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


def function_data_conversion(request) -> tuple[dict, int]:
    """Google Cloud Function that upon invocation downloads a .docx file and converts it into newline delimetered .json

    Args:
        request (flask.request): http request object, expecting the body to have a data json object that has buck file upload details
    """

    data = request.json["data"]
    print(f"request.json = {data}")

    if data.get("bucket"):
        bucket_name = data["bucket"]
        upload_bucket = "tournament-lists-json"
        file_name = data["name"]

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
                loaded_tk_info = any(army.list_placing > 0 for army in list_of_armies)
                possible_tk_names = []
                if not loaded_tk_info:
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
                    if len(x.validation_errors) > 0
                ]

                upload_filename = Path(download_file_path).stem + ".json"
                converted_filename = str(
                    Path(download_file_path).parent / upload_filename
                )
                Write_army_lists_to_json_file(converted_filename, list_of_armies)
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
            except Multi_Error as e:
                return {"message": [str(x) for x in e.errors]}, 400

        return {
            "message": [
                f"Uploaded file:{file_name} was not of extension '.docx' so is being ignored."
            ]
        }, 400
    elif data.get("player_score"):
        # Game reported through web form
        return {"message": [f"Manual game reporting not yet implemented."]}, 400
        player1 = "\n".join([data["player1_name"], data["player1_army"]])
        player2 = "\n".join([data["player2_name"], data["player2_army"]])
        lines = "\n".join([player1, player2])
        list_of_armies = Convert_lines_to_army_list(event_name, lines)
    else:
        {
            "message": [
                f"Data was neither an uploaded word .docx or a manual upload from game reporter."
            ]
        }, 400


if __name__ == "__main__":
    # function_data_conversion()
    pass
