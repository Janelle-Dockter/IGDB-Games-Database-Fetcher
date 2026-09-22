import requests
import csv
import time
import json
import os
from datetime import datetime
from requests.exceptions import RequestException, ConnectionError, HTTPError

CLIENT_ID = ""
CLIENT_SECRET = ""
ACCESS_TOKEN = "Bearer "

api_url = "https://api.igdb.com/v4"
fetch_list = [("/games", "data_games.csv"), 
              ("/genres", "data_genres.csv")]

def main():
    setAuthentication()

def setAuthentication():
    try:
        auth = requests.post("https://id.twitch.tv/oauth2/token", data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials"
            })
        if auth is None:
            raise Exception("Failed to authenticate with Twitch API")

        ACCESS_TOKEN += auth.json()['access_token']
        
    except Exception as e:
        print("An exception occurred:", str(e))




main()