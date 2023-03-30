from os import remove
import google.cloud.bigquery
import google.cloud.bigquery.table
from google.api_core.exceptions import BadRequest
from flask.wrappers import Request
import requests
import json
from pathlib import Path



http = requests.Session()

# name of the function in main.py must equal the trigger name as a default or be set explicitly
def function_static_data(request: Request):

    url = f"https://www.9thbuilder.com/en/api/v1/data_analytics/ninth_ages/"
    sections = [
        "versions",
        "armies",
        "organisations",
        "units",
        "magic_paths",
        "special_items",
        "banners",
        "maps",
    ]
    for endpoint in sections:
        try:
            print(f"Fetching: {endpoint}")
            response = http.get(
                url+endpoint,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                    "User-Agent": "ninthage-data-analytics/1.1.0",
                },
                timeout=30,
            ) 
        except requests.exceptions.ReadTimeout as err:
            raise err

        if response.status_code != 200:
            raise ValueError(response.text)
        elif response.json():
            store_data(endpoint, response.json())

    return f"worked", 200


def scrub_list(d):
    scrubbed_list = []
    for i in d:
        if isinstance(i, dict):
            i = scrub_dict(i)
        scrubbed_list.append(i)
    return scrubbed_list

def scrub_dict(d):
    new_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = scrub_dict(v)
        if isinstance(v, list):
            v = scrub_list(v)
        if not v in (u'', None, {}, []):
            new_dict[k] = v
    return new_dict

def write_dicts_to_json(file_path: str, data: list[dict]):
    with open(file_path, "w") as jsonFile:
        pass
    with open(file_path, "a") as jsonFile:
        for item in data:
            no_nulls = scrub_dict(item)
            jsonFile.write(json.dumps(no_nulls)+"\n")

def push_to_bq(local_file: str):
    client = google.cloud.bigquery.Client()
    dataset_id = "9th_builder_static_data"
    source = Path(local_file).stem

    # ---------------------------------------
    # Save new data
    dataset_ref = client.dataset(dataset_id)
    table_ref = dataset_ref.table(source)
    job_config = google.cloud.bigquery.LoadJobConfig()
    job_config.source_format = google.cloud.bigquery.SourceFormat.NEWLINE_DELIMITED_JSON
    job_config.autodetect = True
    job_config.write_disposition = google.cloud.bigquery.WriteDisposition.WRITE_TRUNCATE

    with open(local_file, "rb") as source_file:
        job = client.load_table_from_file(
            source_file,
            table_ref,
            location="us-central1",  # Must match the destination dataset location.
            job_config=job_config,
        )  # API request

        try:
            job.result()  # Waits for table load to complete.
            print(
                "Loaded {} rows into {}:{}.".format(job.output_rows, dataset_id, source)
            )
        except BadRequest:
            print(f"Upload job failed: {job.errors=}")
            raise ValueError({"message": [err["message"] for err in job.errors or []]}, 400)


def store_data(endpoint:str, data:dict):
    local_file = "/tmp/" + endpoint + ".json"
    if __name__ == "__main__":
        local_file = "..\data\9th builder static data\\" + endpoint + ".json"
        

    if isinstance(data.get(endpoint, {}), list):
        write_dicts_to_json(file_path=local_file, data=data.get(endpoint,[{}]))
    else:
        raise ValueError(f"Data from {endpoint} is not a list")
    # Push data to BQ
    push_to_bq(local_file)

    # Clean up
    if __name__ != "__main__":
        remove(local_file)

if __name__ == "__main__":
    request_obj = Request.from_values(json={})
    function_static_data(request_obj)