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
fetch_list = [("/games", "IGDB Fetch/games.json"),
              ("/genres", "IGDB Fetch/genres.json")]
# Other Possible Fetches:
# ("/games", "IGDB Fetch/games.txt")
# ("/genres", "IGDB Fetch/genres.txt")
auth_file = "authentication.txt"
log_file = "log_output.log"

def main():
    setup()
    set_authentication()
    loop_fetch_list()
    
# Purpose of this method is to populate CLIENT_ID, CLIENT_SECRET, and reset files.
# CLIENT_ID and CLIENT_SECRET are populated from the first two lines of the specified auth_file.
def setup():
    global CLIENT_ID
    global CLIENT_SECRET

    file_print("Began program to pull from IGDB according to the specified fetch_list.")
    for fetch in fetch_list:
        if os.path.exists(fetch[1]):
            os.remove(fetch[1])
        find_ext(fetch[1])
    file_print("Deleted target output files if they existed.")
        
    file_print("Searching local files for valid Twich Client data...")
    with open(auth_file, 'r') as file:
        lines = file.readlines()
        CLIENT_ID = lines[0].strip()
        CLIENT_SECRET = lines[1].strip()
    
# Purpose of this method is to populate ACCESS_TOKEN, retrieved from twitch and expires,
# and to populate AUTH_HEADER.
def set_authentication():
    global ACCESS_TOKEN
    global AUTH_HEADER

    file_print("Authenticating with Twitch...")
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
            file_print("An exception occurred:", str(e))
            if has_retried:
                raise
            file_print("Retrying authentication...")
            time.sleep(30)

        has_retried = True
    AUTH_HEADER = {
        "Client-ID": CLIENT_ID,
        "Authorization": ACCESS_TOKEN
    }
    file_print("Successful authentication!")

# Loops through each specified element of the fetch_list, pulling from the endpoint and outputting to a text file.
def loop_fetch_list():
    for fetch in fetch_list:
        loop_endpoint(api_url + fetch[0], fetch[1])

# Fetches all data from a specified IGDB endpoint by looping through 500 records at a time.
def loop_endpoint(url, output_file):
    file_print(f"Contents of {url} will be output to {output_file}")
    has_data = True
    offset = 0
    limit = 500
    while has_data:
        has_data = fetch_subset(url, output_file, offset, limit)
        offset += 500

# Prints output from POST request to a file for parsing later.
# Returns true if there was some new data detected, false otherwise.
def fetch_subset(url, output_file, offset, limit):
    file_print(f"Fetching contents of {url} from {offset + 1} to {offset + limit}")
    body = (f"fields *; limit {limit}; offset {offset};")
    response = post_request_with_retry(url, AUTH_HEADER, body, 2)
    if response.text != '[]':
        with open(output_file, 'a') as file:
            json.dump(response.json(), file)
        return True
    file_print(f"Finished pulling all contents from {url}.")
    return False

# Handles possible errors from authentication or too many requests per second.
def post_request_with_retry(url, headers = None, data = None, max_retries = 5, backoff_factor = 0.5):
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers = headers, data = data)
            response.raise_for_status()
            return response
        except (ConnectionError, HTTPError, RequestException) as e:
            wait = backoff_factor * (2 ** attempt)
            if e.response.status_code == 401:
                file_print(f"Auth failed ({e}), refreshing access key now...")
                set_authentication()
                file_print(f"Retrying original request in {wait:.1f}s... (attempt {attempt + 1} of {max_retries})")
            else:
                file_print(f"Warning: Request failed ({e}), retrying in {wait:.1f}s... (attempt {attempt + 1} of {max_retries})")
            time.sleep(wait)
    file_print(f"Error: Failed to get a successful response from {url} after {max_retries} attempts.")

def find_ext(file_path):
    file_path = "example_file.txt"
    root, ext = os.path.splitext(file_path)
    if ext == '.txt' or ext == '.json':
        return ext.replace(".", "")
    else:
        raise Exception(f"Chosen output file {file_path} not valid. Please choose a text or json file.")  

# Replaces standard print statements - routes to specified logger file with a timestamp.
def file_print(log_message):
    with open(log_file, 'a') as f:
        print(get_print_prefix() + log_message, file=f)

# Helper method to put before print strings, helpful when logging to file instead of printing directly.
def get_print_prefix():
    current_timestamp = datetime.now()
    prefix = current_timestamp.strftime("%Y-%m-%d %H:%M:%S") + ": "
    return prefix

main()