from flask.wrappers import Request
from requests import get
import time
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
    # get thread started
    Thread(target=get, args=(url,), kwargs={'headers': headers}).start()
    # response.read() This takes to long and makes discord assume nothing happened
    time.sleep(.5)
    # finished sleeping request should be sent
    return "Static data loading has begun"