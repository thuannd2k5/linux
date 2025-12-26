import json
import os

BOOKMARK_FILE = "data/bookmarks.json"

def load_bookmarks():
    if not os.path.exists(BOOKMARK_FILE):
        return []
    try:
        with open(BOOKMARK_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_bookmarks(bookmarks):
    with open(BOOKMARK_FILE, "w") as f:
        json.dump(bookmarks, f, indent=4)

def add_bookmark(server_ip, path):
    bookmarks = load_bookmarks()
    bookmarks.append({
        "server": server_ip,
        "path": path
    })
    save_bookmarks(bookmarks)
