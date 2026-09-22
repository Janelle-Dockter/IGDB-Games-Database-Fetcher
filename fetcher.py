import requests
import time
import json
import os
from datetime import datetime
from requests.exceptions import RequestException, ConnectionError, HTTPError

CLIENT_ID = ""
CLIENT_SECRET = ""
ACCESS_TOKEN = ""
AUTH_HEADER = ""

api_url = "https://api.igdb.com/v4"
fetch_list = [("/games", "IGDB Fetch/games.txt"), 
              ("/genres", "IGDB Fetch/genres.txt")]
auth_file = "authentication.txt"

def main():
    setup()
    set_authentication()
    loop_fetch_list()
    
# Purpose of this method is to populate CLIENT_ID, CLIENT_SECRET, and reset files.
# CLIENT_ID and CLIENT_SECRET are populated from the first two lines of the specified auth_file.
def setup():
    global CLIENT_ID
    global CLIENT_SECRET

    print(get_print_prefix() + "Began program to pull from IGDB according to the specified fetch_list.")
    for fetch in fetch_list:
        if os.path.exists(fetch[1]):
            os.remove(fetch[1])
    print(get_print_prefix() + "Searching local files for valid Twich Client data...")
    with open(auth_file, 'r') as file:
        lines = file.readlines()
        CLIENT_ID = lines[0].strip()
        CLIENT_SECRET = lines[1].strip()
    
# Purpose of this method is to populate ACCESS_TOKEN, retrieved from twitch and expires.
def set_authentication():
    global ACCESS_TOKEN
    global AUTH_HEADER

    print(get_print_prefix() + "Authenticating with Twitch...")
    has_retried = False
    while not has_retried:
        try:
            auth = requests.post("https://id.twitch.tv/oauth2/token", data = {
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "client_credentials"
                })
            if auth is None:
                raise Exception("Failed to authenticate with Twitch API")

            ACCESS_TOKEN = "Bearer " + auth.json()["access_token"]

        except Exception as e:
            print(get_print_prefix() + "An exception occurred:", str(e))
            if has_retried:
                raise
            print(get_print_prefix() + "Retrying authentication...")
            time.sleep(30)

        has_retried = True
    AUTH_HEADER = {
        "Client-ID": CLIENT_ID,
        "Authorization": ACCESS_TOKEN
    }
    print(get_print_prefix() + "Successful authentication!")

def loop_fetch_list():
    for fetch in fetch_list:
        loop_endpoint(api_url + fetch[0], fetch[1])

def loop_endpoint(url, output_file):
    print(get_print_prefix() + f"Contents of {url} will be output to {output_file}")
    has_data = True
    offset = 0
    limit = 500
    while has_data:
        has_data = fetch_subset(url, output_file, offset, limit)
        offset += 500

# Returns true if there was some new data detected, false otherwise
def fetch_subset(url, output_file, offset, limit):
    print(get_print_prefix() + f"Fetching contents of {url} from {offset + 1} to {limit}")
    body = (f"fields *; limit {limit}; offset {offset};")
    response = post_request_with_retry(url, AUTH_HEADER, body, 2)
    if response:
        with open(output_file, 'w') as file:
            json.dump(response.json(), file)
        return True
    return False

def post_request_with_retry(url, headers = None, data = None, max_retries = 5, backoff_factor = 0.5):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers = headers, data = data)
            response.raise_for_status()
            return response
        except (ConnectionError, HTTPError, RequestException) as e:
            if e.response.status_code == 401:
                print(get_print_prefix() + f"Auth failed ({e}), refreshing access key now...")
                set_authentication()
                print(get_print_prefix() + f"Retrying original request in {wait:.1f}s... (attempt {attempt + 1} of {max_retries})")
            else:
                print(get_print_prefix() + f"Warning: Request failed ({e}), retrying in {wait:.1f}s... (attempt {attempt + 1} of {max_retries})")
            wait = backoff_factor * (2 ** attempt)
            time.sleep(wait)
    print(get_print_prefix() + f"Error: Failed to get a successful response from {url} after {max_retries} attempts.")

# Helper method to put before print strings. 
# When leaving this to run, a command prompt will route output to a log file, 
# so it is helpful to have a date/time stamp on logged lines. Also helps with runtime analysis.
def get_print_prefix():
    current_timestamp = datetime.now()
    prefix = current_timestamp.strftime("%Y-%m-%d %H:%M:%S") + ": "
    return prefix

main()