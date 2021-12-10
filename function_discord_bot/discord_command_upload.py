
from flask.wrappers import Request
from google.cloud import storage
import requests
from pathlib import Path

from os import remove


def upload_file(request: Request):
    data = request.json["data"]
    message_id = data["target_id"]
    attachments = data["resolved"]["messages"][message_id]["attachments"]
    uploaded_files = []
    upload_bucket = "tournament-lists"
    print(f"DEBUG: All attachments: {attachments}")

    for attachment in attachments:
        print(f"DEBUG: Current attachment: {attachment}")
        url: str = attachment["url"]
        filename: str = attachment["filename"]

        download_file_path = f"/tmp/{filename}"

        r = requests.get(url, allow_redirects=True)
        open(download_file_path, 'wb').write(r.content)

        # removing `_` from file name as well as "/tmp/"
        proper_name = Path(filename.replace("_", " ")).name

        upload_blob(upload_bucket, download_file_path, proper_name)
        uploaded_files.append(filename)
        remove(download_file_path)

    return f"Files: {uploaded_files} successfully received, please await parsing results."




def upload_blob(bucket_name, file_path, destination_blob_name) -> None:
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)

    print('File {} uploaded to {}.'.format(
        destination_blob_name,
        bucket_name))
