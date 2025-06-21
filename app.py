from flask import Flask, request, jsonify, render_template
from datetime import datetime
import requests
import os

app = Flask(__name__)

# ✅ JSONBin Configuration
BIN_ID = "685666b58561e97a5028a85f"
API_KEY = "$2a$10$AXTwTatLcVqZ7q1D1V0gDuuT76fvxssdzPUcIkBdsDK8yHqOBZqc6"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": API_KEY
}

def load_data():
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest"
    res = requests.get(url, headers=HEADERS)
    if res.status_code == 200:
        return res.json().get("record", {})
    return {"SAGAR": [], "ADMIN": [], "TESTER": []}  # fallback on error

def save_data(data):
    url = f"https://api.jsonbin.io/v3/b/{BIN_ID}"
    payload = { "record": data }
    res = requests.put(url, json=payload, headers=HEADERS)
    return res.status_code == 200

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
