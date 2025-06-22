from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import requests
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Replace with your actual JSONBin credentials
JSONBIN_API_KEY = "$2a$10$qpbJqpXhVrqPgWBQgq4Rmu7BWx/WcNLkrObn5UUfpYk1/eibVKDFq"
BIN_ID = "6856f8e58a456b7966b2ca8d"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

def load_data():
    try:
        r = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers=HEADERS)
        return r.json().get("record", {})
    except Exception as e:
        print("Load Error:", e)
        return {}

def save_data(data):
    try:
        r = requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", headers=HEADERS, json=data)
        return r.status_code == 200
    except Exception as e:
        print("Save Error:", e)
        return False

@app.route('/')
def index():
    return render_template("index.html")

@app.route("/create_app", methods=["POST"])
def create_app():
    data = load_data()
    app_name = request.json.get("app")
    if app_name in data:
        return jsonify({"status": "exists"})
    data[app_name] = []
    if save_data(data):
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"})

@app.route("/get_apps", methods=["GET"])
def get_apps():
    data = load_data()
    return jsonify(list(data.keys()))

@app.route("/create_user", methods=["POST"])
def create_user():
    app_name = request.json.get("app")
    username = request.json.get("username")
    password = request.json.get("password")
    expiry = request.json.get("expiry")
    data = load_data()

    if app_name not in data:
        return jsonify({"status": "invalid_app"})

    for user in data[app_name]:
        if user["Username"] == username:
            return jsonify({"status": "exists"})

    data[app_name].append({
        "Username": username,
        "Password": password,
        "HWID": "N/A",
        "Status": "Active",
        "Expiry": expiry,
        "CreatedAt": datetime.now().strftime("%Y-%m-%d")
    })

    if save_data(data):
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"})

@app.route("/get_users", methods=["POST"])
def get_users():
    app_name = request.json.get("app")
    data = load_data()
    return jsonify(data.get(app_name, []))

@app.route("/delete_user", methods=["POST"])
def delete_user():
    app_name = request.json.get("app")
    username = request.json.get("username")
    data = load_data()
    if app_name not in data:
        return jsonify({"status": "invalid_app"})
    data[app_name] = [u for u in data[app_name] if u["Username"] != username]
    if save_data(data):
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"})

@app.route("/pause_user", methods=["POST"])
def pause_user():
    app_name = request.json.get("app")
    username = request.json.get("username")
    action = request.json.get("action")  # pause or unpause
    data = load_data()
    for user in data.get(app_name, []):
        if user["Username"] == username:
            user["Status"] = "Suspended" if action == "pause" else "Active"
            if save_data(data):
                return jsonify({"status": "success"})
            return jsonify({"status": "fail"})
    return jsonify({"status": "not_found"})

@app.route("/reset_hwid", methods=["POST"])
def reset_hwid():
    app_name = request.json.get("app")
    username = request.json.get("username")
    data = load_data()
    for user in data.get(app_name, []):
        if user["Username"] == username:
            user["HWID"] = "N/A"
            if save_data(data):
                return jsonify({"status": "success"})
            return jsonify({"status": "fail"})
    return jsonify({"status": "not_found"})

@app.route("/user_info", methods=["POST"])
def user_info():
    app_name = request.json.get("app")
    username = request.json.get("username")
    data = load_data()
    for user in data.get(app_name, []):
        if user["Username"] == username:
            return jsonify(user)
    return jsonify({"error": "not_found"})

@app.route("/send_message", methods=["POST"])
def send_message():
    app_name = request.json.get("app")
    username = request.json.get("username")
    message = request.json.get("message")
    data = load_data()
    if "messages" not in data:
        data["messages"] = {}
    data["messages"][f"{app_name}:{username}"] = message
    if save_data(data):
        return jsonify({"status": "success"})
    return jsonify({"status": "fail"})

@app.route("/get_message", methods=["POST"])
def get_message():
    app_name = request.json.get("app")
    username = request.json.get("username")
    data = load_data()
    return jsonify({"message": data.get("messages", {}).get(f"{app_name}:{username}", "")})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
