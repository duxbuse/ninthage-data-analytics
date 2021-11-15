from google.cloud import bigquery
from google.cloud import storage
from google.api_core.exceptions import BadRequest
import json

def download_blob(bucket_name, blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob


def function_upload_data_into_bigquery(request, is_remote = True):

    request_body = json.loads(request.json["json_file"]["body"])
    print(f"request.json = {request_body}")

    if not "message" in request_body:

        filename = request_body["filename"]
        bucket_name = request_body["bucket_name"]
        client = bigquery.Client()
        dataset_id = 'all_lists'
        table_id = 'tournament_lists'
        if is_remote:
            downloaded_docx_blob = download_blob(bucket_name, filename)
            file_path = f"/tmp/{filename}"
            downloaded_docx_blob.download_to_filename(file_path)
        else:
            file_path = f"data/{filename}"


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
            raise



        print("Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table_id))
    return "its over"

if __name__ == "__main__":
    import sys
    from flask import Request

    if len(sys.argv) > 1:
        request_payload = {'json_file': {'body': sys.argv[1]} }
    else:
        request_payload = {'json_file': {'body': '{"bucket_name": "tournament-lists-json", "filename": "Round 1.json"}'} }

    request_obj = Request.from_values(json=request_payload)

    print(f"request_payload = {request_payload}")
    status = function_upload_data_into_bigquery(request=request_obj, is_remote=False)
    print(status)