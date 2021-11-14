from google.cloud import bigquery
from google.cloud import storage


def download_blob(bucket_name, blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.get_blob(blob_name)

    return blob


def function_upload_data_into_bigquery(request):

    # print(request.get_json())

    request_body = request.get_json()["json_file"]["body"]
    print(request_body)

    if request_body != "Uploaded file was not of extension \'.docx\' so is being ignored.":

        filename = request_body["filename"]
        bucket_name = request_body["bucket_name"]
        client = bigquery.Client()
        dataset_id = 'all_lists'
        table_id = 'tournament_lists'

        downloaded_docx_blob = download_blob(bucket_name, filename)
        downloaded_docx_blob.download_to_filename(f"/tmp/{filename}")

        dataset_ref = client.dataset(dataset_id)
        table_ref = dataset_ref.table(table_id)
        job_config = bigquery.LoadJobConfig()
        job_config.source_format = bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
        job_config.autodetect = True

        with open(f"/tmp/{filename}", "rb") as source_file:
            job = client.load_table_from_file(
                source_file,
                table_ref,
                location="US",  # Must match the destination dataset location.
                job_config=job_config,
            )  # API request

        job.result()  # Waits for table load to complete.

        print("Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, table_id))