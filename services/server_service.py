import json
import os

DATA_FILE = "data/servers.json"

def load_servers():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_servers(servers):
    with open(DATA_FILE, "w") as f:
        json.dump(servers, f, indent=4)
