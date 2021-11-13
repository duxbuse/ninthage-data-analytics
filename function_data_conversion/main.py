from google.cloud import storage
from pathlib import Path
from converter import Convert

def download_blob(bucket_name, blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob.download_as_text


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


    print(f"request = {request}")

    bucket_name = request.data["bucket"]
    file_name = request.data["name"]

    downloaded_docx = download_blob(bucket_name, file_name)
    print(f"Downloaded ${file_name} from ${bucket_name}")

    converted_file = Convert(downloaded_docx)
    print(f"Converted ${file_name} to .json")

    converted_filename = Path(file_name).stem + ".json"

    upload_blob(bucket_name, converted_file, converted_filename)
    print(f"Uploaded ${converted_filename} to ${bucket_name}")





if __name__ == "__main__":
    function_data_conversion()