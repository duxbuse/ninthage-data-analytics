from flask.wrappers import Request
import requests

def fetch_static_data(request: Request):
    url = "https://us-central1-ninthage-data-analytics.cloudfunctions.net/function_static_data"
    r = requests.get(url, allow_redirects=True)
    print(r.status_code, r.text)
    if r.status_code == 200:
        return "Static data loading has begun"
    else:
        return "Static data loading has failed"
