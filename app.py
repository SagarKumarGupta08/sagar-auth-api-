from flask import Flask, request, jsonify, render_template
import json, os, requests, base64
from datetime import datetime

app = Flask(__name__)

def load_data():
    # Download latest users.json from GitHub
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    REPO_OWNER = os.environ.get("REPO_OWNER")
    REPO_NAME = os.environ.get("REPO_NAME")
    FILE_PATH = os.environ.get("FILE_PATH")

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.json()["content"]
        return json.loads(base64.b64decode(content).decode())
    return {}

def save_data(data):
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    REPO_OWNER = os.environ.get("REPO_OWNER")
    REPO_NAME = os.environ.get("REPO_NAME")
    FILE_PATH = os.environ.get("FILE_PATH")

    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    # Get current SHA
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        print("❌ Failed to get file SHA")
        return
    sha = res.json()["sha"]

    # Encode and upload new content
    new_content = json.dumps(data, indent=2)
    encoded = base64.b64encode(new_content.encode()).decode()

    payload = {
        "message": "Update users.json",
        "content": encoded,
        "sha": sha,
        "branch": "main"
    }

    put = requests.put(url, headers=headers, json=payload)
    if put.status_code not in [200, 201]:
        print("❌ Failed to update GitHub file:", put.text)
    else:
        print("✅ users.json updated on GitHub")

@app.route("/", methods=["GET"])
def home():
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

@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data()
    category = request.form["category"]
    return jsonify(data.get(category, []))

@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    if category not in data:
        return jsonify({"status": "error", "message": "Invalid application"})
    users = data[category]
    updated = [u for u in users if u["Username"] != username]
    if len(users) == len(updated):
        return jsonify({"status": "error", "message": "User not found"})
    data[category] = updated
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
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
