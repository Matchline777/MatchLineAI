import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_API_KEY")


def get_live_matches():

    today = datetime.now().strftime("%Y-%m-%d")

    url = f"https://v3.football.api-sports.io/fixtures?date={today}"

    headers = {
        "x-apisports-key": API_KEY
    }

    response = requests.get(url, headers=headers)

    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    if response.status_code != 200:
        return None

    return response.json()


def get_match(fixture_id):

    url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"

    headers = {
        "x-apisports-key": API_KEY
    }

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(response.text)
        return None

    return response.json()