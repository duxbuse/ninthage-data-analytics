from google.cloud import storage
from pathlib import Path
from converter import Convert_docx_to_list, Write_army_lists_to_json_file


def download_blob(bucket_name, blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob


def upload_blob(bucket_name, file_path, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(file_path)

    print('File {} uploaded to {}.'.format(
        destination_blob_name,
        bucket_name))


def function_data_conversion(request):
    """Google Cloud Function that upon invocation downloads a .docx file and converts it into newline delimetered .json

    Args:
        request (flask.request): http request object, expecting the body to have a data json object that has buck file upload details
    """

    data = request.json["data"]
    print(f"request.json = {data}")

    bucket_name = data["bucket"]
    file_name = data["name"]

    # only convert .docx files, because the json verions are also put back into the bucket there is another trigger
    if Path(file_name).suffix == ".docx":

        downloaded_docx_blob = download_blob(bucket_name, file_name)
        downloaded_docx_blob.download_to_filename(f"/tmp/{file_name}")
        print(f"Downloaded {file_name} from {bucket_name}")

        list_of_armies = Convert_docx_to_list(f"/tmp/{file_name}")

        converted_filename = Path(file_name).parent / (Path(file_name).stem + ".json")
        Write_army_lists_to_json_file(converted_filename, list_of_armies)
        print(f"Converted /tmp/{file_name} to {converted_filename}")

        upload_blob(bucket_name, converted_filename, converted_filename)
        print(f"Uploaded {converted_filename} to {bucket_name}")

        return {"bucket_name": bucket_name,  "filename": converted_filename}


if __name__ == "__main__":
    function_data_conversion()
