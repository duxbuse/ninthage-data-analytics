from typing import Union
from google.cloud import bigquery
from google.cloud import storage
from google.api_core.exceptions import BadRequest
from flask.wrappers import Request
from pathlib import Path
from os import remove


from google.cloud.storage.blob import Blob


def download_blob(bucket_name: str, blob_name: str) -> Union[Blob, None]:
    """Downloads a file from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob


def delete_blob(bucket_name: str, blob_name: str) -> None:
    """Deletes a blob from the bucket."""
    # bucket_name = "your-bucket-name"
    # blob_name = "your-object-name"

    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()

    print("Blob {} deleted.".format(blob_name))


def function_upload_data_into_bigquery(
    request: Request, is_remote: bool = True
) -> tuple[dict, int]:

    print(f"{request.json=}")

    request_body = request.json["json_file"]["body"]
    print(f"request.json = {request_body}")

    if not "message" in request_body:

        filename = request_body["file_name"]
        bucket_name = request_body["bucket_name"]
        dataset_id = "all_lists"
        table_id = "tournament_lists"

        # Running on gcp
        if is_remote:
            client = bigquery.Client()
            downloaded_json_blob = download_blob(bucket_name, filename)
            file_path = f"/tmp/{filename}"
            if downloaded_json_blob:
                downloaded_json_blob.download_to_filename(file_path)
            else:
                raise ValueError(
                    f"Download of file {filename} from {bucket_name} failed."
                )
        # running locally
        else:
            from google.oauth2 import service_account

            file_path = f"data/{filename}"
            key_path = "ninthage-data-analytics-3eeb86b69c3a.json"
            credentials = service_account.Credentials.from_service_account_file(
                key_path
            )
            client = bigquery.Client(credentials=credentials)

        # skip uploads for test files
        if "t9a-data-test" in filename:
            print("Skipping upload due to test file")
            num_lines = sum(1 for _ in open(file_path))
            return {
                "list_number": num_lines,
                "file_name": filename,
                "output_table": f"File was a test file so skipping upload",
            }, 200

        # Clear data that we are overwritting
        tournament_name = Path(filename).stem
        query_string = f"""
        DELETE
        FROM `ninthage-data-analytics.all_lists.tournament_lists`
        WHERE `tournament` = "{tournament_name}"
        """
        # Dont delete if its a manual report because its not the same event
        if tournament_name != "manual game report":
            delete_result = client.query(query_string).result()

            if not isinstance(delete_result, bigquery.table._EmptyRowIterator):
                raise ValueError(f"Delete failed for {tournament_name}")

        # Save new data
        dataset_ref = client.dataset(dataset_id)
        table_ref = dataset_ref.table(table_id)
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        job_config.autodetect = True

        with open(file_path, "rb") as source_file:
            job = client.load_table_from_file(
                source_file,
                table_ref,
                location="US",  # Must match the destination dataset location.
                job_config=job_config,
            )  # API request

        try:
            job.result()  # Waits for table load to complete.
        except BadRequest:
            print(f"Upload job failed: {job.errors=}")
            return {"message": [err["message"] for err in job.errors or []]}, 400

        print(
            "Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table_id)
        )
        # delete local download to reduce function memory
        remove(file_path)
        # delete *.json to reduce bucket storage
        if not is_remote:
            delete_blob(bucket_name, filename)

        return {
            "list_number": job.output_rows,
            "file_name": filename,
            "output_table": f"{dataset_id}:{table_id}",
        }, 200
    return {"message": ["Do nothing cause no file was parsed"]}, 400


if __name__ == "__main__":
    filename = "Round 2.json"
    request_payload = {
        "json_file": {
            "body": {"bucket_name": "tournament-lists-json", "file_name": filename}
        }
    }

    request_obj = Request.from_values(json=request_payload)

    print(f"request_payload = {request_payload}")
    status = function_upload_data_into_bigquery(request=request_obj, is_remote=False)
    print(status)
