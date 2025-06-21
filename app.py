from flask import Flask, request, jsonify, render_template
import json
from datetime import datetime
import os

app = Flask(__name__)

DATA_FILE = "users.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

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
            return jsonify({"status": "success", "message": f"HWID reset for {username}"})

    return jsonify({"status": "error", "message": "User not found"})

# 🔥 This part is updated for Render deployment:
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render will provide PORT
    app.run(host="0.0.0.0", port=port, debug=True)
