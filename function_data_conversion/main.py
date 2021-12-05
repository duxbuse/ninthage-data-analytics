from google.cloud import storage
from pathlib import Path
from typing import Union
from google.cloud.storage.blob import Blob
from os import remove

import jsons
from converter import Convert_docx_to_list, Write_army_lists_to_json_file


def download_blob(bucket_name, blob_name) ->  Union[Blob, None]:
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

    print('File {} uploaded to {}.'.format(
        destination_blob_name,
        bucket_name))

# TODO: Need to catch all exceptions and return them so that we have the reason to pass to the discord chat
def function_data_conversion(request) -> str:
    """Google Cloud Function that upon invocation downloads a .docx file and converts it into newline delimetered .json

    Args:
        request (flask.request): http request object, expecting the body to have a data json object that has buck file upload details
    """

    data = request.json["data"]
    print(f"request.json = {data}")

    bucket_name = data["bucket"]
    upload_bucket = "tournament-lists-json"
    file_name = data["name"]

    # only convert .docx files, because the json versions are also put back into the bucket there is another trigger
    if Path(file_name).suffix == ".docx":

        downloaded_docx_blob = download_blob(bucket_name, file_name)
        download_file_path = f"/tmp/{file_name}"
        downloaded_docx_blob.download_to_filename(download_file_path)
        print(f"Downloaded {file_name} from {bucket_name} to {download_file_path}")

        list_of_armies = Convert_docx_to_list(download_file_path)

        upload_filename = Path(download_file_path).stem + ".json"
        converted_filename = str(Path(download_file_path).parent / upload_filename)
        Write_army_lists_to_json_file(converted_filename, list_of_armies)
        print(f"Converted {download_file_path} to {converted_filename}")

        upload_blob(upload_bucket, converted_filename, upload_filename)
        print(f"Uploaded {upload_filename} to {upload_bucket}")
        remove(download_file_path)
        remove(converted_filename)
        return jsons.dumps({"bucket_name": upload_bucket,  "filename": upload_filename})

    return jsons.dumps({"message": "Uploaded file was not of extension '.docx' so is being ignored."})

if __name__ == "__main__":
    # function_data_conversion()
    pass
