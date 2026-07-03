import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("FOOTBALL_API_KEY")

HEADERS = {
    "x-apisports-key": API_KEY
}


def get_live_matches():

    today = datetime.now().strftime("%Y-%m-%d")

    url = "https://v3.football.api-sports.io/fixtures?live=all"

    response = requests.get(url, headers=HEADERS)

    print("LIVE STATUS:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        return None

    return response.json()


def get_match(fixture_id):

    url = f"https://v3.football.api-sports.io/fixtures?id={fixture_id}"

    response = requests.get(url, headers=HEADERS)

    print("MATCH STATUS:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        return None

    return response.json()


def get_statistics(fixture_id):

    url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"

    response = requests.get(url, headers=HEADERS)

    print("=" * 50)
    print("STAT STATUS:", response.status_code)
    print("STAT BODY:", response.text)
    print("=" * 50)

    if response.status_code != 200:
        return None

    return response.json()


def get_events(fixture_id):

    url = f"https://v3.football.api-sports.io/fixtures/events?fixture={fixture_id}"

    response = requests.get(url, headers=HEADERS)

    print("=" * 50)
    print("EVENT STATUS:", response.status_code)
    print("EVENT BODY:", response.text)
    print("=" * 50)

    if response.status_code != 200:
        return None

    return response.json()


def get_team_last_matches(team_id, last=5):

    url = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last={last}"

    response = requests.get(url, headers=HEADERS)

    print("=" * 50)
    print("TEAM LAST MATCHES STATUS:", response.status_code)
    print("TEAM LAST MATCHES BODY:", response.text)
    print("=" * 50)

    if response.status_code != 200:
        return None

    return response.json()


def get_head_to_head(team1_id, team2_id, last=5):

    url = f"https://v3.football.api-sports.io/fixtures/headtohead?h2h={team1_id}-{team2_id}&last={last}"

    response = requests.get(url, headers=HEADERS)

    print("=" * 50)
    print("HEAD TO HEAD STATUS:", response.status_code)
    print("HEAD TO HEAD BODY:", response.text)
    print("=" * 50)

    if response.status_code != 200:
        return None

    return response.json()


def get_odds(fixture_id):

    url = f"https://v3.football.api-sports.io/odds?fixture={fixture_id}"

    response = requests.get(url, headers=HEADERS)

    print("=" * 50)
    print("ODDS STATUS:", response.status_code)
    print("ODDS BODY:", response.text)
    print("=" * 50)

    if response.status_code != 200:
        return None

    return response.json()
