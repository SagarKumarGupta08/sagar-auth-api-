import requests
import json
from config import JSONBIN_API_KEY, JSONBIN_BIN_ID

BASE_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
HEADERS = {
    "X-Master-Key": JSONBIN_API_KEY,
    "Content-Type": "application/json"
}

def get_users():
    res = requests.get(BASE_URL + "/latest", headers=HEADERS)
    return res.json()['record']

def update_users(data):
    res = requests.put(BASE_URL, headers=HEADERS, json=data)
    return res.status_code == 200

def create_user(username, password, expiry):
    users = get_users()
    if username in users:
        return False
    users[username] = {
        "password": password,
        "expiry": expiry,
        "paused": False,
        "hwid": "",
        "message": ""
    }
    return update_users(users)

def delete_user(username):
    users = get_users()
    if username in users:
        del users[username]
        return update_users(users)
    return False

def pause_user(username, state=True):
    users = get_users()
    if username in users:
        users[username]["paused"] = state
        return update_users(users)
    return False

def reset_hwid(username):
    users = get_users()
    if username in users:
        users[username]["hwid"] = ""
        return update_users(users)
    return False

def send_message(username, msg):
    users = get_users()
    if username in users:
        users[username]["message"] = msg
        return update_users(users)
    return False

def get_user_info(username):
    users = get_users()
    return users.get(username, None)

def get_all_users():
    return get_users()

def export_users():
    return json.dumps(get_users(), indent=2)
