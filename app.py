from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import requests
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# --- Configuration ---
ADMIN_USERNAME = "RTX"
ADMIN_PASSWORD = "3050"

JSONBIN_API_KEY = "$2a$10$vm/bHfwrLhw7wBCU4c/WeuiaKZy8mbLZt06WK3x6HpnEI9IPqyQFO"
BIN_ID = "6856f8e58a456b7966b2ca8d"

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_API_KEY
}

# --- JSONBin Helpers ---
def load_data():
    try:
        r = requests.get(f"https://api.jsonbin.io/v3/b/{BIN_ID}/latest", headers=HEADERS)
        return r.json()['record'] if r.status_code == 200 else {}
    except Exception as e:
        print("Error loading:", e)
        return {}

def save_data(data):
    try:
        r = requests.put(f"https://api.jsonbin.io/v3/b/{BIN_ID}", headers=HEADERS, json=data)
        return r.status_code == 200
    except Exception as e:
        print("Error saving:", e)
        return False

# --- Routes ---
@app.route("/")
def home():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/")
        return render_template("login.html", error="Invalid Credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect("/")

# --- Application Management ---
@app.route("/create_app", methods=["POST"])
def create_app():
    app_name = request.form["name"]
    data = load_data()
    if app_name in data:
        return jsonify({"status": "error", "message": "App already exists"})
    data[app_name] = []
    if save_data(data):
        return jsonify({"status": "success", "message": "App created"})
    return jsonify({"status": "error", "message": "Failed to save app"})

@app.route("/get_apps")
def get_apps():
    data = load_data()
    apps = [key for key in data.keys() if key != "messages"]
    return jsonify(apps)

# --- User Operations ---
@app.route("/add_user", methods=["POST"])
def add_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    password = request.form["password"]
    expiry = request.form["expiry"]
    if category not in data:
        return jsonify({"status": "error", "message": "Invalid app"})
    for u in data[category]:
        if u["Username"] == username:
            return jsonify({"status": "error", "message": "User exists"})
    data[category].append({
        "Username": username,
        "Password": password,
        "HWID": None,
        "Status": "Active",
        "Expiry": expiry,
        "CreatedAt": datetime.today().strftime("%Y-%m-%d")
    })
    if save_data(data):
        return jsonify({"status": "success", "message": "User created"})
    return jsonify({"status": "error", "message": "Failed to save"})

@app.route("/delete_user", methods=["POST"])
def delete_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    if category not in data:
        return jsonify({"status": "error", "message": "Invalid app"})
    data[category] = [u for u in data[category] if u["Username"] != username]
    if save_data(data):
        return jsonify({"status": "success", "message": "User deleted"})
    return jsonify({"status": "error", "message": "Failed to update"})

@app.route("/pause_user", methods=["POST"])
def pause_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    action = request.form["action"]  # "pause" or "unpause"
    for user in data.get(category, []):
        if user["Username"] == username:
            user["Status"] = "Paused" if action == "pause" else "Active"
            if save_data(data):
                return jsonify({"status": "success", "message": f"User {action}d"})
            return jsonify({"status": "error", "message": "Failed to save"})
    return jsonify({"status": "error", "message": "User not found"})

@app.route("/reset_hwid", methods=["POST"])
def reset_hwid():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    for user in data.get(category, []):
        if user["Username"] == username:
            user["HWID"] = None
            if save_data(data):
                return jsonify({"status": "success", "message": "HWID reset"})
            return jsonify({"status": "error", "message": "Save failed"})
    return jsonify({"status": "error", "message": "User not found"})

@app.route("/info_user", methods=["POST"])
def info_user():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    for user in data.get(category, []):
        if user["Username"] == username:
            return jsonify({"status": "success", "data": user})
    return jsonify({"status": "error", "message": "User not found"})

@app.route("/get_users", methods=["POST"])
def get_users():
    data = load_data()
    category = request.form["category"]
    return jsonify(data.get(category, []))

# --- Message System ---
@app.route("/send_message", methods=["POST"])
def send_message():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    msg = request.form["message"]
    if "messages" not in data:
        data["messages"] = {}
    data["messages"][f"{category}:{username}"] = msg
    if save_data(data):
        return jsonify({"status": "success", "message": "Message sent"})
    return jsonify({"status": "error", "message": "Failed to save message"})

@app.route("/get_message", methods=["POST"])
def get_message():
    data = load_data()
    category = request.form["category"]
    username = request.form["username"]
    key = f"{category}:{username}"
    message = data.get("messages", {}).get(key, "")
    return jsonify({"message": message})

if __name__ == "__main__":
    app.run(debug=True)
