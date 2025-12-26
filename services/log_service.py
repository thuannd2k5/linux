import json
import os
from datetime import datetime

LOG_FILE = "data/activity_log.json"

def load_logs():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def write_log(action, server_ip, detail=""):
    logs = load_logs()
    logs.append({
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "server": server_ip,
        "action": action,
        "detail": detail
    })
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)
