from flask.wrappers import Request
import urllib
import google.auth.transport.requests
import google.oauth2.id_token

def fetch_static_data(request: Request):
    url = "https://us-central1-ninthage-data-analytics.cloudfunctions.net/function_static_data"

    req = urllib.request.Request(url)

    auth_req = google.auth.transport.requests.Request()
    id_token = google.oauth2.id_token.fetch_id_token(auth_req, url)

    req.add_header("Authorization", f"Bearer {id_token}")
    response = urllib.request.urlopen(req)

    # return response.read()

    print("worked fine")



    # if r.status_code == 200:
    #     return "Static data loading has begun"
    # else:
    #     return "Static data loading has failed"
