import json
from os import remove
from pathlib import Path
from typing import Union

import google.cloud.bigquery
import google.cloud.bigquery.table
import google.cloud.storage
from flask.wrappers import Request
from google.api_core.exceptions import BadRequest
from google.cloud.storage.blob import Blob


def download_blob(bucket_name: str, blob_name: str) -> Union[Blob, None]:
    """Downloads a file from the bucket."""
    storage_client = google.cloud.storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob


def delete_blob(bucket_name: str, blob_name: str) -> None:
    """
    Deletes a blob from the bucket.
    bucket_name = "your-bucket-name"
    blob_name = "your-file-name"
    """
    storage_client = google.cloud.storage.Client()

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
        dataset_id = "list_data"
        table_id = "tournament_lists"

        # Running on gcp
        if is_remote:
            client = google.cloud.bigquery.Client()
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
            client = google.cloud.bigquery.Client(credentials=credentials)

        # skip uploads for test files
        if "t9a-data-test" in filename:
            print("Skipping upload due to test file")
            num_lines = sum(1 for _ in open(file_path))
            return {
                "list_number": num_lines,
                "file_name": filename,
                "output_table": f"File was a test file so skipping upload",
            }, 200


        # Clear data that we are overwriting
        # ---------------------------------------------------------
        tournament_name = Path(filename).stem
        if "new-recruit-" in tournament_name:
            data_source = "NEW_RECRUIT"
            with open(file_path, 'r') as f:
                data = json.loads(f.readline())
                if data and "tournament" in data:
                    tournament_name = data["tournament"]
        else:
            data_source = "TOURNEY_KEEPER"        

        query_string = f"""
        DELETE
        FROM `ninthage-data-analytics.{dataset_id}.{table_id}`
        WHERE `tournament` = "{tournament_name}" AND data_source = "{data_source}"
        """
        # Dont delete if its a manual report because its not the same event
        dont_delete = ["manual game report", "fading flame", "warhall"]
        if tournament_name not in dont_delete:
            delete_result = client.query(query_string).result()

            if not isinstance(delete_result, google.cloud.bigquery.table._EmptyRowIterator):
                raise ValueError(f"Delete failed for {tournament_name=} from {data_source=}")
            print(f"deleted {tournament_name=} from {data_source=}")

        # Save new data
        # ------------------------------------------------------------
        dataset_ref = client.dataset(dataset_id)
        table_ref = dataset_ref.table(table_id)
        job_config = google.cloud.bigquery.LoadJobConfig()
        job_config.source_format = google.cloud.bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        job_config.autodetect = True

        with open(file_path, "rb") as source_file:
            job = client.load_table_from_file(
                source_file,
                table_ref,
                location="us-central1",  # Must match the destination dataset location.
                job_config=job_config,
                num_retries=20, #sometimes we get rate limited
                timeout=5.0,
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
