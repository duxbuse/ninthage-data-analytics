from google.cloud import storage
from pathlib import Path

import requests
from converter import Convert


def download_blob(bucket_name, blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob


def upload_blob(bucket_name, blob_text, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(blob_text)

    print('File {} uploaded to {}.'.format(
        destination_blob_name,
        bucket_name))


def function_data_conversion(request):


    data = request.json["data"]
    print(f"request.json = {data}")

    bucket_name = data["bucket"]
    file_name = data["name"]

    downloaded_docx_blob = download_blob(bucket_name, file_name)
    downloaded_docx_blob.download_to_filename(f"/tmp/{file_name}")
    print(f"Downloaded {file_name} from {bucket_name}")

    converted_file = Convert(f"/tmp/{file_name}")
    print(f"Converted /tmp/{file_name} to .json")

    converted_filename = Path(file_name).stem + ".json"

    upload_blob(bucket_name, converted_file, converted_filename)
    print(f"Uploaded {converted_filename} to {bucket_name}")





if __name__ == "__main__":
    function_data_conversion()