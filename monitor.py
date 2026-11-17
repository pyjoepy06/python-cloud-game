
import os
import requests

SERVER = os.environ.get(
    "GAME_SERVER_URL",
    "http://127.0.0.1:5000"
)

try:
    health = requests.get(
        f"{SERVER}/health", timeout=5
    ).json()

    print("GAME SERVER STATUS")
    print("------------------")
    print("Status:", health["status"])
    print("Players:", health["players"])

    scores = requests.get(
        f"{SERVER}/leaderboard", timeout=5
    ).json()

    print("\nLEADERBOARD")
    for player in scores:
        print(player["player"], player["score"])

except requests.RequestException as error:
    print("SERVER UNAVAILABLE:", error)
