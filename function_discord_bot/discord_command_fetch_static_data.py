from flask.wrappers import Request
import requests
from threading import Thread
import google.auth.transport.requests
import google.oauth2.id_token

def fetch_static_data(request: Request):
    url = "https://us-central1-ninthage-data-analytics.cloudfunctions.net/function_static_data"

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, url)
    headers={
            "Authorization": f"Bearer {id_token}",
        }
    Thread(target=requests.get, args=(url, headers)).start()
    # response.read() This takes to long and makes discord assume nothing happened

    return "Static data loading has begun", 200