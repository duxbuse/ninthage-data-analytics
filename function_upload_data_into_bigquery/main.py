from typing import Union
from google.cloud import bigquery
from google.cloud import storage
from google.api_core.exceptions import BadRequest
from flask.wrappers import Request
import json
from pathlib import Path
from os import remove


from google.cloud.storage.blob import Blob

def download_blob(bucket_name:str, blob_name:str) -> Union[Blob, None]:
    """Downloads a file from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob



def function_upload_data_into_bigquery(request:Request, is_remote:bool = True) -> tuple[str, int]:

    assert request is not None
    
    request_body = request.json["json_file"]["body"]
    print(f"request.json = {request_body}")

    if not "message" in request_body:

        filename = request_body["file_name"]
        bucket_name = request_body["bucket_name"]
        dataset_id = 'all_lists'
        table_id = 'tournament_lists'

        if is_remote:
            client = bigquery.Client()
            downloaded_json_blob = download_blob(bucket_name, filename)
            file_path = f"/tmp/{filename}"
            if downloaded_json_blob:
                downloaded_json_blob.download_to_filename(file_path)
            else:
                raise ValueError(f"Download of file {filename} from {bucket_name} failed.")
        else:
            from google.oauth2 import service_account
            file_path = f"data/{filename}"
            key_path = "ninthage-data-analytics-3eeb86b69c3a.json"
            credentials = service_account.Credentials.from_service_account_file(key_path)
            client = bigquery.Client(credentials=credentials)

        # Clear data that we are overwritting
        tournament_name = Path(filename).stem
        query_string = f"""
        DELETE
        FROM `ninthage-data-analytics.all_lists.tournament_lists`
        WHERE `tournament` = "{tournament_name}"
        """

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
            print("Upload job failed:")
            for err in job.errors:
                    print(err)
            return json.dumps({"message": job.errors}), 400


        print("Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table_id))
        remove(file_path)

        

        return json.dumps({"list_number": job.output_rows, "file_name": filename, "output_table": f"{dataset_id}:{table_id}"}), 200
    return "Do nothing cause no file was parsed", 200

if __name__ == "__main__":
    filename = "Round 2.json"
    request_payload = {'json_file': {'body': {'bucket_name': 'tournament-lists-json', 'file_name': filename}} }

    request_obj = Request.from_values(json=request_payload)

    print(f"request_payload = {request_payload}")
    status = function_upload_data_into_bigquery(request=request_obj, is_remote=False)
    print(status)