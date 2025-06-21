from flask import Flask, request, jsonify, render_template
import requests
from datetime import datetime

app = Flask(__name__)

# 🔐 JSONBin config
JSONBIN_API_KEY = "$2a$10$vm/bHfwrLhw7wBCU4c/WeuiaKZy8mbLZt06WK3x6HpnEI9IPqyQFO"
BIN_ID = "68567a118960c979a5ae5135"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

def load_data():
    try:
        res = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers=HEADERS)
        if res.status_code == 200:
            return res.json().get("record", {})
        return {}
    except Exception as e:
        print("Error loading data:", e)
        return {}

def save_data(data):
    try:
        res = requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", headers=HEADERS, json=data)
        print("Save:", res.status_code, res.text)
        return res.status_code == 200
    except Exception as e:
        print("Error saving data:", e)
        return False

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

    if save_data(data):
        return jsonify({"status": "success", "message": "User added"})
    return jsonify({"status": "error", "message": "Failed to save user"})

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
    if save_data(data):
        return jsonify({"status": "success", "message": "User deleted"})
    return jsonify({"status": "error", "message": "Failed to update data"})

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
            if save_data(data):
                return jsonify({"status": "success", "message": f"User {action}d"})
            return jsonify({"status": "error", "message": "Failed to update user"})

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
            if save_data(data):
                return jsonify({"status": "success", "message": f"HWID reset for {username}"})
            return jsonify({"status": "error", "message": "Failed to update data"})

    return jsonify({"status": "error", "message": "User not found"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
