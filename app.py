from flask import Flask, request, jsonify, render_template
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = os.getenv("REPO_OWNER")
REPO_NAME = os.getenv("REPO_NAME")
FILE_PATH = os.getenv("FILE_PATH")

def github_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

def get_file_sha():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    r = requests.get(url, headers=github_headers())
    if r.status_code == 200:
        return r.json().get("sha")
    return None

def load_data():
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/main/{FILE_PATH}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()
    return {}

def save_data(data):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    content = json.dumps(data, indent=2)
    encoded_content = content.encode("utf-8").decode("utf-8")
    b64_content = encoded_content.encode("utf-8").decode("utf-8")
    message = "Update users.json"
    sha = get_file_sha()

    payload = {
        "message": message,
        "content": content.encode("utf-8").decode("utf-8").encode("base64").decode(),
        "branch": "main",
        "sha": sha
    }

    headers = github_headers()
    requests.put(url, headers=headers, json=payload)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/add_user", methods=["POST"])
def add_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    expiry = request.form["expiry"]

    if category not in data:
        data[category] = []

    if any(u["Username"] == username for u in data[category]):
        return jsonify({"status": "error", "message": "Username already exists"})

    data[category].append({
        "Username": username,
        "Password": password,
        "HWID": None,
        "Expiry": expiry,
        "CreatedAt": datetime.today().strftime("%Y-%m-%d")
    })

    save_data(data)
    return jsonify({"status": "success", "message": "User added"})

@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    users = data[category]
    updated_users = [u for u in users if u["Username"] != username]

    if len(users) == len(updated_users):
        return jsonify({"status": "error", "message": "User not found"})

    data[category] = updated_users
    save_data(data)
    return jsonify({"status": "success", "message": "User deleted"})

@app.route("/pause_user", methods=["POST"])
def pause_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    action = request.form["action"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for u in data[category]:
        if u["Username"] == username:
            u["HWID"] = None if action == "pause" else ""
            save_data(data)
            return jsonify({"status": "success", "message": f"User {action}d"})

    return jsonify({"status": "error", "message": "User not found"})

@app.route("/info_user", methods=["POST"])
def info_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for u in data[category]:
        if u["Username"] == username:
            return jsonify({"status": "success", "data": u})

    return jsonify({"status": "error", "message": "User not found"})

@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data()
    category = request.form["category"]
    return jsonify(data.get(category, []))

@app.route("/reset_hwid", methods=["POST"])
def reset_hwid():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]

    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})

    for u in data[category]:
        if u["Username"] == username:
            u["HWID"] = ""
            save_data(data)
            return jsonify({"status": "success", "message": "HWID reset"})

    return jsonify({"status": "error", "message": "User not found"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
